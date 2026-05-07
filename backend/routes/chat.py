from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_current_user_payload
from database import SessionLocal
from models import Order, QualityLog
from schemas import ChatMessage
from nlp import parse_message

router = APIRouter()
ALLOWED_FLOW = ["Received", "In Review", "Accepted"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_order(db: Session, order_id, user_email: str):
    if order_id:
        # 1) Try actual DB id scoped to current user.
        direct_match = db.query(Order).filter(
            Order.id == order_id,
            Order.created_by_email == user_email,
        ).first()
        if direct_match:
            return direct_match

        # 2) Fallback: interpret provided id as user-visible sequence (1..N).
        user_orders = db.query(Order).filter(
            Order.created_by_email == user_email,
        ).order_by(Order.id.asc()).all()
        if 1 <= order_id <= len(user_orders):
            return user_orders[order_id - 1]
        return None
    # Fallback: apply to latest order when user omits order id.
    return db.query(Order).filter(
        Order.created_by_email == user_email,
    ).order_by(Order.id.desc()).first()


@router.post("/chat")
def chat(
    req: ChatMessage,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user_payload),
):

    try:
        user_email = _user.get("sub")
        user_message = req.message

        result = parse_message(user_message)

        print("PARSED:", result)

        intent = result.get("intent")

        # ---------------- CREATE ORDER ----------------
        if intent == "create_order":

            order = Order(
                part_name=result.get("part_name", "Unknown"),
                material=result.get("material", "Unknown"),
                quantity=result.get("quantity", 0),
                deadline=result.get("deadline", ""),
                status="Received",
                created_by_email=user_email,
            )

            db.add(order)
            db.commit()
            db.refresh(order)

            return {
                "reply": "Order created successfully",
                "order_id": order.id
            }

        # ---------------- UPDATE STATUS ----------------
        if intent == "update_status":
            order = resolve_order(db, result.get("order_id"), user_email)

            if order:
                target_status = result.get("status")
                if target_status not in ALLOWED_FLOW:
                    return {"reply": f"Status must be one of: {', '.join(ALLOWED_FLOW)}"}
                current_index = ALLOWED_FLOW.index(order.status) if order.status in ALLOWED_FLOW else -1
                target_index = ALLOWED_FLOW.index(target_status)
                # Allow moving forward to later stages in one chat command
                # (e.g. "reviewed and accepted"), but prevent going backward/same.
                if target_index <= current_index:
                    next_status = ALLOWED_FLOW[current_index + 1] if current_index + 1 < len(ALLOWED_FLOW) else "none"
                    return {"reply": f"Invalid transition. Allowed next status: {next_status}"}
                order.status = target_status
                db.commit()

                return {"reply": "Status updated successfully"}

            return {"reply": "Order not found"}

        # ---------------- UPDATE ORDER FIELDS ----------------
        if intent == "update_order":
            order = resolve_order(db, result.get("order_id"), user_email)
            if not order:
                return {"reply": "Order not found"}

            changed_fields = []
            for field in ["part_name", "material", "quantity", "deadline"]:
                value = result.get(field)
                if value is not None:
                    setattr(order, field, value)
                    changed_fields.append(field)

            if not changed_fields:
                return {"reply": "No valid fields found to update. Mention part, material, quantity, or deadline."}

            db.commit()
            return {"reply": f"Order updated successfully ({', '.join(changed_fields)})."}

        # ---------------- QUALITY NOTE ----------------
        if intent == "add_quality_note":
            order = resolve_order(db, result.get("order_id"), user_email)
            if not order:
                return {"reply": "Order not found"}
            if order.status != "Accepted":
                return {"reply": "Quality notes can be logged only after the order is Accepted."}
            note_text = (result.get("note") or "").strip()
            if not note_text:
                note_text = "Quality note updated"

            note = QualityLog(
                order_id=order.id,
                note=note_text
            )

            db.add(note)
            db.commit()
            db.refresh(note)

            return {
                "reply": f"Quality checkpoint logged for order {order.id} at {note.timestamp.isoformat()}",
            }

        # ---------------- DELETE ORDER ----------------
        if intent == "delete_order":
            order = resolve_order(db, result.get("order_id"), user_email)
            if not order:
                return {"reply": "Order not found"}

            db.query(QualityLog).filter(QualityLog.order_id == order.id).delete()
            db.delete(order)
            db.commit()
            return {"reply": "Order deleted successfully"}

        # ---------------- GET ORDER STATUS ----------------
        if intent == "get_order_status":
            order = resolve_order(db, result.get("order_id"), user_email)
            if not order:
                return {"reply": "Order not found"}
            latest_quality_note = "No quality note yet"
            if order.quality_logs:
                latest_quality_note = max(order.quality_logs, key=lambda item: item.timestamp).note
            return {
                "reply": (
                    f"Order {order.id} is currently '{order.status}'. "
                    f"Latest quality note: {latest_quality_note}."
                ),
                "order_id": order.id,
                "show_only_order_id": order.id,
            }

        # ---------------- GET ORDER DETAILS ----------------
        if intent == "get_order_details":
            order = resolve_order(db, result.get("order_id"), user_email)
            if not order:
                return {"reply": "Order not found"}
            latest_quality_note = "No quality note yet"
            if order.quality_logs:
                latest_quality_note = max(order.quality_logs, key=lambda item: item.timestamp).note
            return {
                "reply": (
                    f"Order {order.id}: part='{order.part_name}', material='{order.material}', "
                    f"quantity={order.quantity}, deadline='{order.deadline}', status='{order.status}', "
                    f"latest quality note='{latest_quality_note}'."
                ),
                "order_id": order.id,
                "show_only_order_id": order.id,
            }

        return {
            "reply": (
                "Could not understand request. Try: "
                "'create 50 steel valves before June 20', "
                "'update status to in review', "
                "'what is status of order 2', "
                "'show details of order 2', "
                "'quality is excellent', "
                "'change quantity to 80', "
                "'delete order 2'."
            )
        }

    except Exception as e:

        print("CHAT ERROR:", e)

        return {
            "reply": "Backend error occurred",
            "error": str(e)
        }
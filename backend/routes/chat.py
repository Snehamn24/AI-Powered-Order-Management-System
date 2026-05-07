from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import SessionLocal
from nlp import parse_message
from models import Order, QualityLog

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= STATUS FLOW =================
STATUS_FLOW = {
    "Received": ["In Review"],
    "In Review": ["Accepted"],
    "Accepted": ["Completed"],
    "Completed": []
}


# ================= HELPER =================
def get_latest_note(db, order_id):
    note = db.query(QualityLog)\
        .filter(QualityLog.order_id == order_id)\
        .order_by(QualityLog.id.desc())\
        .first()
    return note.note if note else None


# ================= MAIN CHAT =================
@router.post("/chat")
def chat(payload: dict, db: Session = Depends(get_db)):

    user_message = payload.get("message", "")
    result = parse_message(user_message)

    intent = result.get("intent")

    # ================= CREATE ORDER =================
    if intent == "create_order":

        order = Order(
            part_name=result.get("part_name"),
            material=result.get("material"),
            quantity=result.get("quantity"),
            deadline=result.get("deadline"),
            status="Received"
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return {"reply": f"Order #{order.id} created (Received)"}

    # ================= UPDATE STATUS =================
    elif intent == "update_status":

        order_id = result.get("order_id")
        new_status = result.get("status")

        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            return {"reply": f"Order #{order_id} not found"}

        allowed = STATUS_FLOW.get(order.status, [])

        if new_status not in allowed:
            return {
                "reply": f"Cannot move {order.status} → {new_status}"
            }

        order.status = new_status
        db.commit()

        return {"reply": f"Order #{order.id} → {order.status}"}

    # ================= QUALITY NOTE (FIXED WORKING) =================
    elif intent == "add_quality_note":

        order_id = result.get("order_id")

        if not order_id:
            return {"reply": "Invalid order ID"}

        note_entry = QualityLog(
            order_id=order_id,
            note=result.get("note"),
            timestamp=datetime.now()
        )

        db.add(note_entry)
        db.commit()

        return {"reply": f"Quality note saved for Order #{order_id}"}

    # ================= GET ORDER STATUS =================
    elif intent == "get_order_status":

        order_id = result.get("order_id")

        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            return {"reply": f"Order #{order_id} not found"}

        return {
            "reply": f"Order #{order.id}: {order.status} | {order.material} | Qty {order.quantity} | Latest: {get_latest_note(db, order_id)}"
        }

    # ================= DELETE ORDER =================
    elif intent == "delete_order":

        order_id = result.get("order_id")

        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            return {"reply": f"Order #{order_id} not found"}

        db.query(QualityLog).filter(QualityLog.order_id == order_id).delete()
        db.delete(order)
        db.commit()

        return {"reply": f"Order #{order_id} deleted successfully"}

    # ================= FILTER ORDERS =================
    elif intent == "filter_orders":

        status = result.get("status")

        orders = db.query(Order).filter(Order.status == status).all()

        return {
            "reply": [
                {
                    "id": o.id,
                    "status": o.status,
                    "material": o.material,
                    "qty": o.quantity,
                    "latest_note": get_latest_note(db, o.id)
                }
                for o in orders
            ]
        }

    # ================= ALL ORDERS (DASHBOARD) =================
    elif intent == "get_all_orders":

        orders = db.query(Order).all()

        return {
            "reply": [
                {
                    "id": o.id,
                    "status": o.status,
                    "material": o.material,
                    "qty": o.quantity,
                    "latest_note": get_latest_note(db, o.id)
                }
                for o in orders
            ]
        }

    return {"reply": "Sorry, I couldn't understand the request"}
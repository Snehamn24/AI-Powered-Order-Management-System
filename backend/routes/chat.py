from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Order, QualityLog
from schemas import ChatMessage
from nlp import parse_message

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat")
def chat(req: ChatMessage, db: Session = Depends(get_db)):

    try:
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
                status="Received"
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

            order = db.query(Order).filter(Order.id == result.get("order_id")).first()

            if order:
                order.status = result.get("status")
                db.commit()

                return {"reply": "Status updated successfully"}

            return {"reply": "Order not found"}

        # ---------------- QUALITY NOTE ----------------
        if intent == "add_quality_note":

            note = QualityLog(
                order_id=result.get("order_id"),
                note=result.get("note")
            )

            db.add(note)
            db.commit()

            return {"reply": "Quality note added"}

        return {"reply": "Could not understand request"}

    except Exception as e:

        print("CHAT ERROR:", e)

        return {
            "reply": "Backend error occurred",
            "error": str(e)
        }
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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


@router.post("/chat")
def chat(message: dict, db: Session = Depends(get_db)):

    user_message = message["message"]

    result = parse_message(user_message)

    intent = result.get("intent")

    # =====================
    # CREATE ORDER
    # =====================
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

        return {
            "reply": "Order created successfully",
            "order_id": order.id
        }

    # =====================
    # UPDATE STATUS
    # =====================
    elif intent == "update_status":

        order = db.query(Order).filter(Order.id == result.get("order_id")).first()

        if order:
            order.status = result.get("status")
            db.commit()

            return {"reply": "Status updated successfully"}

        return {"reply": "Order not found"}

    # =====================
    # QUALITY NOTE
    # =====================
    elif intent == "add_quality_note":

        note = QualityLog(
            order_id=result.get("order_id"),
            note=result.get("note")
        )

        db.add(note)
        db.commit()

        return {"reply": "Quality note added"}

    # =====================
    # UNKNOWN
    # =====================
    return {
        "reply": "Sorry, I couldn't understand the request"
    }
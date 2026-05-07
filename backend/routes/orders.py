from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Order, QualityLog
from schemas import (
    OrderCreate,
    StatusUpdate,
    QualityNoteCreate
)

router = APIRouter()


# =========================
# DATABASE SESSION
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# CREATE ORDER
# =========================

@router.post("/create-order")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):

    new_order = Order(
        part_name=order.part_name,
        material=order.material,
        quantity=order.quantity,
        deadline=order.deadline,
        status="Received"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Order created successfully",
        "order_id": new_order.id
    }


# =========================
# GET ALL ORDERS
# =========================

@router.get("/orders")
def get_orders(db: Session = Depends(get_db)):

    orders = db.query(Order).all()

    result = []

    for order in orders:

        latest_note = None

        if order.quality_logs:
            latest_note = order.quality_logs[-1].note

        result.append({
            "id": order.id,
            "part_name": order.part_name,
            "material": order.material,
            "quantity": order.quantity,
            "deadline": order.deadline,
            "status": order.status,
            "latest_quality_note": latest_note
        })

    return result


# =========================
# UPDATE STATUS
# =========================

@router.put("/update-status")
def update_status(
    status_update: StatusUpdate,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == status_update.order_id
    ).first()

    if not order:
        return {"error": "Order not found"}

    order.status = status_update.status

    db.commit()

    return {"message": "Status updated successfully"}


# =========================
# ADD QUALITY NOTE
# =========================

@router.post("/add-quality-note")
def add_quality_note(
    quality_note: QualityNoteCreate,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == quality_note.order_id
    ).first()

    if not order:
        return {"error": "Order not found"}

    new_note = QualityLog(
        order_id=quality_note.order_id,
        note=quality_note.note
    )

    db.add(new_note)
    db.commit()

    return {"message": "Quality note added"}
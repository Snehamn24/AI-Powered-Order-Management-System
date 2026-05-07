from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Order, QualityLog

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/orders")
def get_orders(db: Session = Depends(get_db)):

    orders = db.query(Order).all()

    result = []

    for order in orders:

        latest_note = (
            db.query(QualityLog)
            .filter(QualityLog.order_id == order.id)
            .order_by(QualityLog.id.desc())
            .first()
        )

        result.append({
            "id": order.id,
            "part_name": order.part_name,
            "material": order.material,
            "quantity": order.quantity,
            "status": order.status,
            "latest_quality_note": latest_note.note if latest_note else None
        })

    return result
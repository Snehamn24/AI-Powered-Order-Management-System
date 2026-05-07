from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String)
    material = Column(String)
    quantity = Column(Integer)
    deadline = Column(String)
    status = Column(String, default="Received")
    created_by_email = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    quality_logs = relationship("QualityLog", back_populates="order")


class QualityLog(Base):
    __tablename__ = "quality_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    note = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="quality_logs")
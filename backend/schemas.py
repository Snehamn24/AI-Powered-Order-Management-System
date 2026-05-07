from pydantic import BaseModel
from typing import Optional


# =========================
# USER SCHEMAS
# =========================

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str


class UserLogin(BaseModel):
    email: str
    password: str


# =========================
# ORDER SCHEMAS
# =========================

class OrderCreate(BaseModel):
    part_name: str
    material: str
    quantity: int
    deadline: str


class StatusUpdate(BaseModel):
    order_id: int
    status: str


class QualityNoteCreate(BaseModel):
    order_id: int
    note: str


# =========================
# AI CHAT SCHEMA
# =========================

class ChatMessage(BaseModel):
    message: str
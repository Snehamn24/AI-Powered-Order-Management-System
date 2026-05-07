from pydantic import BaseModel, Field
from typing import Optional


# =========================
# USER SCHEMAS
# =========================

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=72)
    role: str = Field(min_length=3, max_length=30)


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=72)


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
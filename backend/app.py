from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import engine
from models import Base
from routes.orders import router as order_router
from routes.chat import router as chat_router
from routes.users import router as user_router

app = FastAPI()

# CORS FIX (VERY IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables
Base.metadata.create_all(bind=engine)


def ensure_orders_owner_column():
    # Lightweight migration for existing SQLite DBs.
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(orders)")).fetchall()
        names = {col[1] for col in columns}
        if "created_by_email" not in names:
            conn.execute(text("ALTER TABLE orders ADD COLUMN created_by_email VARCHAR"))


ensure_orders_owner_column()

# Routes
app.include_router(order_router)
app.include_router(chat_router)
app.include_router(user_router)


@app.get("/")
def home():
    return {"message": "AI Manufacturing Order System Running"}
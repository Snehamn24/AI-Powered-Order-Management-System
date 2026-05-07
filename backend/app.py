from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from models import Base
from routes.orders import router as order_router
from routes.chat import router as chat_router

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

# Routes
app.include_router(order_router)
app.include_router(chat_router)


@app.get("/")
def home():
    return {"message": "AI Manufacturing Order System Running"}
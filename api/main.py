from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import ALLOWED_ORIGINS
from db import authenticate_user, fetch_dashboard_data

app = FastAPI(title="TrueStay API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str

DEFAULT_HOTEL_SLUG = "hotel_arena"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard")
def get_dashboard(hotel: str = Query(default=DEFAULT_HOTEL_SLUG)):
    data = fetch_dashboard_data(hotel)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No dashboard data for hotel '{hotel}'")
    return data


@app.post("/login")
def login(body: LoginRequest):
    user = authenticate_user(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user

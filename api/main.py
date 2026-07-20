from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from auth import CurrentUser, create_access_token, get_current_user
from chat import ask
from config import ALLOWED_ORIGINS
from db import (
    EmailAlreadyRegistered,
    UnknownHotelSlug,
    authenticate_user,
    fetch_dashboard_data,
    register_user,
    search_hotels,
    set_user_plan,
)

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


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=72)
    hotel_slug: str | None = None
    new_hotel_name: str | None = Field(default=None, max_length=200)
    # Only "starter" is settable at registration — no payment/entitlement
    # verification exists anywhere yet, so a wide-open plan field here would
    # let anyone self-assign a paid tier for free.
    plan: Literal["starter"] | None = None

    @model_validator(mode="after")
    def _exactly_one_hotel_choice(self):
        if bool(self.hotel_slug) == bool(self.new_hotel_name):
            raise ValueError("Provide exactly one of hotel_slug or new_hotel_name")
        return self


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class PlanRequest(BaseModel):
    plan: Literal["starter", "hotel_partner", "corporate"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard")
def get_dashboard(current_user: CurrentUser = Depends(get_current_user)):
    data = fetch_dashboard_data(current_user.hotel_slug)
    if data is None:
        raise HTTPException(status_code=404, detail="No dashboard data for your account's hotel")
    return data


@app.post("/login")
def login(body: LoginRequest):
    user = authenticate_user(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(email=user["email"], hotel_slug=user["hotel_slug"])
    return {"token": token, **user}


@app.post("/register", status_code=201)
def register(body: RegisterRequest):
    try:
        user = register_user(
            name=body.name,
            email=body.email,
            password=body.password,
            hotel_slug=body.hotel_slug,
            new_hotel_name=body.new_hotel_name,
            plan=body.plan,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=409, detail="Email already registered")
    except UnknownHotelSlug:
        raise HTTPException(status_code=400, detail="Selected hotel was not found — please search again")

    token = create_access_token(email=user["email"], hotel_slug=user["hotel_slug"])
    return {"token": token, **user}


@app.get("/hotels/search")
def hotels_search(q: str = Query(default="", min_length=0, max_length=200)):
    if not q.strip():
        return []
    return search_hotels(q.strip())


@app.post("/me/plan")
def me_plan(body: PlanRequest, current_user: CurrentUser = Depends(get_current_user)):
    set_user_plan(current_user.email, body.plan)
    return {"plan": body.plan}


@app.post("/chat")
def chat(body: ChatRequest, current_user: CurrentUser = Depends(get_current_user)):
    context = fetch_dashboard_data(current_user.hotel_slug)
    if context is None:
        raise HTTPException(status_code=404, detail="No dashboard data for your account's hotel")
    return {"answer": ask(body.question, context)}

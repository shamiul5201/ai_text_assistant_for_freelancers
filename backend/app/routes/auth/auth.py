# backend/app/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, validator
from app.core.auth import hash_password, verify_password, create_access_token, verify_token
from app.database import get_db
from app.models.user_model import User
import re

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str

    @validator("username")
    def validate_username(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return value.strip()
    
    @validator("password")
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"[0-9]", value):
            raise ValueError("Password must include both letters and numbers.")
        return value

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --------------------------------------------------
# ✅ Register endpoint with DB-level checks
# --------------------------------------------------
@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 1️⃣ Check if username already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists. Please choose another one.")

    # 2️⃣ Hash password & create user
    new_user = User(username=request.username, hashed_password=hash_password(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3️⃣ Success response
    return {"message": "User registered successfully"}

# --------------------------------------------------
# ✅ Login endpoint (unchanged except for clarity)
# --------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # 1️⃣ Check user existence
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")

    # 2️⃣ Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # 3️⃣ Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(hours=12)
    )

    return {"access_token": access_token, "token_type": "bearer"}

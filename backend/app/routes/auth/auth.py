from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import timedelta
from app.core.auth import hash_password, verify_password, create_access_token, verify_token


router = APIRouter()

users_db = {}

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register")
async def register(request: RegisterRequest):
    if request.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db[request.username] = {
        "username" : request.username,
        "hashed_password" : hash_password(request.password)
    }

    return {"message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = users_db.get(request.username)
    if not user or not verify_password(request.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data = {"sub": request.username}, expires_delta=timedelta(hours=24))

    return {"access_token": access_token, "token_type": "bearer"}


# Example of protected route
@router.get("/protected")
async def protected_route(username: str = Depends(verify_token)):
    return {"message": f"Hello, {username}. You are authenticated"}
  
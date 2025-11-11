from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.user_model import User
from app.core.auth import create_access_token, verify_password, hash_password
from app.utils.rate_limiter import remaining_requests
import re   # 🟢 [ADDED] for regex password validation

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse("/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# @router.post("/login", response_class=HTMLResponse)
# async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.username == username).first()
#     if not user or not verify_password(password, user.hashed_password):
#         # 🟢 [UNCHANGED] just clear error message for consistency
#         return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
#     token = create_access_token(data={"sub": username}, expires_delta=timedelta(hours=24))
#     response = RedirectResponse(url="/chat", status_code=302)
#     response.set_cookie(key="access_token", value=token, httponly=True)
#     return response
@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    # 🟢 [1] If username not found → show error below username field
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "username_error": "This username does not exist. Please register first.",
                "password_error": None
            }
        )

    # 🟢 [2] If password incorrect → show error below password field
    if not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "username_error": None,
                "password_error": "Incorrect password. Please try again."
            }
        )

    # 🟢 [3] On success → create token and redirect
    token = create_access_token(data={"sub": username}, expires_delta=timedelta(hours=24))
    response = RedirectResponse(url="/chat", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response



@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 🟢 [NEW BLOCK] Username validation
    if len(username.strip()) < 3:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "username_error": "Username must be at least 3 characters long.",
                "password_error": None
            }
        )

    # 🟢 [NEW BLOCK] Password validation (min 6 chars, must include letters & digits)
    if len(password) < 6 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "username_error": None,
                "password_error": "Password must be at least 6 characters long and include both letters and numbers."
            }
        )

    # 🟢 [UPDATED BLOCK] Duplicate username check with friendly message
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Username already exists. Please choose another one."
            }
        )

    # 🟢 [UNCHANGED] Create and save new user
    user = User(username=username.strip(), hashed_password=hash_password(password))
    db.add(user)
    db.commit()

    # 🟢 [UNCHANGED] Success redirect message
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "message": "Registered successfully. Please log in."
        }
    )


@router.post("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except:
        return RedirectResponse("/login")

    remaining = remaining_requests(username)
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "username": username, "remaining": remaining}
    )

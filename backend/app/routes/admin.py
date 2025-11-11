# # backend/app/routes/admin.py
# import os, json
# from fastapi import APIRouter, Request, Form, Depends
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
# from sqlalchemy.orm import Session
# from app.database import get_db
# from app.models.user_model import User
# from app.utils.rate_limiter import load_limits, save_limits
# from dotenv import load_dotenv

# load_dotenv()
# router = APIRouter()
# templates = Jinja2Templates(directory="app/templates")

# ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
# ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# @router.get("/admin", response_class=HTMLResponse)
# async def admin_login_page(request: Request):
#     return templates.TemplateResponse("admin.html", {"request": request})

# @router.post("/admin", response_class=HTMLResponse)
# async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
#     if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
#         return templates.TemplateResponse("admin.html", {"request": request, "error": "Invalid admin credentials"})
#     response = RedirectResponse("/admin/dashboard", status_code=302)
#     response.set_cookie(key="admin_logged_in", value="true", httponly=True)
#     return response

# @router.get("/admin/dashboard", response_class=HTMLResponse)
# async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
#     if request.cookies.get("admin_logged_in") != "true":
#         return RedirectResponse("/admin")
#     users = db.query(User).all()
#     usage_data = load_limits()
#     return templates.TemplateResponse("admin_dashboard.html", {
#         "request": request,
#         "users": users,
#         "usage": usage_data
#     })

# @router.get("/admin/logs", response_class=HTMLResponse)
# async def view_logs(request: Request):
#     if request.cookies.get("admin_logged_in") != "true":
#         return RedirectResponse("/admin")
#     try:
#         with open("logs.json", "r") as f:
#             logs = json.load(f)
#     except:
#         logs = []
#     return templates.TemplateResponse("admin_logs.html", {"request": request, "logs": logs})


# backend/app/routes/admin.py
import os, json
from datetime import date
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User
from app.utils.rate_limiter import load_limits, save_limits
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# --------------------------- LOGIN / AUTH ---------------------------

@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login form."""
    return templates.TemplateResponse("admin.html", {"request": request})


@router.post("/admin", response_class=HTMLResponse)
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Verify admin credentials and set cookie."""
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        return templates.TemplateResponse(
            "admin.html", {"request": request, "error": "Invalid admin credentials"}
        )

    response = RedirectResponse("/admin/dashboard", status_code=302)
    response.set_cookie(key="admin_logged_in", value="true", httponly=True)
    return response


def admin_required(request: Request):
    if request.cookies.get("admin_logged_in") != "true":
        raise HTTPException(status_code=403, detail="Admin access required")

# --------------------------- DASHBOARD ---------------------------

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Main admin control panel with usage + user stats."""
    admin_required(request)

    users = db.query(User).all()
    usage_data = load_limits()

    # Summary stats
    total_users = len(users)
    total_generations = sum(u["count"] for u in usage_data.values()) if usage_data else 0
    active_today = len([u for u in usage_data.values() if u["date"] == str(date.today())])

    summary = {
        "total_users": total_users,
        "total_generations": total_generations,
        "active_today": active_today
    }

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "users": users, "usage": usage_data, "summary": summary},
    )

# --------------------------- ACTIONS ---------------------------

@router.post("/admin/reset-usage")
async def reset_all_usage(request: Request):
    """Reset all usage counts."""
    admin_required(request)
    open("app/utils/usage_limits.json", "w").write("{}")
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.post("/admin/reset-user")
async def reset_user_limit(request: Request, username: str = Form(...)):
    """Reset a single user's usage count."""
    admin_required(request)
    data = load_limits()
    if username in data:
        del data[username]
        save_limits(data)
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.post("/admin/delete-user")
async def delete_user(
    request: Request, username: str = Form(...), db: Session = Depends(get_db)
):
    """Delete a user account."""
    admin_required(request)
    db.query(User).filter(User.username == username).delete()
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/admin/logs", response_class=HTMLResponse)
async def view_logs(request: Request):
    """View AI generation logs."""
    admin_required(request)
    try:
        with open("logs.json", "r") as f:
            logs = json.load(f)
    except:
        logs = []
    return templates.TemplateResponse("admin_logs.html", {"request": request, "logs": logs})


@router.post("/admin/logout")
async def admin_logout():
    """Clear admin cookie."""
    response = RedirectResponse("/admin", status_code=302)
    response.delete_cookie("admin_logged_in")
    return response

import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import init_db, get_db, SessionLocal
import models
from auth import decode_access_token
from routers import auth as auth_router
from routers import admin as admin_router
from routers import operations as operations_router
from routers import driver as driver_router

app = FastAPI(
    title="Bus Depot Management System",
    description="Enterprise Bus Depot Operations, Fleet, Route, and Driver Scheduling System",
    version="1.0.0"
)

# Initialize Database tables on application start
@app.on_event("startup")
def on_startup():
    init_db()

# Mount Static Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Register API Routers
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(operations_router.router)
app.include_router(driver_router.router)

def get_current_user_from_cookie(request: Request, db: Session) -> tuple[bool, str, dict]:
    """Helper to check authentication state from browser cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return False, "", {}

    if token.startswith("Bearer "):
        token = token[7:]

    payload = decode_access_token(token)
    if not payload:
        return False, "", {}

    username = payload.get("sub")
    if not username:
        return False, "", {}

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.is_active:
        return False, "", {}

    return True, user.role, user.to_dict()

# ==========================================
# PAGE ROUTES WITH ROLE-BASED ACCESS CONTROL
# ==========================================

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request, db: Session = Depends(get_db)):
    is_auth, role, _ = get_current_user_from_cookie(request, db)
    if is_auth:
        if role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
        elif role == "operations":
            return RedirectResponse(url="/operations/dashboard", status_code=status.HTTP_302_FOUND)
        elif role == "driver":
            return RedirectResponse(url="/driver/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    is_auth, role, _ = get_current_user_from_cookie(request, db)
    if is_auth:
        if role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
        elif role == "operations":
            return RedirectResponse(url="/operations/dashboard", status_code=status.HTTP_302_FOUND)
        elif role == "driver":
            return RedirectResponse(url="/driver/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request, db: Session = Depends(get_db)):
    is_auth, role, user = get_current_user_from_cookie(request, db)
    if not is_auth:
        return RedirectResponse(url="/login?error=auth_required", status_code=status.HTTP_302_FOUND)

    if role != "admin":
        if role == "operations":
            return RedirectResponse(url="/operations/dashboard?warning=forbidden", status_code=status.HTTP_302_FOUND)
        elif role == "driver":
            return RedirectResponse(url="/driver/dashboard?warning=forbidden", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/login?error=unauthorized", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="admin_dashboard.html", context={
        "user": user
    })

@app.get("/operations/dashboard", response_class=HTMLResponse)
def operations_dashboard_page(request: Request, db: Session = Depends(get_db)):
    is_auth, role, user = get_current_user_from_cookie(request, db)
    if not is_auth:
        return RedirectResponse(url="/login?error=auth_required", status_code=status.HTTP_302_FOUND)

    if role not in ["operations", "admin"]:
        if role == "driver":
            return RedirectResponse(url="/driver/dashboard?warning=forbidden", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/login?error=unauthorized", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="operations_dashboard.html", context={
        "user": user
    })

@app.get("/driver/dashboard", response_class=HTMLResponse)
def driver_dashboard_page(request: Request, db: Session = Depends(get_db)):
    is_auth, role, user = get_current_user_from_cookie(request, db)
    if not is_auth:
        return RedirectResponse(url="/login?error=auth_required", status_code=status.HTTP_302_FOUND)

    if role not in ["driver", "admin"]:
        if role == "operations":
            return RedirectResponse(url="/operations/dashboard?warning=forbidden", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/login?error=unauthorized", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="driver_dashboard.html", context={
        "user": user
    })

# Generic 404 / 500 JSON handler for API
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and not request.url.path.startswith(("/auth", "/admin/stats", "/admin/users", "/operations/", "/driver/")):
        if exc.status_code == 401:
            return RedirectResponse(url="/login?error=session_expired", status_code=status.HTTP_302_FOUND)
        elif exc.status_code == 403:
            return RedirectResponse(url="/login?error=forbidden", status_code=status.HTTP_302_FOUND)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

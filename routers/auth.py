from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import verify_password, create_access_token, get_current_user, log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    identifier = login_data.username.strip()
    password = login_data.password.strip()

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required."
        )

    # Allow login by username OR email
    user = db.query(models.User).filter(
        (models.User.username == identifier) | (models.User.email == identifier)
    ).first()

    if not user or not verify_password(password, user.password_hash):
        log_activity(db, None, identifier, None, "Login Failed", f"Failed login attempt for identifier: {identifier}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    if not user.is_active:
        log_activity(db, user.id, user.username, user.role, "Login Rejected", "Inactive user attempted login")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact the administrator."
        )

    # Determine redirect URL based on user role
    role_redirects = {
        "admin": "/admin/dashboard",
        "operations": "/operations/dashboard",
        "driver": "/driver/dashboard"
    }
    redirect_url = role_redirects.get(user.role, "/login")

    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role
    }
    access_token = create_access_token(token_data)

    # Set HTTP-only cookie for secure browser navigation
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 8, # 8 hours
        samesite="lax",
        secure=False # Set to True in production HTTPS
    )

    log_activity(db, user.id, user.username, user.role, "Login", f"User {user.username} logged in successfully as {user.role}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "redirect_url": redirect_url
    }

@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request=request, db=db)
        log_activity(db, user.id, user.username, user.role, "Logout", f"User {user.username} logged out")
    except Exception:
        pass

    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    user_dict = current_user.to_dict()
    if current_user.role == "driver" and current_user.driver_profile:
        user_dict["driver_profile"] = current_user.driver_profile.to_dict()
    return user_dict

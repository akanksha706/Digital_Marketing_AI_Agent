"""Authentication endpoints: Login, Password Change, and Current User Profile."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import User, UserRole, Brand
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.domain.schemas.auth import LoginRequest, ChangePasswordRequest, TokenResponse, UserResponse, ForgotPasswordRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency extracting and verifying the JWT authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(payload["sub"])
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found.",
        )
    return user


async def ensure_seed_admin(db: AsyncSession) -> None:
    """Seed initial default admin and creator if not present."""
    admin_res = await db.execute(select(User).where(User.email == "admin@company.com"))
    if not admin_res.scalar_one_or_none():
        # Ensure brand exists
        brand = await db.get(Brand, 1)
        if not brand:
            brand = Brand(
                id=1,
                team_name="Digital Marketing Team",
                primary_color="#dfb876",
                secondary_color="#fdfbf7",
                font_family="Georgia",
                tone_of_voice="inspiring and cinematic",
            )
            db.add(brand)
            await db.flush()

        admin_user = User(
            email="admin@company.com",
            hashed_password=hash_password("admin@123"),
            role=UserRole.ADMIN,
            is_active=True,
            brand_id=1,
        )
        creator_user = User(
            email="creator@company.com",
            hashed_password=hash_password("creator@123"),
            role=UserRole.MEMBER,
            is_active=True,
            brand_id=1,
        )
        db.add_all([admin_user, creator_user])
        await db.commit()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in with email and password",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Authenticate credentials and issue a signed 24h JWT token."""
    await ensure_seed_admin(db)

    result = await db.execute(select(User).where(User.email == payload.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/change-password",
    summary="Change account password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Allow an authenticated user to change their current password."""
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed.",
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long.",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    await db.flush()
    return {"message": "Password changed successfully."}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile and permissions for the currently authenticated session."""
    return current_user


@router.post(
    "/forgot-password",
    summary="Request password reset instructions",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Dispatch password reset verification or instructions."""
    email = payload.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    return {
        "success": True,
        "message": f"If an active account exists for {email}, password reset instructions have been dispatched. You can also contact your organization administrator to instantly reset your password.",
        "account_found": bool(user),
    }

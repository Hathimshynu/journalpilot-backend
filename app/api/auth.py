from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
)
def register(
    data: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):

    email = data.email.lower().strip()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        name=data.name.strip(),
        email=email,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(
            user,
            from_attributes=True,
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):

    email = data.email.lower().strip()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(
            user,
            from_attributes=True,
        ),
    )


@router.post(
    "/google",
    response_model=TokenResponse,
)
def google_login(
    data: GoogleLoginRequest,
    db: Annotated[Session, Depends(get_db)],
):

    try:

        google_user = id_token.verify_oauth2_token(
            data.credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

    except ValueError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    google_id = google_user.get("sub")
    email = google_user.get("email")
    name = google_user.get("name")
    picture = google_user.get("picture")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account information is incomplete",
        )

    email = email.lower().strip()

    user = (
        db.query(User)
        .filter(User.google_id == google_id)
        .first()
    )

    if not user:

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    if not user:

        user = User(
            name=name or email.split("@")[0],
            email=email,
            google_id=google_id,
            profile_image=picture,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    else:

        if not user.google_id:
            user.google_id = google_id

        if picture:
            user.profile_image = picture

        db.commit()
        db.refresh(user)

    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(
            user,
            from_attributes=True,
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):

    return current_user
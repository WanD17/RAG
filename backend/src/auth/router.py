from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import schemas, service
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: schemas.UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await service.create_user(db, payload.email, payload.password, payload.full_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = service.create_access_token(user.id, user.email)
    return schemas.RegisterResponse(
        user=schemas.UserResponse.model_validate(user),
        access_token=token,
    )


@router.post("/login", response_model=schemas.TokenResponse)
async def login(payload: schemas.UserLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await service.authenticate_user(db, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = service.create_access_token(user.id, user.email)
    return schemas.TokenResponse(access_token=token)

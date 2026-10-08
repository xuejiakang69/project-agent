from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.auth import add_user
from app.crud.user import update_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import CreateResult
from app.schemas.common import Result
from app.schemas.user import UserRequest, UserUpdateRequest
from app.utils.auth import get_current_user


router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/register")
async def create_user(
    data: CreateResult,
    db: AsyncSession = Depends(get_db),
) -> Result[UserRequest]:
    user = await add_user(data, db)
    if not user:
        raise HTTPException(status_code=400, detail="已有该用户名")

    return Result[UserRequest](
        result=UserRequest.model_validate(user)
    )


@router.post("/update")
async def update_user_profile(
    data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[UserRequest]:
    user = await update_user(current_user, data, db)

    return Result[UserRequest](
        result=UserRequest.model_validate(user)
    )
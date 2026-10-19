from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import get_users_paginated, update_user, update_user_status, get_user_by_id,add_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import CreateResult
from app.schemas.common import Result
from app.schemas.user import UserAllResult, UserRequest, UserStatusUpdateRequest, UserUpdateRequest
from app.utils.auth import get_current_user,get_user_by_main


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


@router.post("/status")
async def change_user_status(
    data: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_by_main),
) -> Result[UserRequest]:
    user = await get_user_by_id(data.id, db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    allowed_transitions = {(3, 1), (1, 0)}
    if (user.status, data.status) not in allowed_transitions:
        raise HTTPException(status_code=400, detail="当前状态不允许该操作")

    user = await update_user_status(user, data.status, db)
    return Result[UserRequest](
        result=UserRequest.model_validate(user)
    )


#查询全部用户
@router.get("/all")
async def list_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_by_main),
) -> Result[UserAllResult]:
    users, total = await get_users_paginated(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
    )

    return Result[UserAllResult](
        result=UserAllResult(
            items=[UserRequest.model_validate(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )
    )

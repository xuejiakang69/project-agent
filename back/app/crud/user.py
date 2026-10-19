from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import CreateResult
from app.schemas.user import UserUpdateRequest
from app.utils.password import hashed_password


#根据用户名查找
async def get_user_by_username(
    username: str,
    db: AsyncSession,
) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

#添加用户
async def add_user(data: CreateResult, db: AsyncSession):
    existing_user = await get_user_by_username(data.username, db)
    if existing_user:
        return None

    user = User(
        username=data.username,
        password=hashed_password(data.password),
        email=data.email,
        name=data.name,
        phone=data.phone,
        status=3
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

#更新用户
async def update_user(
    current_user: User,
    data: UserUpdateRequest,
    db: AsyncSession,
) -> User:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)
    return current_user


async def get_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user_status(
    user: User,
    status: int,
    db: AsyncSession,
) -> User:
    user.status = status
    await db.flush()
    await db.refresh(user)
    return user



#查看所有用户 （只有管理员才有权限）
async def get_users_paginated(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
) -> tuple[list[User], int]:
    stmt = select(User)
    count_stmt = select(func.count(User.id))

    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(User.username.ilike(pattern))
        count_stmt = count_stmt.where(User.username.ilike(pattern))

    total = await db.scalar(count_stmt) or 0
    result = await db.execute(
        stmt.order_by(User.create_time.desc(), User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total
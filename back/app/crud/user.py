from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import CreateResult
from app.schemas.user import UserUpdateRequest
from app.utils.password import hashed_password


async def get_user_by_username(
    username: str,
    db: AsyncSession,
) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


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
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


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
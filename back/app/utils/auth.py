from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.jwt import decode_token


bearer_schema = HTTPBearer(
    bearerFormat="JWT",
    scheme_name = "bearerAuth",
    auto_error= True
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    try:
        user_id = int(payload.get("user_id"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中没有用户信息",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return user

#查看是否为管理员权限
async def get_user_by_main(current_user:User=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(detail="没有权限",status_code=status.HTTP_403_FORBIDDEN)
    return current_user
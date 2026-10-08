from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import LoginRequest,CreateResult
from app.utils.password import verify_password,hashed_password


#根据用户名查询信息
async def get_user_by_username(username:str,db:AsyncSession):
    user = select(User).where(User.username==username)
    result = await db.execute(user)
    return result.scalar_one_or_none()

#根据用户名查询密码是否正确
async def get_user_by_password(data:LoginRequest,db:AsyncSession):
    get_user = await get_user_by_username(data.username,db)
    if not get_user:
        return None
    if not verify_password(data.password,get_user.password):
        return None
    return get_user


#注册用户
async def add_user(data:CreateResult,db:AsyncSession):
    exi = await get_user_by_username(data.username,db)
    if exi:
         return None
    hash_password = hashed_password(data.password)
    user = User(
        username=data.username,
        password=hash_password,
        email=data.email,
        name = data.name,
        phone= data.phone
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
from fastapi import APIRouter,Depends,HTTPException
from app.schemas.auth import LoginRequest,CreateResult
from app.schemas.user import LoginResult,UserRequest
from app.schemas.common import Result
from sqlalchemy.ext.asyncio import AsyncSession 
from app.database import get_db
from app.crud.auth import get_user_by_password,add_user
from app.utils.jwt import create_jwt_token


router=APIRouter(tags=["权限验证"],prefix="/api/auth")

#登陆
@router.post("/login")
async def login(data:LoginRequest,db:AsyncSession=Depends(get_db))->Result[LoginResult]:
    user = await get_user_by_password(data,db)
    if not user:
        raise HTTPException(status_code=400,detail="用户名或密码错误")
    if user.status== 0:
        raise HTTPException(status_code=401,detail="账号已停用")
    if user.status== 3:
        raise HTTPException(status_code=401,detail="账号审核中请稍后再试")
    token = create_jwt_token(data={"sub":user.username,"user_id":user.id})
    return Result[LoginResult](result=LoginResult(data=UserRequest.model_validate(user),token=token))


from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession




router = APIRouter(prefix="/api/lad",tags=["实验室管理"])



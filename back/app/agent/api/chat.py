from fastapi import APIRouter, Depends,HTTPException
from app.agent.schemas.chat import ChatRequest,ChatMessages
from app.agent.crud.chat import chat_with_model
from app.utils.auth import get_current_user
from app.schemas.common import Result

router = APIRouter(prefix="/api/agent", tags=["智能助手"])



@router.post("/chat")
async def chat(data: ChatRequest,current_user = Depends(get_current_user))-> Result[ChatMessages]:
    """与大模型进行对话"""
    content = await chat_with_model(data)
    print("content:",content)
    return Result[ChatMessages](result=ChatMessages.model_validate({"role":"assistant","content":content}))

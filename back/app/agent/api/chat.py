from fastapi import APIRouter, Depends,HTTPException
from fastapi.responses import StreamingResponse
from app.agent.schemas.chat import ChatRequest,ChatMessages
from app.agent.crud.chat import stream_agent, stream_agent_events
from app.utils.auth import get_current_user
from app.schemas.common import Result
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/agent", tags=["智能助手"])



@router.post("/chat")
async def chat(data: ChatRequest,current_user = Depends(get_current_user),db:AsyncSession=Depends(get_db))-> Result[ChatMessages]:
    """与大模型进行对话"""
    content = await stream_agent(db,current_user,data)

    return Result[ChatMessages](result=ChatMessages.model_validate({"role":"assistant","content":content}))


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Return model output as SSE while preserving reservation tools."""
    return StreamingResponse(
        stream_agent_events(db, current_user, data),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

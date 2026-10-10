from fastapi import HTTPException
from openai import OpenAI,AsyncOpenAI
from app.config import settings
from app.agent.schemas.chat import ChatRequest, ChatMessages

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
你可以介绍本系统的预约流程：
1. 登录后打开实验室列表，选择实验室或设备
2. 填写日期和时段并提交，状态为待审核
3. 管理员审核通过后即可使用
4. 待审核、已通过的预约，本人可以取消
你目前查不到真实的实验室、设备、预约数据。
如果用户问某个实验室几点开门、有没有某台设备，请说明去「实验室列表」查看，不要编造具体数据。
如果用户问了跟实验室无关的问题，可以直接拒绝回答。
"""



async def create_model():

    if not settings.AGENT_KEY or not settings.AGENT_URL or not settings.AGENT_MODEL:
        raise ValueError("大模型配置不完整，请检查 .env 文件中的 AGENT_KEY、AGENT_URL 和 AGENT_MODEL 配置。")

    """创建大模型客户端"""
    model = AsyncOpenAI(
        api_key=settings.AGENT_KEY,
        base_url=settings.AGENT_URL,
    )
    return model

async def chat_with_model(data:ChatRequest):
    """与大模型进行对话"""
    print("data:",data)
    messages = []
    for message in data.messages:
        if message.role in ["user", "assistant"] and message.content:
            messages.append({"role": message.role, "content": message.content})
    if not messages:
        raise ValueError("请输入您想要的对话")

    model = await create_model()
    try:
        res = await model.chat.completions.create(
            model = settings.AGENT_MODEL,
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *messages
            ],
        )
        print("res:",res)
        content = res.choices[0].message.content
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大模型请求失败: {str(e)}")
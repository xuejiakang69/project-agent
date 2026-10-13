import json
from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.crud.ai_tool import call_tools
from app.agent.crud.kb import async_search
from app.config import settings
from app.models.user import User
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from app.agent.schemas.chat import ChatRequest
from typing import Any

SYSTEM_PROMPT = """你是智能实验室预约系统的 Agent，回答要简洁。
你可以：
1. 使用 search_lab_docs 查询实验室的规则、安全、开放时间等问题
2. 使用 list_open_labs / list_lab_equipments  查询真实的实验室和设备
3. 再用户进行了预约确认后，使用 create_lab_reservation 来进行真实的预约落库
4. 使用 get_today 来进行日期的换算
## 必须遵守
当用户提到了 今天、明天、后天 等日期相关的问题，请先调用 get_today 来获取日期，**不要直接返回 我需要确定明天的具体日期**。
在提交预约之前必须向用户复述：实验室ID与名称（或设备ID和名称）、日期、开始时间、结束时间。并得到用户确认再进行实际操作。
用户没说【确认】【确认预约】【就这样预约】等确定性回复之前，不要调用 create_lab_reservation。
工作流的确认环节里如果缺少了 lab_id，请先 list_open_labs 查到了 lab_id 再创建，不要瞎写。
工作流的确认环节里如果缺少了 equipment_id，请先 list_lab_equipments 查到了 equipment_id 再创建，不要瞎写。
预约成功后状态是待审核，必须管理员确认后实验室（或设备）才能使用。
不要瞎编数据库里没有的实验室或者设备信息。
如果是问开放时间或者实验室规则，优先调用 search_lab_docs，不要凭空回复。
"""


def _build_history(data: ChatRequest):
    """前端只传user/assistant 文本，转成langchain消息对象"""
    messages = []
    for message in data.messages or []:
        if message.role == "user" and message.content.strip():
            messages.append(HumanMessage(content=message.content))
        if message.role == "assistant" and message.content.strip():
            messages.append(AIMessage(content=message.content))
    if not messages:
        raise HTTPException(status_code=400,detail="请输入")
    return messages


async def build_agent(db: AsyncSession, current_user: User):
    tools = await call_tools(db, current_user)
    llm = ChatOpenAI(
        model=settings.AGENT_MODEL,
        api_key=settings.AGENT_KEY,
        base_url=settings.AGENT_URL,
        temperature=0,
    ).bind_tools(tools)

    async def agent_node(state: MessagesState):
        """langraph工作流"""
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)  # 调用大模型
    graph.add_node("tools", ToolNode(tools))  # tool节点
    graph.add_edge(START, "agent")  # 流程的起点
    graph.add_conditional_edges(
        "agent", tools_condition
    )  # 看有无tool 有就继续 没有则END输出
    graph.add_edge("tools", "agent")
    return graph.compile()


async def stream_agent(db: AsyncSession, current_user: User, data: ChatRequest):

    messages = _build_history(data)
    agent = await build_agent(db, current_user)
    try:
        result =await agent.ainvoke({"messages":[SystemMessage(content=SYSTEM_PROMPT), *messages]})
        print(f"messages:",result)

    except Exception:
        raise HTTPException(status_code=400, detail="大模型调用失败")

    msg = result.get("messages") or []
    if not msg:
        raise HTTPException(status_code=400, detail="大模型没有回答")
    for message in reversed(msg):
        if isinstance(message, AIMessage) and message.content.strip():
            content = message.content.strip()
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dist) else str(part)
                    for part in content
                )
            if str(content).strip():
                return str(content).strip()
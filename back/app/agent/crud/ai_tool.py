from datetime import datetime, time

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.equipment import get_equipments_paginated
from app.crud.lab import get_labs_paginated
from app.agent.crud.kb import async_search
from app.models.user import User
from app.models.reservation import Reservation
from app.crud.reservation import create_reservation, get_reservations_by_user


async def call_tools(db: AsyncSession, current_user: User):

    @tool
    async def list_open_labs(keyword: str | None = None):
        """查看可用实验室"""
        print(f"读取实验室设备")
        labs, total = await get_labs_paginated(
            db, page=1, page_size=100, keyword=keyword, status=1
        )

        return {
            "total": total,
            "labs": [
                {
                    "id": lab.id,
                    "name": lab.name,
                    "location": lab.location,
                    "open_time": lab.open_time,
                    "close_time": lab.close_time,
                }
                for lab in labs
            ],
        }

    @tool
    async def search_lab_docs(query: str):
        """根据用户提问来检索知识库"""
        try:
            return await async_search(query) or "知识库未查询到相关资料"
        except Exception as ex:
            return {"error": ex}

    @tool
    async def list_lab_equipments(lab_id: int, keywords: str):
        """
        查询指定实验室的设备列表。

        使用规则：
        1. 用户询问某实验室有哪些设备、全部设备时，keywords 传空字符串。
        2. 只有用户明确指定设备名称或类型时，才传入 keywords。
        3. lab_id 必须来自 list_open_labs 的真实查询结果，
            不允许猜测实验室 ID。
        4. 如果查询结果为空，不要反复尝试不同关键词，
            应先确认实验室 ID 是否正确。
        """
        try:
            keywords = keywords.strip() or None
            rows, total = await get_equipments_paginated(
                db,
                page=1,
                page_size=100,
                keyword=keywords,
                lab_id=lab_id,
            )
            return {
                "equipment": [
                    {
                        "id": equipment.id,
                        "name": equipment.name,
                        "spec": equipment.spec,
                        "quantity": equipment.quantity,
                        "lab_id": equipment.lab_id,
                        "lab_name": lab_name,
                    }
                    for equipment, lab_name in rows
                ]
            }
        except Exception as ex:
            return {"error": ex}

    @tool
    async def create_lab_reservation(
        lab_id: int,
        date: str,
        start_time: str,
        end_time: str,
        equipment_id: int | None = None,
        remark: str | None = None,
    ):
        """创建预约单实验室或者设备"""
        try:
            data = Reservation(
                lab_id=lab_id,
                equipment_id=equipment_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                remark=remark,
            )
            await create_reservation(data, current_user, db)
            return {
                "messages": "预约成功，等待管理员审核",
                "lab_id": lab_id,
                "equipment_id": equipment_id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
            }
        except Exception as ex:
            return {"error": ex}

    @tool
    def get_today() -> str:
        """获取服务器当前的日期  2026-09-20"""
        now = datetime.now()
        return now.strftime("%Y-%m-%d")

    @tool
    async def get_user_by_reserve():
        """当前用户预约信息"""
        result, _ = await get_reservations_by_user(
            current_user,
            db,
            page_size=100,
            allowed_statuses=[0, 1],
        )

        return {
            "reserve": [
                {
                    "id": reservation.id,
                    "user_name": reservation.user_name,
                    "lab_id": reservation.lab_id,
                    "lab_name": reservation.lab_name,
                    "equipment_id": reservation.equipment_id,
                    "equipment_name": reservation.equipment_name,
                    "date": reservation.date,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                    "status": reservation.status,
                }
                for reservation in result
            ]
        }

    return [
        search_lab_docs,
        list_open_labs,
        list_lab_equipments,
        create_lab_reservation,
        get_today,
        get_user_by_reserve,
    ]

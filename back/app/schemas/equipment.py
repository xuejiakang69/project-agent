from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EquipmentStatus = Literal[0, 1]


# 实验室设备信息
class EquipmentRequest(BaseModel):
    id: int
    lab_id: int
    lab_name: str | None = None
    name: str
    description: str | None = Field(default=None, max_length=500)
    img: str | None = Field(default=None, max_length=200)
    spec: str | None = Field(default=None, max_length=100)
    quantity: int = Field(ge=0)
    status: EquipmentStatus

    model_config = ConfigDict(from_attributes=True)


# 创建实验室设备
class EquipmentCreateRequest(BaseModel):
    lab_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    img: str | None = Field(default=None, max_length=200)
    spec: str | None = Field(default=None, max_length=100)
    quantity: int = Field(default=1, ge=0)
    status: EquipmentStatus = 1


# 修改实验室设备
class EquipmentUpdateRequest(BaseModel):
    lab_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    img: str | None = Field(default=None, max_length=200)
    spec: str | None = Field(default=None, max_length=100)
    quantity: int | None = Field(default=None, ge=0)
    status: EquipmentStatus | None = None


# 实验室设备分页信息
class EquipmentPageResult(BaseModel):
    items: list[EquipmentRequest]
    total: int
    page: int
    page_size: int
    total_pages: int
from pydantic import BaseModel, ConfigDict
#实验室的信息
class LadRequest(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: int
    location: str | None = None
    open_time: str | None = None
    close_time: str | None = None
    capacity: int | None = None


#修改实验室信息
class LadUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: int | None = None
    location: str | None = None
    open_time: str | None = None
    close_time: str | None = None
    capacity: int | None = None

#增加实验室信息
class LadCreateRequest(BaseModel):
    name: str
    description: str | None = None
    status: int | None = 1
    location: str | None = None
    open_time: str | None = None
    close_time: str | None = None
    capacity: int | None = None

#删除实验室信息
class LadDeleteRequest(BaseModel):
    id: int 
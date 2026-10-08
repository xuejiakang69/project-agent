from pydantic import BaseModel, ConfigDict

#用户的信息
class UserRequest(BaseModel):
    id: int
    username: str
    name: str
    role: str
    email: str | None = None
    phone: str | None = None
    status: int
    avatar: str | None = None

    model_config = ConfigDict(from_attributes=True)

#修改用户信息
class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None


class LoginResult(BaseModel):
    data: UserRequest
    token: str


#用户列表返回
class UserAllResult(BaseModel):
    items:list[UserRequest]
    total:int
    page:int
    page_size:int
    total_pages:int
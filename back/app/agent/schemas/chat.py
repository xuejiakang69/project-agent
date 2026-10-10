from pydantic import BaseModel


class ChatMessages(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessages]
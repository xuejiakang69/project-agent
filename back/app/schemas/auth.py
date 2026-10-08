from pydantic import BaseModel

class LoginRequest(BaseModel):
    username:str
    password:str

class CreateResult(LoginRequest):
    email:str|None = None
    name:str
    phone :str 

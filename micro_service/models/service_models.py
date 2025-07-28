# Pydantic модели для микросервиса

from pydantic import BaseModel


class AppStatus(BaseModel):
    database: bool

class RegisterRequest(BaseModel):
    email: str
    password: str

class RegisterResponse(BaseModel):
    id: int
    token: str

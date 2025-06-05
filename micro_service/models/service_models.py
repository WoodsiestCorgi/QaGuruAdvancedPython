# Pydantic модели для микросервиса

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    id: int
    token: str

class User(BaseModel):
    id: int
    token: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    avatar: str

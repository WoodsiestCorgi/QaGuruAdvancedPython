from pydantic import BaseModel, EmailStr, HttpUrl
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    avatar: str


class UserCreate(BaseModel):
    id: int | None = None
    token: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    avatar: HttpUrl

class UserUpdate(BaseModel):
    id: int = None
    token: str | None = None
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    avatar: HttpUrl | None = None

from http import HTTPStatus
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import select, Session

from .engine import db_engine
from ..models.User import User


def get_next_user_id() -> int:
    with Session(db_engine) as session:
        # Находим максимальный ID и прибавляем 1
        max_id = session.exec(func.max(User.id)).scalar()
        return (max_id or 0) + 1

def get_user(user_id: int) -> User | None:
    with Session(db_engine) as session:
        return session.get(User, user_id)


def get_users() -> Iterable[User]:
    with Session(db_engine) as session:
        statement = select(User)
        return session.exec(statement).all()

def create_user(user: User) -> User:
    user.id = get_next_user_id() if not user.id else user.id
    with Session(db_engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def delete_user(user_id: int) -> None:
    with Session(db_engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User id='{user_id}' not found")

        session.delete(db_user)
        session.commit()

def update_user(user_id: int, user: User) -> User:
    with Session(db_engine) as session:
        db_user = get_user(user_id)
        if not db_user:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User id='{user_id}' not found")

        user_data = user.model_dump(mode='json', exclude_none=True, exclude_unset=True)
        db_user.sqlmodel_update(user_data)

        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user


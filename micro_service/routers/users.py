from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page as BasePage, paginate, Params
from fastapi_pagination.customization import CustomizedPage, UseParamsFields

from micro_service.data.data_for_app import USER_ID_URL, USERS_URL
from micro_service.database import users
from micro_service.models.User import User, UserCreate, UserUpdate

router = APIRouter()

Page = CustomizedPage[
    BasePage,
    UseParamsFields(
            size=Query(50, ge=0)
            )
]


@router.get(USERS_URL, response_model=Page[User], status_code=HTTPStatus.OK)
async def get_users(params: Params = Depends()) -> Page[User]:
    return paginate(list(users.get_users()), params=params)


@router.get(USER_ID_URL, response_model=User, status_code=HTTPStatus.OK)
async def get_user(user_id) -> User:
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="User id must be integer")

    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="User id must be greater than 0")

    user = users.get_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User id not found")

    return user

@router.post(USERS_URL, status_code=HTTPStatus.CREATED)
def create_user(user_data: UserCreate) -> User:
    user_dict = user_data.model_dump(mode='json')
    user = User(**user_dict)
    return users.create_user(user)

@router.patch(USER_ID_URL, status_code=HTTPStatus.OK)
def update_user(user_id: int, user: UserUpdate) -> User:
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="User id must be greater than 0")

    UserUpdate.model_validate(user)
    user = User(**user.model_dump(mode='json'))
    return users.update_user(user_id, user)

@router.delete(USER_ID_URL, status_code=HTTPStatus.OK)
def delete_user(user_id: int):
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="User id must be greater than 0")

    users.delete_user(user_id)

    return {"message": "User deleted"}

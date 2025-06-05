import hashlib
import json
from http import HTTPStatus
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.params import Depends
from fastapi_pagination import add_pagination, Page, paginate, Params
from starlette.responses import JSONResponse

from data.data_for_app import GET_USERS_URL, REGISTER_URL, STATUS_URL
from micro_service.models.service_models import RegisterResponse, User

app = FastAPI()
add_pagination(app)
fake_db: dict[str, User] = {}


@app.post(REGISTER_URL, response_model=RegisterResponse, status_code=HTTPStatus.OK)
async def register_user(request: Request) -> RegisterResponse | JSONResponse:
    data = await request.json()

    if "email" not in data:
        return JSONResponse(status_code=400, content={"error": "Missing email"})
    if "password" not in data:
        return JSONResponse(status_code=400, content={"error": "Missing password"})

    if data['email'] in [_user.email for _user in fake_db.values()]:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = int(uuid4())
    token = str(hashlib.sha256(data['password'].encode()).hexdigest())

    fake_db[str(user_id)] = User(id=user_id, first_name=data.get("first_name"), last_name=data.get("last_name"),
                                 avatar=data.get("avatar"), email=data.get('email'), password=data.get('password'),
                                 token=token)


    return RegisterResponse(id=user_id, token=token)


@app.get(STATUS_URL, status_code=HTTPStatus.OK)
async def status() -> JSONResponse:
    if len(fake_db) == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No users registered")

    return JSONResponse(status_code=HTTPStatus.OK, content={"status": "ok"})


@app.get(GET_USERS_URL, response_model=Page[User], status_code=HTTPStatus.OK)
async def get_users(params: Params = Depends()) -> Page[User]:
    return paginate(list(fake_db.values()), params=params)


@app.get(GET_USERS_URL + "{user_id}", response_model=User, status_code=HTTPStatus.OK)
async def get_user(user_id) -> User:
    if str(user_id) not in fake_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")

    return fake_db[str(user_id)]


if __name__ == "__main__":
    with open("../data/users.json") as f:
        _users = json.load(f)

    for _id, user in _users.items():
        fake_db.update({f"{_id}": User.model_validate(user)})

    uvicorn.run(app, host="localhost", port=8000)

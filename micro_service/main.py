import hashlib
from typing import Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from starlette.responses import JSONResponse

from configs.regres_configs import REGISTER_URL
from micro_service.models.service_models import RegisterRequest, RegisterResponse

app = FastAPI()
fake_db: Dict[str, Dict] = {}


@app.post(REGISTER_URL, response_model=RegisterResponse)
async def register_user(request: Request):
    data = await request.json()

    if "email" not in data:
        return JSONResponse(status_code=400, content={"error": "Missing email"})
    if "password" not in data:
        return JSONResponse(status_code=400, content={"error": "Missing password"})

    data = RegisterRequest(**data)

    if data.email in fake_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = int(uuid4())

    fake_db[str(data.email)] = {
            "id":       str(user_id),
            "password": data.password,
            }

    token = str(hashlib.sha256(data.password.encode()).hexdigest())

    return RegisterResponse(id=user_id, token=token)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

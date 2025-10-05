from http import HTTPStatus

from fastapi import APIRouter

from data.data_for_app import STATUS_URL
from micro_service.database.engine import check_availability
from micro_service.models.service_models import AppStatus

router = APIRouter()


@router.get(STATUS_URL, status_code=HTTPStatus.OK)
async def status() -> AppStatus:
    check_availability()

    return AppStatus(database=check_availability())

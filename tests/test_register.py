from http import HTTPStatus

import requests

from configs.regres_configs import BASE_URL, TOKEN_HEADER
from data.data_for_app import REGISTER_URL
from data.data_for_tests import EXPECTED_ERROR, INVALID_REGISTER_REQUEST, REGISTER_REQUEST

TEST_URL = BASE_URL + REGISTER_URL


def test_successful_register(app_url):
    response = requests.post(app_url + REGISTER_URL,
                             json=REGISTER_REQUEST,
                             headers=TOKEN_HEADER)
    assert response.status_code == HTTPStatus.OK
    body = response.json()

    for key, value in body.items():
        assert key in ["id", "token"]
        assert value


def test_register_unsuccessful(app_url):
    response = requests.post(app_url + REGISTER_URL,
                             json=INVALID_REGISTER_REQUEST,
                             headers=TOKEN_HEADER)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.json()

    assert body == EXPECTED_ERROR

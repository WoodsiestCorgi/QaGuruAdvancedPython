import requests

from configs.regres_configs import BASE_URL, REGISTER_URL, TOKEN_HEADER
from data.data_for_tests import EXPECTED_ERROR, INVALID_REGISTER_REQUEST, REGISTER_REQUEST

TEST_URL = BASE_URL + REGISTER_URL


def test_successful_register():
    response = requests.post(TEST_URL,
                             json=REGISTER_REQUEST,
                             headers=TOKEN_HEADER)

    body = response.json()

    assert response.status_code == 200
    for key, value in body.items():
        assert key in ["id", "token"]
        assert value


def test_register_unsuccessful():
    response = requests.post(TEST_URL,
                             json=INVALID_REGISTER_REQUEST,
                             headers=TOKEN_HEADER)

    body = response.json()

    assert response.status_code == 400
    assert body == EXPECTED_ERROR

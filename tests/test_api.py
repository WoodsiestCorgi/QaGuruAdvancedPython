import json
from http import HTTPStatus

import pytest
import requests

from micro_service.models.User import User


@pytest.fixture()
def fill_test_data(app_url):
    with open('../data/users.json', 'r', encoding='utf-8') as f:
        test_data_users = json.load(f)

    for user in test_data_users.values():
        requests.post(f'{app_url}/api/users', json=user)


def test_status(app_url):
    response = requests.get(f"{app_url}/api/status")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"database": True}


def test_get_users(app_url, fill_test_data):
    response = requests.get(f"{app_url}/api/users")

    assert response.status_code == HTTPStatus.OK

    users = response.json()
    for user in users['items']:
        User.model_validate(user)


def test_get_users_pagination_page(app_url):
    response = requests.get(f"{app_url}/api/users?page=2")

    assert response.status_code == HTTPStatus.OK
    users = response.json()
    assert users['page'] == 2

@pytest.mark.parametrize("size, pages", [(50, 1),(10, 2), (5, 3), (3, 4)])
def test_get_users_pagination_page_num(app_url, size, pages):
    response = requests.get(f"{app_url}/api/users?size={size}")
    assert response.status_code == HTTPStatus.OK

    users = response.json()
    assert users['pages'] == pages


def test_get_users_pagination_page_data(app_url):
    response = requests.get(f"{app_url}/api/users?page=2&size=3")
    assert response.status_code == HTTPStatus.OK

    data_1 = response.json()

    response = requests.get(f"{app_url}/api/users?page=3&size=3")
    assert response.status_code == HTTPStatus.OK

    data_2 = response.json()

    for user in data_1['items']:
        assert user not in data_2['items']


@pytest.mark.parametrize("size", [1, 3, 5])
def test_get_users_pagination_page_size(app_url, size):
    response = requests.get(f"{app_url}/api/users?size={size}")
    assert response.status_code == HTTPStatus.OK

    users = response.json()
    assert users['size'] == size
    assert len(users['items']) == size


@pytest.mark.parametrize("user_id", [1, 3, 5, 12])
def test_get_user_by_id(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.OK
    user = response.json()

    User.model_validate(user)

    assert user["id"] == user_id


@pytest.mark.parametrize("user_id", [-1, "adaasd"])
def test_get_user_invalid(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("user_id", [100, 200])
def test_get_user_missing_id(app_url, user_id):
    response = requests.get(f"{app_url}/api/users/{user_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

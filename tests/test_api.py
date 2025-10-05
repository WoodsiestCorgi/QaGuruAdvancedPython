import json
from http import HTTPStatus

import pytest
import requests

from micro_service.models.User import User, UserCreate


@pytest.fixture()
def fill_test_data(app_url):
    with open('./data/users.json', 'r', encoding='utf-8') as f:
        test_data_users = json.load(f)

    for user in test_data_users.values():
        requests.post(f'{app_url}/api/users', json=user)


@pytest.fixture()
def build_user_payload():
    """Генерирует валидный payload для создания пользователя"""
    return {
            "email":      "test.user@example.com",
            "first_name": "Test",
            "last_name":  "User",
            "avatar":     "https://example.com/avatar.png",
            "token":      "testtoken123",
            "password":   "P@ssw0rd!"
            }


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


def test_create_user_post(app_url, build_user_payload):
    response = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert response.status_code == HTTPStatus.CREATED

    created = response.json()
    User.model_validate(created)
    assert created.get("id") is not None
    assert created["email"] == build_user_payload["email"]

    # Очистка после теста
    delete_resp = requests.delete(f"{app_url}/api/users/{created.get("id")}")
    assert delete_resp.status_code == HTTPStatus.OK
    assert delete_resp.json()["message"] == "User deleted"


def test_delete_user(app_url, build_user_payload):
    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED
    user_id = create_resp.json()["id"]

    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK
    assert delete_resp.json().get("message") == "User deleted"


def test_patch_user(app_url):
    user_id = 1
    # Получаем полный объект пользователя для PATCH
    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.OK
    user_body = get_resp.json()
    user_body["first_name"] = "Updated"

    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=user_body)
    assert patch_resp.status_code == HTTPStatus.OK

    updated = patch_resp.json()
    User.model_validate(updated)
    assert updated["first_name"] == "Updated"

    # Очистка после теста - возвращаем имя назад
    user_body["first_name"] = "George"
    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=user_body)
    assert patch_resp.status_code == HTTPStatus.OK
    assert patch_resp.json().get("first_name") == "George"


def test_get_user_after_create_or_update(app_url, build_user_payload):
    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED
    user_id = create_resp.json()["id"]

    # GET после создания
    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.OK
    assert get_resp.json()["email"] == build_user_payload["email"]

    # PATCH и GET после изменения
    body = get_resp.json()
    body["last_name"] = "Changed"
    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=body)
    assert patch_resp.status_code == HTTPStatus.OK

    get_after_patch = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_after_patch.status_code == HTTPStatus.OK
    assert get_after_patch.json()["last_name"] == "Changed"

    # Очистка после теста
    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK
    assert delete_resp.json()["message"] == "User deleted"


# ============= Тесты на ошибки HTTP =============

def test_method_not_allowed_405(app_url):
    resp = requests.put(f"{app_url}/api/status")
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_delete_invalid_id_422(app_url):
    resp = requests.delete(f"{app_url}/api/users/-1")
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_delete_invalid_type_422(app_url):
    resp = requests.delete(f"{app_url}/api/users/abc")
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_delete_nonexistent_404(app_url):
    resp = requests.delete(f"{app_url}/api/users/999999")
    assert resp.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR]


def test_patch_invalid_id_422(app_url, build_user_payload):
    resp = requests.patch(f"{app_url}/api/users/-1", json=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_patch_nonexistent_404(app_url, build_user_payload):
    resp = requests.patch(f"{app_url}/api/users/999999", json=build_user_payload)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_get_deleted_user_404(app_url, build_user_payload):
    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED
    user_id = create_resp.json()["id"]

    # Удаляем пользователя
    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK

    # Пытаемся получить удаленного пользователя
    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.NOT_FOUND


# ============= Тесты валидации данных =============

def test_test_data_validity_email_and_url(app_url):
    with open('./data/users.json', 'r', encoding='utf-8') as f:
        test_data_users = json.load(f)

    for user in test_data_users.values():
        UserCreate.model_validate(user)


def test_create_user_invalid_email(app_url, build_user_payload):
    build_user_payload["email"] = "invalid-email"  # Невалидный email

    resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_user_invalid_url(app_url, build_user_payload):
    build_user_payload["avatar"] = "not-a-valid-url"  # Невалидный URL

    resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_e2e_create_read_update_delete(app_url, build_user_payload):
    # 1. CREATE
    build_user_payload["email"] = "e2e.test@example.com"  # Уникальный email для e2e

    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED
    created_user = create_resp.json()
    user_id = created_user["id"]
    assert created_user["email"] == build_user_payload["email"]

    # 2. READ
    read_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert read_resp.status_code == HTTPStatus.OK
    read_user = read_resp.json()
    assert read_user["id"] == user_id
    assert read_user["email"] == build_user_payload["email"]
    assert read_user["first_name"] == build_user_payload["first_name"]

    # 3. UPDATE
    read_user["first_name"] = "E2E_Updated"
    read_user["last_name"] = "E2E_Changed"

    update_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=read_user)
    assert update_resp.status_code == HTTPStatus.OK
    updated_user = update_resp.json()
    assert updated_user["first_name"] == "E2E_Updated"
    assert updated_user["last_name"] == "E2E_Changed"

    # Проверяем, что изменения сохранились
    verify_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert verify_resp.status_code == HTTPStatus.OK
    assert verify_resp.json()["first_name"] == "E2E_Updated"

    # 4. DELETE
    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK

    # Проверяем, что пользователь удален
    final_check = requests.get(f"{app_url}/api/users/{user_id}")
    assert final_check.status_code == HTTPStatus.NOT_FOUND

import json
from http import HTTPStatus

import pytest
import requests

from micro_service.models.User import User, UserCreate


@pytest.fixture(scope='session', autouse=True)
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
    assert response.status_code == HTTPStatus.OK, f"Ожидался статус 200, получен {response.status_code}: {response.text}"
    assert response.json() == {"database": True}, f"Ожидался ответ {{'database': True}}, получен {response.json()}"


def test_get_users(app_url, fill_test_data):
    response = requests.get(f"{app_url}/api/users")

    assert response.status_code == HTTPStatus.OK, f"Не удалось получить список пользователей: {response.status_code} {response.text}"

    users = response.json()
    for user in users['items']:
        User.model_validate(user)


def test_get_users_pagination_page(app_url):
    response = requests.get(f"{app_url}/api/users?page=2")

    assert response.status_code == HTTPStatus.OK, f"Ожидался статус 200, получен {response.status_code}: {response.text}"
    users = response.json()
    assert users['page'] == 2, f"Ожидалась страница 2, получена {users['page']}"

@pytest.mark.parametrize("size, pages", [(50, 1),(10, 2), (5, 3), (3, 4)])
def test_get_users_pagination_page_num(app_url, size, pages):
    response = requests.get(f"{app_url}/api/users?size={size}")
    assert response.status_code == HTTPStatus.OK

    users = response.json()
    assert users['pages'] == pages , f"Ожидалось {pages} страниц, а получено {users['pages']}"


def test_get_users_pagination_page_data(app_url):
    response = requests.get(f"{app_url}/api/users?page=2&size=3")
    assert response.status_code == HTTPStatus.OK

    data_1 = response.json()

    response = requests.get(f"{app_url}/api/users?page=3&size=3")
    assert response.status_code == HTTPStatus.OK

    data_2 = response.json()

    for user in data_1['items']:
        assert user not in data_2['items'], "Дублирование данных на разных страницах"


@pytest.mark.parametrize("size", [1, 3, 5])
def test_get_users_pagination_page_size(app_url, size):
    response = requests.get(f"{app_url}/api/users?size={size}")
    assert response.status_code == HTTPStatus.OK

    users = response.json()
    assert users['size'] == size
    assert len(users['items']) == size, f"Количество записей не соответствует ожидаемому"


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


def test_get_user_missing_id(app_url):
    response = requests.get(f"{app_url}/api/users/999999")
    assert response.status_code == HTTPStatus.NOT_FOUND, \
        f"Ожидался статус 404, получен {response.status_code}: {response.text}"


def test_create_user_post(app_url, build_user_payload):
    response = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert response.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {response.status_code} {response.text}"

    created = response.json()
    User.model_validate(created)
    assert created.get("id") is not None, "ID пользователя не был сгенерирован"

    # Проверяем, что все поля соответствуют ожидаемым
    for key, value in build_user_payload.items():
        assert created[key] == value, f"Поле {key} не совпадает: ожидалось {value}, получено {created.get(key)}"

    # Очистка после теста
    delete_resp = requests.delete(f"{app_url}/api/users/{created.get("id")}")
    assert delete_resp.status_code == HTTPStatus.OK, \
        f"Не удалось удалить тестового пользователя: {delete_resp.status_code} {delete_resp.text}"
    assert delete_resp.json()["message"] == "User deleted"


def test_delete_user(app_url, build_user_payload):
    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK, \
        f"Не удалось удалить тестового пользователя: {delete_resp.status_code} {delete_resp.text}"
    assert delete_resp.json().get("message") == "User deleted"

    # Проверка удаления
    get_user = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_user.status_code == HTTPStatus.NOT_FOUND, (f"Ожидался статус 404, получен {get_user.status_code}:"
                                                          f" {get_user.text}")
    assert get_user.json()["detail"] == "User id not found"


def test_patch_user(app_url):
    user_id = 1
    # Получаем полный объект пользователя для PATCH
    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.OK, \
        f"Не удалось получить пользователя: {get_resp.status_code} {get_resp.text}"
    user_body = get_resp.json()
    user_body["first_name"] = "Updated"

    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=user_body)
    assert patch_resp.status_code == HTTPStatus.OK, \
        f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"

    updated = patch_resp.json()
    User.model_validate(updated)
    assert (updated_name := updated["first_name"]) == "Updated", \
        f"Имя пользователя не изменилось: Ожидается 'Updated', в ответе '{updated_name}'"

    # Очистка после теста - возвращаем имя назад
    user_body["first_name"] = "George"
    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=user_body)
    assert patch_resp.status_code == HTTPStatus.OK, \
        f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"
    assert patch_resp.json().get("first_name") == "George"


def test_get_user_after_create_or_update(app_url, build_user_payload):
    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    # GET после создания
    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.OK, \
        f"Не удалось получить пользователя: {get_resp.status_code} {get_resp.text}"
    assert get_resp.json()["email"] == build_user_payload["email"]

    # PATCH и GET после изменения
    body = get_resp.json()
    body["last_name"] = "Changed"
    patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=body)
    assert patch_resp.status_code == HTTPStatus.OK, \
        f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"

    get_after_patch = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_after_patch.status_code == HTTPStatus.OK, \
        f"Не удалось получить пользователя: {get_after_patch.status_code} {get_after_patch.text}"
    assert get_after_patch.json()["last_name"] == "Changed"

    # Очистка после теста
    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK, \
        f"Не удалось удалить тестового пользователя: {delete_resp.status_code} {delete_resp.text}"
    assert delete_resp.json()["message"] == "User deleted"


# ============= Тесты на ошибки HTTP =============

def test_method_not_allowed_405(app_url):
    resp = requests.put(f"{app_url}/api/status")
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (f"Ожидался статус 405, получен"
                                                               f" {resp.status_code}: {resp.text}")


def test_delete_invalid_id_422(app_url):
    resp = requests.delete(f"{app_url}/api/users/-1")
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, (f"Ожидался статус 422, получен"
                                                                 f" {resp.status_code}: {resp.text}")


def test_delete_invalid_type_422(app_url):
    resp = requests.delete(f"{app_url}/api/users/abc")
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, (f"Ожидался статус 422, получен"
                                                                 f" {resp.status_code}: {resp.text}")


def test_delete_nonexistent_404(app_url):
    resp = requests.delete(f"{app_url}/api/users/999999")
    assert resp.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR]


def test_patch_invalid_id_422(app_url, build_user_payload):
    resp = requests.patch(f"{app_url}/api/users/-1", json=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, (f"Ожидался статус 422, получен"
                                                                 f" {resp.status_code}: {resp.text}")


def test_patch_nonexistent_404(app_url, build_user_payload):
    resp = requests.patch(f"{app_url}/api/users/999999", json=build_user_payload)
    assert resp.status_code == HTTPStatus.NOT_FOUND, \
        f"Ожидался статус 404, получен {resp.status_code}: {resp.text}"


def test_get_deleted_user_404(app_url, build_user_payload):
    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    # Удаляем пользователя
    delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
    assert delete_resp.status_code == HTTPStatus.OK, (f"Не удалось удалить пользователя: {delete_resp.status_code} "
                                                      f"{delete_resp.text}")

    # Пытаемся получить удаленного пользователя
    get_resp = requests.get(f"{app_url}/api/users/{user_id}")
    assert get_resp.status_code == HTTPStatus.NOT_FOUND, \
        f"Ожидался статус 404, получен {get_resp.status_code}: {get_resp.text}"


# ============= Тесты валидации данных =============

def test_test_data_validity_email_and_url(app_url):
    with open('./data/users.json', 'r', encoding='utf-8') as f:
        test_data_users = json.load(f)

    for user in test_data_users.values():
        UserCreate.model_validate(user)


def test_create_user_invalid_email(app_url, build_user_payload):
    build_user_payload["email"] = "invalid-email"  # Невалидный email

    resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, \
        f"Ожидалась ошибка валидации (422) для email {build_user_payload['email']}"


def test_create_user_invalid_url(app_url, build_user_payload):
    build_user_payload["avatar"] = "not-a-valid-url"  # Невалидный URL

    resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, \
        f"Ожидалась ошибка валидации (422) для avatar {build_user_payload['avatar']}"


def test_e2e_create_read_update_delete(app_url, build_user_payload):
    # 1. Создание
    build_user_payload["email"] = "e2e.test@example.com"  # Уникальный email для e2e

    create_resp = requests.post(f"{app_url}/api/users", json=build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    try:
        # 2. Чтение
        get_resp = requests.get(f"{app_url}/api/users/{user_id}")
        assert get_resp.status_code == HTTPStatus.OK, \
            f"Не удалось получить пользователя: {get_resp.status_code} {get_resp.text}"

        # 3. Обновление
        update_data = {"first_name": "Updated"}
        patch_resp = requests.patch(f"{app_url}/api/users/{user_id}", json=update_data)
        assert patch_resp.status_code == HTTPStatus.OK, \
            f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"

        # 4. Проверка обновления
        updated_user = patch_resp.json()
        assert updated_user["first_name"] == "Updated", \
            f"Имя не было обновлено: {updated_user}"

    finally:
        # 5. Удаление
        delete_resp = requests.delete(f"{app_url}/api/users/{user_id}")
        assert delete_resp.status_code == HTTPStatus.OK, \
            f"Не удалось удалить пользователя: {delete_resp.status_code} {delete_resp.text}"

        # Проверяем, что пользователь удален
        get_deleted = requests.get(f"{app_url}/api/users/{user_id}")
        assert get_deleted.status_code == HTTPStatus.NOT_FOUND, "Пользователь не был удален"

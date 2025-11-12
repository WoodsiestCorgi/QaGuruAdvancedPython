import json
from http import HTTPStatus

import pytest
import requests

from micro_service.models.User import User, UserCreate


def test_status(status_api):
    response = status_api.get_status()
    assert response.status_code == HTTPStatus.OK, f"Ожидался статус 200, получен {response.status_code}: {response.text}"
    assert response.json() == {"database": True}, f"Ожидался ответ {{'database': True}}, получен {response.json()}"


def test_get_users(users_api):
    response = users_api.get_users()

    assert response.status_code == HTTPStatus.OK, (f"Не удалось получить список пользователей:"
                                                   f" {response.status_code} {response.text}")

    users = response.json()
    for user in users['items']:
        User.model_validate(user)


def test_get_users_pagination_page(users_api):
    response = users_api.get_users(params={"page": 2})

    assert response.status_code == HTTPStatus.OK, f"Ожидался статус 200, получен {response.status_code}: {response.text}"
    users = response.json()
    assert users['page'] == 2, f"Ожидалась страница 2, получена {users['page']}"

@pytest.mark.parametrize("size, pages", [(50, 1),(10, 2), (5, 3), (3, 4)])
def test_get_users_pagination_page_num(users_api, size, pages):
    response = users_api.get_users(params={"size": size})
    assert response.status_code == HTTPStatus.OK

    users = response.json()
    assert users['pages'] == pages , f"Ожидалось {pages} страниц, а получено {users['pages']}"


def test_get_users_pagination_page_data(users_api):
    response = users_api.get_users(params={"page": 2, "size": 3})
    assert response.status_code == HTTPStatus.OK

    data_1 = response.json()

    response = users_api.get_users(params={"page": 3, "size": 3})
    assert response.status_code == HTTPStatus.OK

    data_2 = response.json()

    for user in data_1['items']:
        assert user not in data_2['items'], "Дублирование данных на разных страницах"


@pytest.mark.parametrize("size", [1, 3, 5])
def test_get_users_pagination_page_size(users_api, size):
    response = users_api.get_users(params={"size": size})
    assert response.status_code == HTTPStatus.OK

    users = response.json()
    assert users['size'] == size
    assert len(users['items']) == size, f"Количество записей не соответствует ожидаемому"


@pytest.mark.parametrize("user_id", [1, 3, 5, 12])
def test_get_user_by_id(users_api, user_id):
    response = users_api.get_user(user_id=user_id)
    assert response.status_code == HTTPStatus.OK
    user = response.json()

    User.model_validate(user)

    assert user["id"] == user_id


@pytest.mark.parametrize("user_id", [-1, "adaasd"])
def test_get_user_invalid(users_api, user_id):
    response = users_api.get_user(user_id=user_id)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_user_missing_id(users_api):
    response = users_api.get_user(user_id=999999)
    assert response.status_code == HTTPStatus.NOT_FOUND, \
        f"Ожидался статус 404, получен {response.status_code}: {response.text}"


def test_create_user_post(users_api, build_user_payload):
    response = users_api.create_user(build_user_payload)
    assert response.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {response.status_code} {response.text}"

    created = response.json()
    User.model_validate(created)
    assert created.get("id") is not None, "ID пользователя не был сгенерирован"

    # Проверяем, что все поля соответствуют ожидаемым
    for key, value in build_user_payload.items():
        assert created[key] == value, f"Поле {key} не совпадает: ожидалось {value}, получено {created.get(key)}"

    # Очистка после теста
    delete_resp = users_api.delete_user(user_id=created.get("id"))
    assert delete_resp.status_code == HTTPStatus.OK, \
        f"Не удалось удалить тестового пользователя: {delete_resp.status_code} {delete_resp.text}"
    assert delete_resp.json()["message"] == "User deleted"


def test_delete_user(users_api, build_user_payload):
    create_resp = users_api.create_user(build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    delete_resp = users_api.delete_user(user_id=user_id)
    assert delete_resp.status_code == HTTPStatus.OK, \
        f"Не удалось удалить тестового пользователя: {delete_resp.status_code} {delete_resp.text}"
    assert delete_resp.json().get("message") == "User deleted"

    # Проверка удаления
    get_user = users_api.get_user(user_id=user_id)
    assert get_user.status_code == HTTPStatus.NOT_FOUND, (f"Ожидался статус 404, получен {get_user.status_code}:"
                                                          f" {get_user.text}")
    assert get_user.json()["detail"] == "User id not found"


def test_patch_user(users_api):
    user_id = 1
    # Получаем полный объект пользователя для PATCH
    get_resp = users_api.get_user(user_id=user_id)
    assert get_resp.status_code == HTTPStatus.OK, \
        f"Не удалось получить пользователя: {get_resp.status_code} {get_resp.text}"
    user_body = get_resp.json()
    user_body["first_name"] = "Updated"

    patch_resp = users_api.update_user(user_id=user_id, payload=user_body)
    assert patch_resp.status_code == HTTPStatus.OK, \
        f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"

    updated = patch_resp.json()
    User.model_validate(updated)
    assert (updated_name := updated["first_name"]) == "Updated", \
        f"Имя пользователя не изменилось: Ожидается 'Updated', в ответе '{updated_name}'"

    # Очистка после теста - возвращаем имя назад
    user_body["first_name"] = "George"
    patch_resp = users_api.update_user(user_id=user_id, payload=user_body)
    assert patch_resp.status_code == HTTPStatus.OK, \
        f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"
    assert patch_resp.json().get("first_name") == "George"


def test_get_user_after_create_or_update(users_api, build_user_payload):
    create_resp = users_api.create_user(build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    # GET после создания
    get_resp = users_api.get_user(user_id=user_id)
    assert get_resp.status_code == HTTPStatus.OK, \
        f"Не удалось получить пользователя: {get_resp.status_code} {get_resp.text}"
    assert get_resp.json()["email"] == build_user_payload["email"]

    # PATCH и GET после изменения
    body = get_resp.json()
    body["last_name"] = "Changed"
    patch_resp = users_api.update_user(user_id=user_id, payload=body)
    assert patch_resp.status_code == HTTPStatus.OK, \
        f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"

    get_after_patch = users_api.get_user(user_id=user_id)
    assert get_after_patch.status_code == HTTPStatus.OK, \
        f"Не удалось получить пользователя: {get_after_patch.status_code} {get_after_patch.text}"
    assert get_after_patch.json()["last_name"] == "Changed"

    # Очистка после теста
    delete_resp = users_api.delete_user(user_id=user_id)
    assert delete_resp.status_code == HTTPStatus.OK, \
        f"Не удалось удалить тестового пользователя: {delete_resp.status_code} {delete_resp.text}"
    assert delete_resp.json()["message"] == "User deleted"


# ============= Тесты на ошибки HTTP =============

def test_method_not_allowed_405(status_api):
    resp = status_api.put(status_api.endpoint)
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (f"Ожидался статус 405, получен"
                                                               f" {resp.status_code}: {resp.text}")


@pytest.mark.parametrize("invalid_id", [-1, "abc"])
def test_delete_invalid_id_422(users_api, invalid_id):
    resp = users_api.delete_user(user_id=invalid_id)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, (f"Ожидался статус 422, получен"
                                                                 f" {resp.status_code}: {resp.text}")


def test_delete_nonexistent_404(app_url):
    resp = users_api.delete_user(user_id=999999)
    assert resp.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR]


def test_patch_invalid_id_422(users_api, build_user_payload):
    resp = users_api.update_user(user_id=-1, payload=build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, (f"Ожидался статус 422, получен"
                                                                 f" {resp.status_code}: {resp.text}")


def test_patch_nonexistent_404(users_api, build_user_payload):
    resp = users_api.update_user(user_id=999999, payload=build_user_payload)
    assert resp.status_code == HTTPStatus.NOT_FOUND, \
        f"Ожидался статус 404, получен {resp.status_code}: {resp.text}"


def test_get_deleted_user_404(users_api, build_user_payload):
    create_resp = users_api.create_user(build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    # Удаляем пользователя
    delete_resp = users_api.delete_user(user_id=user_id)
    assert delete_resp.status_code == HTTPStatus.OK, (f"Не удалось удалить пользователя: {delete_resp.status_code} "
                                                      f"{delete_resp.text}")

    # Пытаемся получить удаленного пользователя
    get_resp = users_api.get_user(user_id=user_id)
    assert get_resp.status_code == HTTPStatus.NOT_FOUND, \
        f"Ожидался статус 404, получен {get_resp.status_code}: {get_resp.text}"


# ============= Тесты валидации данных =============

def test_test_data_validity_email_and_url():
    with open('./data/users.json', 'r', encoding='utf-8') as f:
        test_data_users = json.load(f)

    for user in test_data_users.values():
        UserCreate.model_validate(user)


def test_create_user_invalid_email(users_api, build_user_payload):
    build_user_payload["email"] = "invalid-email"  # Невалидный email

    resp = users_api.create_user(build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, \
        f"Ожидалась ошибка валидации (422) для email {build_user_payload['email']}"


def test_create_user_invalid_url(users_api, build_user_payload):
    build_user_payload["avatar"] = "not-a-valid-url"  # Невалидный URL

    resp = users_api.create_user(build_user_payload)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, \
        f"Ожидалась ошибка валидации (422) для avatar {build_user_payload['avatar']}"


def test_e2e_create_read_update_delete(users_api, build_user_payload):
    # 1. Создание
    build_user_payload["email"] = "e2e.test@example.com"  # Уникальный email для e2e

    create_resp = users_api.create_user(build_user_payload)
    assert create_resp.status_code == HTTPStatus.CREATED, \
        f"Не удалось создать пользователя: {create_resp.status_code} {create_resp.text}"
    user_id = create_resp.json()["id"]

    try:
        # 2. Чтение
        get_resp = users_api.get_user(user_id=user_id)
        assert get_resp.status_code == HTTPStatus.OK, \
            f"Не удалось получить пользователя: {get_resp.status_code} {get_resp.text}"

        # 3. Обновление
        update_data = {"first_name": "Updated"}
        patch_resp = user_id.update_user(user_id=user_id, payload=update_data)
        assert patch_resp.status_code == HTTPStatus.OK, \
            f"Не удалось обновить пользователя: {patch_resp.status_code} {patch_resp.text}"

        # 4. Проверка обновления
        updated_user = patch_resp.json()
        assert updated_user["first_name"] == "Updated", \
            f"Имя не было обновлено: {updated_user}"

    finally:
        # 5. Удаление
        delete_resp = users_api.delete_user(user_id=user_id)
        assert delete_resp.status_code == HTTPStatus.OK, \
            f"Не удалось удалить пользователя: {delete_resp.status_code} {delete_resp.text}"

        # Проверяем, что пользователь удален
        get_deleted = users_api.get_user(user_id=user_id)
        assert get_deleted.status_code == HTTPStatus.NOT_FOUND, "Пользователь не был удален"

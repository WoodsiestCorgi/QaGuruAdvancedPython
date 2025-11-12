import json

import pytest


@pytest.fixture(scope='session', autouse=True)
def fill_test_data(users_api):
    with open('./data/users.json', 'r', encoding='utf-8') as f:
        test_data_users = json.load(f)

    for user in test_data_users.values():
        users_api.create_user(user)


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

from micro_service.data.data_for_app import USER_ID_URL, USERS_URL
from tests.api.base_session import BaseSession


class UsersApi(BaseSession):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_users(self, **kwargs):
        return self.get(USERS_URL, **kwargs)

    def get_user(self, user_id, **kwargs):
        return self.get(USER_ID_URL.format(user_id=user_id), **kwargs)

    def create_user(self, payload: dict, **kwargs):
        return self.post(USERS_URL, json=payload, **kwargs)

    def update_user(self, user_id, payload: dict, **kwargs):
        return self.patch(USER_ID_URL.format(user_id=user_id), json=payload, **kwargs)

    def delete_user(self, user_id, **kwargs):
        return self.delete(USER_ID_URL.format(user_id=user_id), **kwargs)

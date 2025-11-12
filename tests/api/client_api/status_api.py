from micro_service.data.data_for_app import STATUS_URL
from tests.api.base_session import BaseSession


class StatusApi(BaseSession):
    def __init__(self, **kwargs):
        self.endpoint = STATUS_URL
        super().__init__(**kwargs)

    def get_status(self):
        return self.get(self.endpoint)
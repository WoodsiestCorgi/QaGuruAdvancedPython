from requests import Session


class BaseSession(Session):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.base_url = kwargs.pop("base_url", None)
        if self.base_url is None:
            raise ValueError("base_url is required")

    def request(self, method, url, *args, **kwargs):
        return super().request(method, self.base_url + url, *args, **kwargs)

from requests import Session


class BaseSession(Session):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.base_url = kwargs.pop("base_url", None)
        if self.base_url is None:
            raise ValueError("base_url is required")

    def post(self, url, *args, **kwargs):
        url = self.base_url + url
        return super().post(url, *args, **kwargs)

    def get(self, url, *args, **kwargs):
        url = self.base_url + url
        return super().get(url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        url = self.base_url + url
        return super().put(url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        url = self.base_url + url
        return super().delete(url, *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        url = self.base_url + url
        return super().patch(url, *args, **kwargs)

    def request(self, method, url, *args, **kwargs):
        url = self.base_url + url
        return super().request(method, url, *args, **kwargs)

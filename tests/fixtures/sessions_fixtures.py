import pytest

from tests.api.client_api.status_api import StatusApi
from tests.api.client_api.users_api import UsersApi
from tests.api.config import Server


@pytest.fixture(scope="session")
def base_url(env, app_url):
    return app_url or Server(env).base_url


@pytest.fixture(scope="session")
def users_api(base_url):
    with UsersApi(base_url=base_url) as session:
        yield session


@pytest.fixture(scope="session")
def status_api(base_url):
    with StatusApi(base_url=base_url) as session:
        yield session

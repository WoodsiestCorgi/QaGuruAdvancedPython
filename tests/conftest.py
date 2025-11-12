import os

import dotenv
import pytest

pytest_plugins = ["tests.fixtures.sessions_fixtures", "tests.fixtures.data_fixtures"]

@pytest.fixture(scope="session", autouse=True)
def envs():
    dotenv.load_dotenv()


@pytest.fixture(scope="session")
def env(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def app_url():
    url = os.getenv("APP_URL")
    return url


def pytest_addoption(parser):
    parser.addoption("--env", default="test", help="Environment for tests")

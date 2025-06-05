import os

import dotenv
import pytest


@pytest.fixture(scope="session", autouse=True)
def envs():
    dotenv.load_dotenv()


@pytest.fixture(scope="session")
def app_url():
    url = os.getenv("APP_URL")
    return url

from app import create_app
from db_models import Users

import pytest

@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client


"""
Users for testing
"""
@pytest.fixture(scope='module')
def fake_user():
    user = Users()
    user.setup("BobPhil123", "weakpassword", "Bob Phil", "bobphil@gmail.com")
    return user

@pytest.fixture(scope='module')
def fake_user2():
    user = Users()
    user.setup("robby", "weakpassword", "robby", "robby@gmail.com")
    return user

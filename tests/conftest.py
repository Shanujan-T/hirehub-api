import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    def _login(email, password):
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        token = response.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login


@pytest.fixture()
def employer_user(app):
    user = User(
        email="employer@example.com",
        full_name="Test Employer",
        role="employer",
    )
    user.set_password("secret123")
    db.session.add(user)
    db.session.commit()
    return user

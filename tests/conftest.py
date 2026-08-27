import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "super-secret-test-key-with-at-least-32-characters-long",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Testler için standart bir kullanıcı kaydeder ve yetkilendirme başlığını döner."""
    client.post('/auth/register', json={"username": "testuser", "password": "password123"})
    response = client.post('/auth/login', json={"username": "testuser", "password": "password123"})
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

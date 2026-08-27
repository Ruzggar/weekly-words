def test_register_success(client):
    response = client.post('/auth/register', json={"username": "newuser", "password": "123"})
    assert response.status_code == 201


def test_register_duplicate(client):
    client.post('/auth/register', json={"username": "newuser", "password": "123"})
    response = client.post('/auth/register', json={"username": "newuser", "password": "123"})
    assert response.status_code == 400


def test_login_success(client):
    client.post('/auth/register', json={"username": "logintest", "password": "123"})
    response = client.post('/auth/login', json={"username": "logintest", "password": "123"})
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_wrong_password(client):
    client.post('/auth/register', json={"username": "logintest", "password": "123"})
    response = client.post('/auth/login', json={"username": "logintest", "password": "wrong"})
    assert response.status_code == 401


def test_protected_route(client, auth_headers):
    response = client.get('/auth/protected', headers=auth_headers)
    assert response.status_code == 200


def test_change_username(client, auth_headers):
    response = client.put('/auth/change-username', json={"new_username": "updated_user"}, headers=auth_headers)
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_change_password(client, auth_headers):
    response = client.put('/auth/change-password',
                          json={"old_password": "password123", "new_password": "newpass"},
                          headers=auth_headers)
    assert response.status_code == 200


def test_logout(client, auth_headers):
    response = client.delete('/auth/logout', headers=auth_headers)
    assert response.status_code == 200

    # Token blocklist'e girdiği için protected route artık 401 dönmeli
    response2 = client.get('/auth/protected', headers=auth_headers)
    assert response2.status_code == 401


def test_logout_all(client, auth_headers):
    response = client.delete('/auth/logout-all', headers=auth_headers)
    assert response.status_code == 200

    # Tüm cihazlardan çıkış yapıldığı için eski token geçersiz olmalı
    response2 = client.get('/auth/protected', headers=auth_headers)
    assert response2.status_code == 401


def test_delete_account(client, auth_headers):
    response = client.delete('/auth/account', headers=auth_headers)
    assert response.status_code == 200

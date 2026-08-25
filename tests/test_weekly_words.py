def test_add_weekly_words(client, auth_headers):
    data = {
        "learning_language": "en",
        "known_language": "tr",
        "words": [
            {"word": "apple", "meaning": "elma", "type": ["noun"]}
        ]
    }
    response = client.post('/add-weekly-words', json=data, headers=auth_headers)
    assert response.status_code == 201

def test_get_weekly_words_specific_week(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/weekly-words/1', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["words"][0]["word"] == "apple"

def test_get_weekly_words_last_week_with_zero(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/weekly-words/0', headers=auth_headers)
    assert response.status_code == 200

def test_get_last_week_number(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/last-week-number', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["last_week_number"] == 1
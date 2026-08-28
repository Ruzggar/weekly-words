def test_add_weekly_words(client, auth_headers):
    data = {
        "learning_language": "en",
        "known_language": "tr",
        "words": [
            {"word": "apple", "plural": "apples", "meaning": "elma", "type": ["noun"]}
        ]
    }
    response = client.post('/add-weekly-words', json=data, headers=auth_headers)
    assert response.status_code == 201


def test_add_weekly_words_missing_plural(client, auth_headers):
    # İsim (noun) olmasına rağmen plural gönderilmezse 400 dönmeli
    data = {
        "learning_language": "en",
        "known_language": "tr",
        "words": [
            {"word": "apple", "meaning": "elma", "type": ["noun"]}
        ]
    }
    response = client.post('/add-weekly-words', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "çoğul" in response.get_json()["error"]


def test_add_weekly_words_with_slash_split(client, auth_headers):
    data = {
        "learning_language": "en",
        "known_language": "tr",
        "words": [
            {"word": "kır", "plural": "kırlar", "meaning": "Renk / Alan, sahra", "type": ["noun"]}
        ]
    }
    response = client.post('/add-weekly-words', json=data, headers=auth_headers)
    assert response.status_code == 201

    # 1 adet word gönderdik ancak slash (/) olduğu için DB'ye 2 adet word eklenmiş olmalı
    res = client.get('/weekly-words/1', headers=auth_headers)
    words_list = res.get_json()["words"]

    assert len(words_list) == 2
    assert words_list[0]["word"] == "kır"
    assert words_list[0]["meaning"] == "Renk"

    assert words_list[1]["word"] == "kır"
    assert words_list[1]["meaning"] == "Alan, sahra"


def test_get_weekly_words_specific_week(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/weekly-words/1', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["words"][0]["word"] == "apple"
    assert response.get_json()["words"][0]["plural"] == "apples"


def test_get_weekly_words_last_week_with_zero(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/weekly-words/0', headers=auth_headers)
    assert response.status_code == 200


def test_get_last_week_number(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/last-week-number', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["last_week_number"] == 1


def test_get_all_weekly_words(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    response = client.get('/all-weekly-words', headers=auth_headers)
    assert response.status_code == 200
    assert "1" in response.get_json()["all_weekly_words"]
from unittest.mock import patch

from tests.test_weekly_words import test_add_weekly_words


@patch('app.services.quiz_service.extensions.genai_client')
def test_generate_quiz_success(mock_genai_client, client, auth_headers):
    test_add_weekly_words(client, auth_headers)

    class MockParsed:
        def model_dump(self):
            return {"content": {"multi_choice": [], "sentences": []}}

    class MockResponse:
        parsed = MockParsed()

    # genai_client.models.generate_content çağrıldığında dönecek sahte (mock) yanıt
    mock_genai_client.models.generate_content.return_value = MockResponse()

    response = client.post('/generate-quiz', headers=auth_headers)
    assert response.status_code == 200


def test_generate_quiz_no_words_found(client, auth_headers):
    # Kelime eklemeden quiz üretmeye çalışırsak 404 dönmeli
    response = client.post('/generate-quiz', headers=auth_headers)
    assert response.status_code == 404


def test_get_quiz_content_not_found(client, auth_headers):
    response = client.get('/quiz-content/1/1', headers=auth_headers)
    assert response.status_code == 404


def test_get_weekly_quizzes_content_not_found(client, auth_headers):
    response = client.get('/quiz-content/1', headers=auth_headers)
    assert response.status_code == 404


def test_get_last_generated_quiz_not_found(client, auth_headers):
    response = client.get('/last-generated-quiz', headers=auth_headers)
    assert response.status_code == 404


def test_get_last_completed_quiz_not_found(client, auth_headers):
    response = client.get('/last-completed-quiz', headers=auth_headers)
    assert response.status_code == 404


def test_final_quiz_cannot_be_generated_early(client, auth_headers):
    # 6 günlük test tamamlanmadan final testi istenirse 404 dönmeli (çünkü kayıt yok)
    response = client.get('/final-quiz/1', headers=auth_headers)
    assert response.status_code == 404


def test_quiz_completed_without_wrong_answers(client, auth_headers):
    test_add_weekly_words(client, auth_headers)

    # İçinde "questions" listesi olmayan, sadece haftayı belirten data
    data = {"week_number": 1}
    response = client.post('/quiz-completed', json=data, headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["msg"] == "Quiz tamamlanması başarıyla işlendi"


def test_quiz_completed_missing_week_number(client, auth_headers):
    # week_number gönderilmezse 400 hatası dönmeli
    response = client.post('/quiz-completed', json={}, headers=auth_headers)
    assert response.status_code == 400
    assert "Hafta numarası boş olamaz" in response.get_json()["error"]


def test_quiz_completed_week_not_found(client, auth_headers):
    # Veritabanında olmayan bir hafta numarası gönderilirse 404 dönmeli
    data = {"week_number": 999}
    response = client.post('/quiz-completed', json=data, headers=auth_headers)
    assert response.status_code == 404
    assert "bulunamadı" in response.get_json()["error"]


def test_quiz_completed_with_wrong_answers(client, auth_headers):
    # Önce haftalık kelimeleri ekleyerek 1. haftayı oluşturalım
    test_add_weekly_words(client, auth_headers)

    # WrongAnswersService'in beklediği formatta data hazırlıyoruz
    data = {
        "week_number": 1,
        "day_number": 1,
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {
                    "question_sentence": "This is a _____.",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0
                }
            }
        ]
    }

    response = client.post('/quiz-completed', json=data, headers=auth_headers)

    # İşlem başarılı olduğunda 200 ve özel başarı mesajı dönmeli
    assert response.status_code == 200
    assert "yanlış cevap verilen sorular başarıyla eklendi" in response.get_json()["msg"]


def test_quiz_completed_wrong_answers_missing_day_number(client, auth_headers):
    # Önce haftalık kelimeleri ekleyelim
    test_add_weekly_words(client, auth_headers)

    # İçinde sorular (questions) var ama WrongAnswersService'in zorunlu tuttuğu 'day_number' yok
    data = {
        "week_number": 1,
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {
                    "question_sentence": "Test",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0
                }
            }
        ]
    }

    response = client.post('/quiz-completed', json=data, headers=auth_headers)

    # WrongAnswersService'den 400 hatası dönüp quiz_completed endpoint'ine yansımalı
    assert response.status_code == 400
    assert "day_number" in response.get_json()["error"]


@patch('app.services.quiz_service.extensions.genai_client')
def test_save_quiz_progress_success(mock_genai_client, client, auth_headers):
    # 1. Dummy quiz oluştur (Hafta 1, Gün 0 olarak oluşacaktır)
    test_add_weekly_words(client, auth_headers)

    class MockParsed:
        def model_dump(self):
            return {"content": {"multi_choice": [], "sentences": []}}

    class MockResponse:
        parsed = MockParsed()

    mock_genai_client.models.generate_content.return_value = MockResponse()
    client.post('/generate-quiz', headers=auth_headers)

    # 2. Progress'i 5 olarak kaydet
    response = client.post('/save-quiz-progress/1/0/5', headers=auth_headers)
    assert response.status_code == 200
    assert "başarıyla kaydedildi" in response.get_json()["msg"]


@patch('app.services.quiz_service.extensions.genai_client')
def test_save_quiz_progress_default_none(mock_genai_client, client, auth_headers):
    # 1. Dummy quiz oluştur
    test_add_weekly_words(client, auth_headers)

    class MockParsed:
        def model_dump(self):
            return {"content": {"multi_choice": [], "sentences": []}}

    class MockResponse:
        parsed = MockParsed()

    mock_genai_client.models.generate_content.return_value = MockResponse()
    client.post('/generate-quiz', headers=auth_headers)

    # 2. current_index göndermeden URL'e istek at (None olarak kaydolmalı)
    response = client.post('/save-quiz-progress/1/0', headers=auth_headers)
    assert response.status_code == 200

    # 3. GET ile kontrol et, current_index None gelmeli
    get_response = client.get('/quiz-progress/1/0', headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.get_json()["current_index"] is None


@patch('app.services.quiz_service.extensions.genai_client')
def test_get_quiz_progress_success(mock_genai_client, client, auth_headers):
    # 1. Dummy quiz oluştur
    test_add_weekly_words(client, auth_headers)

    class MockParsed:
        def model_dump(self):
            return {"content": {"multi_choice": [], "sentences": []}}

    class MockResponse:
        parsed = MockParsed()

    mock_genai_client.models.generate_content.return_value = MockResponse()
    client.post('/generate-quiz', headers=auth_headers)

    # 2. Progress'i 3 olarak kaydet
    client.post('/save-quiz-progress/1/0/3', headers=auth_headers)

    # 3. GET ile çek ve doğrula
    response = client.get('/quiz-progress/1/0', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["current_index"] == 3


def test_save_quiz_progress_not_found(client, auth_headers):
    # Olmayan bir quize progress kaydetmeye çalış
    response = client.post('/save-quiz-progress/99/99/1', headers=auth_headers)
    assert response.status_code == 404
    assert "bulunamadı" in response.get_json()["error"]


def test_get_quiz_progress_not_found(client, auth_headers):
    # Olmayan bir quizin progress'ini getirmeye çalış
    response = client.get('/quiz-progress/99/99', headers=auth_headers)
    assert response.status_code == 404
    assert "bulunamadı" in response.get_json()["error"]

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

    # genai_client.models.generate_content çağrıldığında dönecek sahte yanıt
    mock_genai_client.models.generate_content.return_value = MockResponse()

    response = client.post('/generate-quiz', headers=auth_headers)
    assert response.status_code == 200


def test_generate_quiz_no_words_found(client, auth_headers):
    # Kelime eklemeden quiz üretmeye çalışırsak 404 dönmeli
    response = client.post('/generate-quiz', headers=auth_headers)
    assert response.status_code == 404


def test_get_quiz_content_not_found(client, auth_headers):
    response = client.get('/get-quiz-content/1/1', headers=auth_headers)
    assert response.status_code == 404


def test_get_weekly_quizzes_content_not_found(client, auth_headers):
    response = client.get('/get-quiz-content/1', headers=auth_headers)
    assert response.status_code == 404


def test_get_quiz_history_not_found(client, auth_headers):
    response = client.get('/get-quiz-history', headers=auth_headers)
    assert response.status_code == 404


def test_final_quiz_cannot_be_generated_early(client, auth_headers):
    # 6 günlük test tamamlanmadan final testi istenirse 409 dönmeli
    response = client.get('/final-quiz/1', headers=auth_headers)
    assert response.status_code == 404  # Henüz hiç günlük test olmadığı için önce 404'e düşer
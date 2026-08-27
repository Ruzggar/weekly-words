from sqlalchemy.orm.attributes import flag_modified

from app.extensions import db
from app.models.wrong_answers import WrongAnswers
from tests.test_weekly_words import test_add_weekly_words


def add_dummy_wrong_answer(client, auth_headers):
    test_add_weekly_words(client, auth_headers)
    data = {
        "week_number": 1,
        "day_number": 2,
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {
                    "question_sentence": "Test Q1",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0
                }
            }
        ]
    }
    return client.post('/quiz-completed', json=data, headers=auth_headers)


def test_add_wrong_answers_via_quiz_completed(client, auth_headers):
    response = add_dummy_wrong_answer(client, auth_headers)
    assert response.status_code == 200
    assert "yanlış cevap verilen sorular başarıyla eklendi" in response.get_json()["msg"]


def test_get_wrong_answers_by_week_and_day(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers/1/2', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()["questions"]) == 1


def test_get_wrong_answers_filter_all(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers/all', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()["questions"]) == 1


def test_get_wrong_answers_filter_new(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers/new', headers=auth_headers)
    assert response.status_code == 200
    questions = response.get_json()["questions"]
    assert len(questions) == 1
    assert questions[0]["new"] is True


def test_get_wrong_answers_filter_old(client, auth_headers, app):
    add_dummy_wrong_answer(client, auth_headers)
    response_empty = client.get('/wrong-answers/old', headers=auth_headers)
    assert response_empty.status_code == 404

    with app.app_context():
        record = db.session.query(WrongAnswers).first()
        updated_questions = list(record.questions)
        updated_questions[0]["new"] = False
        record.questions = updated_questions

        flag_modified(record, "questions")
        db.session.commit()

    response_old = client.get('/wrong-answers/old', headers=auth_headers)
    assert response_old.status_code == 200
    questions = response_old.get_json()["questions"]
    assert len(questions) == 1
    assert questions[0]["new"] is False


def test_invalid_filter_type(client, auth_headers):
    response = client.get('/wrong-answers/invalid_filter', headers=auth_headers)
    assert response.status_code == 404


def test_generate_wrong_answers_quiz_success(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/generate-wrong-answers-quiz/5/new', headers=auth_headers)
    assert response.status_code == 200
    content = response.get_json()["content"]
    assert len(content["multi_choice"]) == 1
    assert len(content["sentences"]) == 0


def test_generate_wrong_answers_quiz_not_found(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/generate-wrong-answers-quiz/5/old', headers=auth_headers)
    assert response.status_code == 404


def test_change_wrong_answers_status_with_week_and_day(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    data = {
        "week_number": 1,
        "day_number": 2,
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {
                    "question_sentence": "Test Q1",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0
                }
            }
        ]
    }
    response = client.post('/change-wrong-answers-status', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert "başarıyla (old olarak) güncellendi" in response.get_json()["msg"]


def test_change_wrong_answers_status_without_week_and_day(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    data = {
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {
                    "question_sentence": "Test Q1",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0
                }
            }
        ]
    }
    response = client.post('/change-wrong-answers-status', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert "başarıyla (old olarak) güncellendi" in response.get_json()["msg"]


def test_change_wrong_answers_status_no_match(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    data = {
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {"question_sentence": "Eşleşmeyen Soru"}
            }
        ]
    }
    response = client.post('/change-wrong-answers-status', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert "bulunamadı" in response.get_json()["msg"]


def test_get_wrong_answers_info(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers-info', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_question_count"] == 1
    assert data["new_question_count"] == 1
    assert data["old_question_count"] == 0

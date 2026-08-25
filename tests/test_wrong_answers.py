from app.extensions import db
from app.models.wrong_answers import WrongAnswers
from sqlalchemy.orm.attributes import flag_modified


def add_dummy_wrong_answer(client, auth_headers):
    """Testler içinde kullanmak için yardımcı fonksiyon"""
    data = {
        "week_number": 1,
        "day_number": 2,
        "questions": [
            {"question_type": "multi_choice", "question_content": "Wrong Q1"}
        ]
    }
    return client.post('/add-wrong-answers', json=data, headers=auth_headers)


def test_add_wrong_answers(client, auth_headers):
    response = add_dummy_wrong_answer(client, auth_headers)
    assert response.status_code == 201


def test_get_wrong_answers_by_week_and_day(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers/1/2', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()["questions"]) == 1


# ================= FILTRE TESTLERI =================

def test_get_wrong_answers_filter_all(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers/all', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()["questions"]) == 1


def test_get_wrong_answers_filter_new(client, auth_headers):
    # Yeni eklenen sorular varsayılan olarak "new": True ile eklenir
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

        # ÇÖZÜM BURADA: SQLAlchemy'yi JSON güncellemesi yapmaya zorluyoruz
        flag_modified(record, "questions")

        db.session.commit()

    response_old = client.get('/wrong-answers/old', headers=auth_headers)
    assert response_old.status_code == 200  # Artık sorunsuz geçecek!
    questions = response_old.get_json()["questions"]
    assert len(questions) == 1
    assert questions[0]["new"] is False


def test_invalid_filter_type(client, auth_headers):
    # any(all, new, old) dışında bir şey gönderilirse Flask doğrudan 404 dönmeli
    response = client.get('/wrong-answers/invalid_filter', headers=auth_headers)
    assert response.status_code == 404
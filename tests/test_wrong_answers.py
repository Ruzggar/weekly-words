from app.extensions import db
from app.models.wrong_answers import WrongAnswers
from sqlalchemy.orm.attributes import flag_modified
from tests.test_weekly_words import test_add_weekly_words


def add_dummy_wrong_answer(client, auth_headers):
    """Testler içinde kullanmak için yardımcı fonksiyon. Yeni mimariye göre uyarlandı."""

    # 1. Önce WeeklyWords oluşturmamız lazım ki quiz_completed 404 dönmesin
    test_add_weekly_words(client, auth_headers)

    # 2. Şimdi quiz-completed endpoint'ine istek atalım.
    # Frontend'den geleceği gibi question_content'i dict (sözlük) olarak ayarladık.
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
    assert response.status_code == 200  # Servis başarılı olunca artık 200 dönüyor
    assert "yanlış cevap verilen sorular başarıyla eklendi" in response.get_json()["msg"]


def test_get_wrong_answers_by_week_and_day(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)
    response = client.get('/wrong-answers/1/2', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()["questions"]) == 1


# ================= FİLTRE TESTLERİ =================

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


# ================= YENİ EKLENEN ENDPOINT TESTLERİ =================

def test_generate_wrong_answers_quiz_success(client, auth_headers):
    # Dummy verimizi ekliyoruz (Varsayılan olarak "new": True ile eklenir)
    add_dummy_wrong_answer(client, auth_headers)

    # İstenen soru sayısı 5 olsa bile veritabanında 1 tane olduğu için çökmeden 1 tane dönmeli
    response = client.get('/generate-wrong-answers-quiz/5/new', headers=auth_headers)
    assert response.status_code == 200

    content = response.get_json()["content"]
    assert len(content["multi_choice"]) == 1
    assert len(content["sentences"]) == 0


def test_generate_wrong_answers_quiz_not_found(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)

    # Bütün sorular "new" olduğu için "old" filtresi ile quiz üretilmek istendiğinde 404 dönmeli
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

    # Güncellendiğini (old'a dönüştüğünü) doğrulamak için "old" filtresini çekelim
    response_old = client.get('/wrong-answers/old', headers=auth_headers)
    assert response_old.status_code == 200
    assert len(response_old.get_json()["questions"]) == 1


def test_change_wrong_answers_status_without_week_and_day(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)

    # Sadece "questions" gönderiyoruz, week_number ve day_number yok. Havuzu tarayıp bulmalı.
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

    # Doğrulama işlemi
    response_old = client.get('/wrong-answers/old', headers=auth_headers)
    assert response_old.status_code == 200
    assert len(response_old.get_json()["questions"]) == 1


def test_change_wrong_answers_status_no_match(client, auth_headers):
    add_dummy_wrong_answer(client, auth_headers)

    # Eşleşmeyen tamamen farklı bir soru gönderelim
    data = {
        "questions": [
            {
                "question_type": "multi_choice",
                "question_content": {"question_sentence": "Eşleşmeyen Soru"}
            }
        ]
    }
    response = client.post('/change-wrong-answers-status', json=data, headers=auth_headers)

    # Sistemin çökmediğinden (200 döndüğünden) ama hiçbir şeyi değiştirmediğinden emin olalım
    assert response.status_code == 200
    assert "bulunamadı" in response.get_json()["msg"]
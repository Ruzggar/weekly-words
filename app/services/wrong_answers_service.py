from app.extensions import db
from app.models.user import User
from app.models.wrong_answers import WrongAnswers

class WrongAnswersService:
    @staticmethod
    def add_wrong_answers(user_id, username, data):
        if not data:
            return {"error": "Request body'si yok"}, 400

        week_number = data.get("week_number")
        day_number = data.get("day_number")
        raw_questions = data.get("questions")

        if not week_number or not day_number:
            return {"error": "JSON içerisinde 'week_number' veya 'day_number' bulunamadı ya da boş"}, 400

        if not raw_questions or not isinstance(raw_questions, list):
            return {"error": "JSON'da 'questions' listesi bulunamadı veya formati hatalı"}, 400

        user_exists = db.session.query(User.id).filter_by(id=user_id).scalar()
        if not user_exists:
            return {"error": f"{username} isimli ve {user_id} id'li bir kullanıcı bulunamadı"}, 404

        processed_questions = []

        for item in raw_questions:
            if not isinstance(item, dict):
                return {"error": "JSON'daki 'questions'ın içindeki elemanlardan en az biri dict değil"}, 400

            question_type = item.get("question_type")
            question_content = item.get("question_content")

            if not question_type or not question_content:
                return {"error": "Sorulardan en az birinin tipi veya içeriği eksik"}, 400

            processed_questions.append({
                "question_type": question_type,
                "question_content": question_content,
                "new": True
            })

        present_wrong_answers = WrongAnswers.query.filter_by(
            user_id=user_id,
            week_number=week_number,
            day_number=day_number
        ).first()

        if present_wrong_answers:
            existing_questions = list(present_wrong_answers.questions)
            existing_questions.extend(processed_questions)
            present_wrong_answers.questions = existing_questions
        else:
            new_wrong_answers = WrongAnswers(
                user_id=user_id,
                questions=processed_questions,
                week_number=week_number,
                day_number=day_number
            )
            db.session.add(new_wrong_answers)

        db.session.commit()

        return {"msg": "Yanlış cevap verilen sorular başarıyla eklendi"}, 201

    @staticmethod
    def get_wrong_answers_by_week_and_day(user_id, username, week_number, day_number):
        wrong_answers = WrongAnswers.query.filter_by(
            user_id=user_id,
            week_number=week_number,
            day_number=day_number
        ).first()

        if wrong_answers:
            # EKLENDİ: Başarı durumunda 200 kodu eksikti.
            return {"questions": wrong_answers.questions}, 200
        else:
            return {
                "error": f"{username} kullanıcısına ait {week_number}. hafta ve {day_number}. güne ait yanlış yapılan sorular bulunamadı"}, 404

    @staticmethod
    def get_wrong_answers_by_filter(user_id, username, filter_type):
        if filter_type not in ["all", "new", "old"]:
            return {"error": "Geçersiz filtre tipi. Sadece 'all', 'new' veya 'old' kullanılabilir."}, 400

        all_wrong_answers = WrongAnswers.query.filter_by(
            user_id=user_id,
        ).all()

        if not all_wrong_answers:
            return {"msg": f"{username} kullanıcısına ait herhangi bir yanlış cevap kaydı bulunamadı",
                    "questions": []}, 404

        filtered_questions = []

        for record in all_wrong_answers:
            week = record.week_number
            day = record.day_number

            for question in record.questions:
                is_new = question.get("new", False)

                q_copy = question.copy()
                q_copy["week_number"] = week
                q_copy["day_number"] = day

                if filter_type == "all":
                    filtered_questions.append(q_copy)
                elif filter_type == "new" and is_new:
                    filtered_questions.append(q_copy)
                elif filter_type == "old" and not is_new:
                    filtered_questions.append(q_copy)

        if not filtered_questions:
            return {"msg": f"Seçilen filtreye ({filter_type}) uygun soru bulunamadı", "questions": []}, 404

        return {"questions": filtered_questions}, 200
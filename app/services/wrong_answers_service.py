import random

from sqlalchemy.orm.attributes import flag_modified

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

        present_wrong_answers = db.session.query(WrongAnswers).filter_by(
            user_id=user_id,
            week_number=week_number,
            day_number=day_number
        ).first()

        if present_wrong_answers:
            existing_questions = list(present_wrong_answers.questions)
            existing_questions.extend(processed_questions)
            present_wrong_answers.questions = existing_questions

            flag_modified(present_wrong_answers, "questions")
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
        wrong_answers = db.session.query(WrongAnswers).filter_by(
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

        all_wrong_answers = db.session.query(WrongAnswers).filter_by(
            user_id=user_id,
        ).all()

        if not all_wrong_answers:
            return {"error": f"{username} kullanıcısına ait herhangi bir yanlış cevap kaydı bulunamadı",
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
            return {"error": f"Seçilen filtreye ({filter_type}) uygun soru bulunamadı", "questions": []}, 404

        return {"questions": filtered_questions}, 200

    @staticmethod
    def generate_wrong_answers_quiz(user_id, username, question_count, filter_type):
        if filter_type not in ["all", "new", "old"]:
            return {"error": "Geçersiz filtre tipi. Sadece 'all', 'new' veya 'old' kullanılabilir."}, 400

        all_wrong_answers = db.session.query(WrongAnswers).filter_by(user_id=user_id).all()

        if not all_wrong_answers:
            return {"error": f"{username} kullanıcısına ait herhangi bir yanlış cevap kaydı bulunamadı"}, 404

        filtered_questions = []

        # 1. Filtreye uyan tüm soruları düz bir liste (havuz) haline getirme
        for record in all_wrong_answers:
            for question in record.questions:
                is_new = question.get("new", False)

                if filter_type == "all":
                    filtered_questions.append(question)
                elif filter_type == "new" and is_new:
                    filtered_questions.append(question)
                elif filter_type == "old" and not is_new:
                    filtered_questions.append(question)

        if not filtered_questions:
            return {"error": f"Seçilen filtreye ({filter_type}) uygun soru bulunamadı"}, 404

        # 2. Havuzdan rastgele soru seçme (Eğer havuzdaki soru sayısı istenenden azsa, olanların tamamını alır)
        sample_size = min(question_count, len(filtered_questions))
        selected_questions = random.sample(filtered_questions, sample_size)

        # 3. Seçilen soruları TestScheme / QuizContent (Yapay Zeka) formatına dönüştürme
        quiz_content = {"multi_choice": [], "sentences": []}

        for q in selected_questions:
            q_type = q.get("question_type")
            q_content = q.get("question_content")

            if q_type == "multi_choice":
                quiz_content["multi_choice"].append(q_content)
            elif q_type == "sentence":
                quiz_content["sentences"].append(q_content)

        return {"content": quiz_content}, 200

    @staticmethod
    def change_wrong_answers_status(user_id, username, data):
        if not data:
            return {"error": "Request body'si yok"}, 400

        questions_to_change = data.get("questions")
        if not questions_to_change or not isinstance(questions_to_change, list):
            return {"error": "JSON'da 'questions' listesi bulunamadı veya formatı hatalı"}, 400

        week_number = data.get("week_number")
        day_number = data.get("day_number")

        records_to_process = []

        # 1. Durum: week ve day verilmişse sadece o spesifik kaydı bul
        if week_number is not None and day_number is not None:
            record = db.session.query(WrongAnswers).filter_by(
                user_id=user_id, week_number=week_number, day_number=day_number
            ).first()
            if record:
                records_to_process.append(record)
        # 2. Durum: week ve day yoksa kullanıcının tüm kayıtlarını taramak üzere listeye ekle
        else:
            records = db.session.query(WrongAnswers).filter_by(user_id=user_id).all()
            records_to_process.extend(records)

        if not records_to_process:
            return {"error": "Değişiklik yapılacak hedef yanlış cevap kaydı bulunamadı"}, 404

        changed_any = False

        # 3. Kayıtları ve soruları tarama optimizasyonu
        for record in records_to_process:
            record_changed = False
            updated_questions = list(record.questions)

            # OPTİMİZASYON 1: Döngülerin sırasını değiştirdik. Önce DB'deki soruları dönüyoruz.
            for db_q in updated_questions:

                # OPTİMİZASYON 2: Eğer soru zaten "new": False ise, hedef listeyle hiç kıyaslama (Hızlı Eleme)
                if db_q.get("new", False) is False:
                    continue

                for target_q in questions_to_change:
                    # Soru tipi ve içeriği birebir eşleşiyorsa
                    if (db_q.get("question_type") == target_q.get("question_type") and
                            db_q.get("question_content") == target_q.get("question_content")):
                        db_q["new"] = False
                        record_changed = True
                        changed_any = True

                        # OPTİMİZASYON 3: Eşleşme bulundu ve soru "old" yapıldı.
                        # Bu soru için diğer hedeflere bakmaya gerek yok, döngüyü kırıp sıradaki DB sorusuna geçiyoruz.
                        break

                        # Eğer bu kaydın içindeki herhangi bir soruda değişiklik yapıldıysa JSON verisini güncelle
            if record_changed:
                record.questions = updated_questions
                flag_modified(record, "questions")

        # 4. En az 1 soruda değişiklik olduysa veritabanına kaydet
        if changed_any:
            db.session.commit()
            return {"msg": "Belirtilen soruların statüsü başarıyla (old olarak) güncellendi"}, 200
        else:
            return {"msg": "Değiştirilecek veya eşleşen 'new' statüsünde soru bulunamadı"}, 200

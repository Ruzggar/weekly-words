from app.extensions import db
from app.models.quiz import Quiz
from app.models.weekly_words import WeeklyWords


class WeeklyWordsService:
    @staticmethod
    def add_weekly_words(username, user_id, data):
        words = data.get('words')
        learning_language = data.get('learning_language')
        known_language = data.get('known_language')

        if not username or not user_id:
            return {"error": "Kullanıcı adı veya ID boş olamaz"}, 400

        last_week = db.session.query(WeeklyWords).filter_by(user_id=user_id).order_by(
            WeeklyWords.week_number.desc()).first()

        if last_week and db.session.query(Quiz).filter_by(
                user_id=user_id, week_number=last_week.week_number).count() == 7:
            last_week.completed = True

        if last_week and not last_week.completed:
            return {"error": "Bir hafta tamamlanmamışken yenisine geçilemez"}, 409

        new_week_number = last_week.week_number + 1 if last_week else 1

        if not words:
            return {"error": "Kelimeler boş olamaz"}, 400

        if not isinstance(words, list) or not isinstance(learning_language, str) or not isinstance(known_language, str):
            return {"error": "Kelimeler liste, diller string olmalıdır"}, 400

        learning_language = learning_language.strip().lower()
        known_language = known_language.strip().lower()
        if learning_language not in ["tr", "en", "de", "el"] or known_language not in ["tr", "en", "de", "el"]:
            return {"error": "Desteklenen diller: tr, en, de, el"}, 400

        processed_words = []

        for word_dict in words:
            if not isinstance(word_dict, dict):
                return {"error": "Her bir kelime verisi sözlük yapısında olmalıdır"}, 400

            w_word = word_dict.get("word")
            w_meaning = word_dict.get("meaning")
            w_type = word_dict.get("type")

            if not w_word or not isinstance(w_word, str) or not w_meaning or not isinstance(w_meaning,
                                                                                            str) or not w_type or not isinstance(
                w_type, list):
                return {"error": "Words için gerekli tüm alanlar doğru doldurulmalıdır (TypeError)"}, 400

            w_word = w_word.strip()
            w_meaning = w_meaning.strip()
            if not w_word or not w_meaning or not w_type:
                return {"error": "Kelime, anlam veya tür alanı boş bırakılamaz"}, 400

            word_dict["word"] = w_word
            word_dict["meaning"] = w_meaning

            if "noun" in w_type:
                w_plural = word_dict.get("plural")
                if not w_plural or not isinstance(w_plural, str):
                    return {
                        "error": "İsim (noun) türündeki kelimeler için 'plural' (çoğul) alanı doğru doldurulmalıdır"}, 400
                w_plural = w_plural.strip()
                if not w_plural:
                    return {"error": "Çoğul (plural) alanı boş bırakılamaz"}, 400
                word_dict["plural"] = w_plural

                if learning_language in ["de", "el"]:
                    w_article = word_dict.get("article")
                    if not w_article or not isinstance(w_article, str):
                        return {"error": "Words için gerekli tüm alanlar doğru doldurulmalıdır (NoArticle)"}, 400
                    word_dict["article"] = w_article.strip()

            meanings = [m.strip() for m in w_meaning.split('/') if m.strip()]

            if not meanings:
                return {"error": "Anlam alanı sadece slash veya boşluklardan oluşamaz"}, 400

            for mean in meanings:
                new_word_dict = word_dict.copy()
                new_word_dict["meaning"] = mean
                processed_words.append(new_word_dict)

        weekly_words = WeeklyWords(
            user_id=user_id,
            week_number=new_week_number,
            words=processed_words,
            learning_language=learning_language,
            known_language=known_language
        )

        db.session.add(weekly_words)
        db.session.commit()

        return {"msg": "Yeni haftalık kelimeler başarıyla oluşturuldu", "new_week_number": new_week_number}, 201

    @staticmethod
    def get_weekly_words(username, user_id, week_number):
        if not username or week_number is None:
            return {"error": "Kullanıcı adı veya hafta numarası boş olamaz"}, 400

        weekly_words_of_user = db.session.query(WeeklyWords).filter_by(user_id=user_id, week_number=week_number).first()

        if not weekly_words_of_user:
            last_week = db.session.query(WeeklyWords).filter_by(user_id=user_id).order_by(
                WeeklyWords.week_number.desc()).first()
            if week_number == 0 and last_week:
                return {"words": last_week.words}, 200
            else:
                return {
                    "error": f"{username} kullanıcısına ait {week_number} numaralı hafta bulunamadı"}, 404 if week_number != 0 else {
                    "error": f"{username} kullanıcısına ait en son hafta bulunamadı"}, 404

        return {"words": weekly_words_of_user.words}, 200

    @staticmethod
    def get_all_weekly_words(username, user_id):
        all_weekly_words_of_user = db.session.query(WeeklyWords).filter_by(user_id=user_id).order_by(
            WeeklyWords.week_number.asc()).all()
        if not all_weekly_words_of_user:
            return {"error": f"{username} kullanıcısına ait herhangi bir haftalık kelime bulunamadı"}, 404

        all_words = {weekly_word.week_number: weekly_word.words for weekly_word in all_weekly_words_of_user}

        return {"all_weekly_words": all_words}, 200

    @staticmethod
    def get_last_week_number(username, user_id):
        last_week = db.session.query(WeeklyWords).filter_by(user_id=user_id).order_by(
            WeeklyWords.week_number.desc()).first()

        if last_week:
            return {"last_week_number": last_week.week_number}, 200
        else:
            return {"error": f"{username} kullanıcısına ait en son hafta ve numarası bulunamadı"}, 404

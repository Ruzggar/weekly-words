import copy
import random
from typing import List

from pydantic import BaseModel, Field
from sqlalchemy import desc

from app import extensions, db
from app.models.quiz import Quiz
from app.models.user import User
from app.models.weekly_words import WeeklyWords
from app.services.wrong_answers_service import WrongAnswersService


# Çoktan seçmeli soru yapısı
class MultiChoiceItem(BaseModel):
    question_sentence: str = Field(
        description="A question sentence in the learning language containing a blank space consisting of EXACTLY FIVE underscores (_____) (without the parentheses) where the target word should be.")
    options: List[str] = Field(
        description="Exactly 4 options, including one correct answer and three plausible distractors.", min_length=4,
        max_length=4)
    correct_option_index: int = Field(description="The integer index of the correct option (0, 1, 2, or 3).", ge=0,
                                      le=3)


# Çevirili örnek cümle yapısı
class SentenceItem(BaseModel):
    sentence: str = Field(
        description="An example sentence in the learning language that correctly uses the target word.")
    translate: str = Field(
        description="The translation of the sentence into the user's known language (known_language).")


# İçeriğin ana yapısı (multi_choice ve sentences listelerini barındırır)
class QuizContent(BaseModel):
    multi_choice: List[MultiChoiceItem] = Field(description="Multiple-choice questions generated for the target words.")
    sentences: List[SentenceItem] = Field(
        description="Example sentences with translations generated for the target words.")


# En dıştaki yanıt şeması
class TestScheme(BaseModel):
    content: QuizContent = Field(description="The complete generated quiz and study content.")


class QuizService:
    @staticmethod
    def generate_quiz(username, user_id):
        if not username or not user_id:
            return {"error": "Kullanıcı adı veya ID boş olamaz"}, 400

        user = db.session.query(User).filter_by(id=user_id, username=username).first()
        if not user:
            return {"error": f"{username} isimli ve {user_id} id'li bir kullanıcı bulunamadı"}, 404

        last_week = db.session.query(WeeklyWords).filter_by(user_id=user.id).order_by(
            WeeklyWords.week_number.desc()).first()
        if not last_week:
            return {"error": f"{username} isimli ve {user_id} id'li kullanıcıya ait herhangi bir hafta bulunamadı"}, 404

        if last_week.last_generated_daily_quiz_number >= 5:
            return {"error": "Bu haftanın tüm günlük testleri zaten oluşturulmuş"}, 409

        if last_week.last_generated_daily_quiz_number > last_week.last_completed_daily_quiz_number:
            return {"error": "Bir önceki günlük testi tamamlamadan yenisini oluşturamazsınız"}, 409

        last_weekly_words: List[dict] = last_week.words
        last_weekly_words_length = len(last_weekly_words)

        # 1. Kelimeleri günlere adil dağıtma
        number_per_day = last_weekly_words_length // 6
        mod = last_weekly_words_length % 6

        words_for_each_quiz = []
        for i in range(6):
            if i < mod:
                words_for_each_quiz.append(number_per_day + 1)
            else:
                words_for_each_quiz.append(number_per_day)

        seed_string = f"user_{user_id}_week_{last_week.week_number}"
        local_random = random.Random(seed_string)
        local_random.shuffle(words_for_each_quiz)

        # 2. Yeni test indeksini ve kelime sayısını belirleme
        new_generated_daily_quiz_number = last_week.last_generated_daily_quiz_number + 1
        words_for_this_quiz = words_for_each_quiz[new_generated_daily_quiz_number]

        # 3. Başlangıç indeksini hesaplama
        start_word_index = 0
        for i in range(new_generated_daily_quiz_number):
            start_word_index += words_for_each_quiz[i]

        # 4. Liste dilimleme ve AYRI AYRI %25 İHTİMAL HESAPLAMASI
        target_words = copy.deepcopy(last_weekly_words[start_word_index: start_word_index + words_for_this_quiz])

        for w in target_words:
            if "noun" in w.get("type", []):
                # Her iki output (çoktan seçmeli ve cümle) için ayrı ayrı %25 zar atıyoruz
                mc_plural = random.random() < 0.25
                sentence_plural = random.random() < 0.25

                # Eğer ikisi birden tutarsa, "en fazla birinde olabilir" kuralını korumak için rastgele birini iptal ediyoruz
                if mc_plural and sentence_plural:
                    if random.choice([True, False]):
                        mc_plural = False
                    else:
                        sentence_plural = False

                # Yapay zekaya nokta atışı emir veriyoruz
                if mc_plural:
                    w["regular_plural_instruction"] = "use_plural_in_multi_choice"
                elif sentence_plural:
                    w["regular_plural_instruction"] = "use_plural_in_sentence"
                else:
                    w["regular_plural_instruction"] = "use_singular_only"

        # =====================================================================
        # 5. PROMPT'U SİSTEM VE KULLANICI OLARAK İKİYE BÖLME
        # =====================================================================

        system_instruction = (
            "You are a strict, expert language learning quiz generator.\n\n"
            "STRICT RULES:\n"
            "1. For each word and for EACH of its 'type' (part of speech), generate EXACTLY ONE multiple-choice question AND EXACTLY ONE example sentence pair.\n"
            "2. MULTI_CHOICE REQUIREMENTS:\n"
            "   - 'question_sentence': Write a sentence in the Learning Language with a blank space consisting of EXACTLY FIVE UNDERSCORES (_____) (without the parentheses) where the target word belongs. DO NOT use fewer or more than 5 underscores.\n"
            "   - 'options': Provide exactly 4 options. One must be the correct target word. The other 3 must be plausible distractors in the Learning Language.\n"
            "   - 'correct_option_index': Provide the integer index (0, 1, 2, or 3) indicating where the correct answer is in the 'options' list.\n"
            "3. SENTENCES REQUIREMENTS:\n"
            "   - 'sentence': Write a complete example sentence using the target word correctly in the Learning Language.\n"
            "   - 'translate': Translate this sentence accurately into the Known Language.\n"
            "4. Make sure to vary the lengths of all generated sentences across short (1-6 words), medium (7-11 words), and long (12-15 words).\n"
            "5. The context of the sentences must align with the provided 'meaning' of the words.\n"
            "6. PLURAL NOUNS:\n"
            "   - For IRREGULAR plurals (e.g., mouse/mice, person/people): You MUST use the plural form instead of the singular in EXACTLY ONE of the two generated outputs (either in the multiple-choice question OR in the example sentence).\n"
            "   - For REGULAR plurals: Check the 'regular_plural_instruction' flag in the JSON details. \n"
            "     * If it is 'use_plural_in_multi_choice', use the plural form ONLY in the multiple-choice question.\n"
            "     * If it is 'use_plural_in_sentence', use the plural form ONLY in the example sentence.\n"
            "     * If it is 'use_singular_only' (or missing), use ONLY the singular form in both outputs.\n"
            "   - STRICT LIMIT: For any single target word, NEVER use the plural form in both of its generated outputs.\n"
            "7. GRAMMAR & SYNTAX: NEVER use inverted sentences or non-standard word order. Always construct natural sentences using standard, direct grammatical structures (e.g., standard Subject-Verb-Object order) appropriate for both the Learning Language and the Known Language."
        )

        user_content = (
            f"Learning Language: {last_week.learning_language}\n"
            f"Known Language (for translations): {last_week.known_language}\n\n"
            f"Target words and their details to process:\n{target_words}\n\n"
            "Please generate the quiz content based on these words following your strict system rules."
        )

        response = extensions.genai_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=user_content,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": TestScheme,
                "automatic_function_calling": {"disable": True},
            },
        )

        if response.parsed:
            result_dict = response.parsed.model_dump()
            quiz_content = result_dict.get("content", {})
            last_week_number = last_week.week_number

            new_quiz = Quiz(
                user_id=user_id,
                content=quiz_content,
                week_number=last_week_number,
                day_number=new_generated_daily_quiz_number
            )

            last_week.last_generated_daily_quiz_number = new_generated_daily_quiz_number

            db.session.add(new_quiz)
            db.session.commit()

            return {"content": quiz_content}, 200
        else:
            return {"error": "Yapay zekadan geçerli bir yanıt alınamadı"}, 500

    @staticmethod
    def get_quiz_content(user_id, username, week_number, day_number):
        quiz = db.session.query(Quiz).filter_by(
            user_id=user_id,
            week_number=week_number,
            day_number=day_number
        ).order_by(Quiz.id.desc()).first()

        if quiz and not quiz.final:
            return {"content": quiz.content}, 200
        elif quiz and quiz.final:
            return {"error": f"Final quiz olduğu için gönderilmedi, '/final-quiz/{week_number}'a istek atın"}, 409
        else:
            return {
                "error": f"{username} kullanıcısına ait {week_number}. hafta ve {day_number}. güne ait bir quiz bulunamadı"}, 404

    @staticmethod
    def get_weekly_quizzes_content(user_id, username, week_number):
        quizzes = db.session.query(Quiz).filter_by(
            user_id=user_id,
            week_number=week_number,
        ).order_by(Quiz.day_number.asc()).all()

        if quizzes:
            # Son eleman final testi mi diye kontrol et. Öyleyse listeden çıkar (pop) ve değişkene ata.
            final = None
            if quizzes[-1].final:
                final = quizzes.pop()

            quiz_dict = {}
            for quiz in quizzes:
                quiz_dict[f"day_number_{quiz.day_number}"] = quiz.content

            if final:
                quiz_dict["final"] = final.content

            return {"quizzes": quiz_dict}, 200
        else:
            return {
                "error": f"{username} kullanıcısına ait {week_number}. haftanın günlük testleri bulunamadı"}, 404

    @staticmethod
    def get_last_generated_quiz(user_id, username):
        last_quiz = db.session.query(Quiz).filter_by(user_id=user_id).order_by(
            desc(Quiz.week_number), desc(Quiz.day_number)
        ).first()

        if not last_quiz:
            return {"error": f"{username} kullanıcısına ait son quiz bulunamadı"}, 404
        last_quiz_week = last_quiz.week_number
        last_quiz_day = last_quiz.day_number
        return {"last_quiz_week": last_quiz_week, "last_quiz_day": last_quiz_day}, 200

    @staticmethod
    def get_last_completed_quiz(user_id, username):
        last_two_weekly_words = db.session.query(WeeklyWords).filter_by(
            user_id=user_id
        ).order_by(WeeklyWords.week_number.desc()).limit(2).all()

        if not last_two_weekly_words:
            return {"error": "Kullanıcıya ait herhangi bir hafta bulunamadı"}, 404

        # Liste 1 elemanlı da olsa, 2 elemanlı da olsa döngü sırayla (en yeniden eskiye) kontrol eder.
        for weekly_words in last_two_weekly_words:
            if weekly_words.last_completed_daily_quiz_number != -1:
                return {
                    "last_quiz_week": weekly_words.week_number,
                    "last_quiz_day": weekly_words.last_completed_daily_quiz_number
                }, 200

        return {
            "error": "Kullanıcının tamamladığı herhangi bir quiz bulunamadı veya birden çok tamamlanmamış hafta mevcut"}, 404

    @staticmethod
    def get_or_generate_final_quiz(user_id, username, week_number):
        final_quiz = db.session.query(Quiz).filter_by(
            user_id=user_id,
            week_number=week_number,
            final=True
        ).first()

        if final_quiz:
            return {"content": final_quiz.content}, 200
        else:
            quizzes = db.session.query(Quiz).filter_by(
                user_id=user_id,
                week_number=week_number,
            ).order_by(Quiz.day_number.asc()).all()

            if not quizzes:
                return {
                    "error": f"{username} kullanıcısına ait {week_number}. haftanın günlük testleri bulunamadı"}, 404
            elif len(quizzes) < 6:
                return {
                    "error": f"Henüz {week_number} haftasındaki tüm günlerin quizleri tamamlanmadığı için final testi oluşturulamaz"}, 409
            elif len(quizzes) > 6:
                return {"error": f"Zaten {week_number} haftası için oluşturulmuş bir final testi var"}, 409

            selection = "multi"
            final_quiz_content = {"multi_choice": [], "sentences": []}

            for quiz in quizzes:
                content: dict[str, list] = quiz.content
                multi_choice: list[dict] = content.get("multi_choice")
                sentences: list[dict] = content.get("sentences")

                for i in range(len(multi_choice)):
                    if selection == "multi":
                        final_quiz_content["multi_choice"].append(multi_choice[i])
                        selection = "sentence"
                    else:
                        final_quiz_content["sentences"].append(sentences[i])
                        selection = "multi"

            final_quiz = Quiz(
                user_id=user_id,
                content=final_quiz_content,
                week_number=week_number,
                day_number=6,  # Final quiz 7. gün olduğu için indeksi 6 olacak (0, 1, 2, 3, 4, 5 -> günlükler)
                final=True
            )

            db.session.add(final_quiz)
            db.session.commit()

            return {"content": final_quiz.content}, 200

    @staticmethod
    def quiz_completed(user_id, username, data):
        week_number = data.get("week_number")
        if not week_number:
            return {"error": "Hafta numarası boş olamaz"}, 400

        weekly_words_of_quiz = db.session.query(WeeklyWords).filter_by(
            user_id=user_id, week_number=week_number).first()

        if weekly_words_of_quiz and weekly_words_of_quiz.last_completed_daily_quiz_number != 6:
            weekly_words_of_quiz.last_completed_daily_quiz_number += 1
        elif not weekly_words_of_quiz:
            return {"error": f"{username} kullanıcısına ait {week_number}. haftaya ait quiz bulunamadı"}, 404

        questions_of_wrong_answers = data.get("questions")

        if not questions_of_wrong_answers:
            db.session.commit()
            return {"msg": "Quiz tamamlanması başarıyla işlendi"}, 200

        result, status_code = WrongAnswersService.add_wrong_answers(user_id, username, data)

        if result.get("msg") and status_code == 201:
            return {"msg": "Quiz tamamlanması başarıyla işlendi ve yanlış cevap verilen sorular başarıyla eklendi"}, 200
        else:
            return result, status_code

    @staticmethod
    def save_quiz_progress(user_id, username, week_number, day_number, current_index):
        if not week_number or day_number is None:
            return {"error": "Hafta veya gün numarası boş bırakılamaz"}, 400

        quiz = db.session.query(Quiz).filter_by(user_id=user_id, week_number=week_number, day_number=day_number).first()

        if not quiz:
            return {
                "error": f"{username} adlı kullanıcıya ait {week_number}. hafta {day_number}. gün quizi bulunamadı"}, 404

        quiz.progress = current_index
        db.session.commit()

        return {"msg": "Quiz ilerlemesi başarıyla kaydedildi"}, 200

    @staticmethod
    def get_quiz_progress(user_id, username, week_number, day_number):
        if not week_number or day_number is None:
            return {"error": "Hafta veya gün numarası boş bırakılamaz"}, 400

        quiz = db.session.query(Quiz).filter_by(user_id=user_id, week_number=week_number, day_number=day_number).first()

        if not quiz:
            return {
                "error": f"{username} adlı kullanıcıya ait {week_number}. hafta {day_number}. gün quizi bulunamadı"}, 404

        return {"current_index": quiz.progress}, 200
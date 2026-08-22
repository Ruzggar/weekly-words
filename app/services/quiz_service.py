from typing import List
from pydantic import BaseModel, Field

from app import extensions, db
from app.models.user import User
from app.models.quiz import Quiz
from app.models.weekly_words import WeeklyWords


class SentenceItem(BaseModel):
    word: str = Field(description="Kullanılan hedef kelime")
    part_of_speech: str = Field(description="Kelimenin cümlede kullanılan türü (örn: verb, noun)")
    word_count: int = Field(description="Cümledeki toplam kelime sayısı")
    text: str = Field(description="Üretilen örnek cümle")


class TestScheme(BaseModel):
    sentences: List[SentenceItem] = Field(
        description="Kurallara uygun olarak üretilen detaylı cümle objelerinin listesi."
    )


class QuizService:
    @staticmethod
    def generate_quiz(username, user_id):
        if not username or not user_id:
            return {"error": "Kullanıcı adı veya ID boş olamaz"}, 400

        user = User.query.filter_by(id=user_id, username=username).first()
        if not user:
            return {"error": f"{username} isimli ve {user_id} id'li bir kullanıcı bulunamadı"}, 404

        last_week = WeeklyWords.query.filter_by(user_id=user.id).order_by(WeeklyWords.week_number.desc()).first()
        if not last_week:
            return {"error": f"{username} isimli ve {user_id} id'li kullanıcıya ait herhangi bir hafta bulunamadı"}, 404
        if last_week.test_generated:
            return {"error": "Zaten testi oluşturulmuş bir haftanın testi tekrar oluşturulamaz"}, 409

        last_weekly_words: List[dict] = last_week.words

        # Prompt'u daha otoriter ve adım adım (Chain of Thought) yapısına uygun hale getirdik
        prompt = (
            f"Target words and their details: {last_weekly_words}\n\n"
            f"Language to use for sentences: {last_week.learning_language}\n\n"
            "STRICT RULES:\n"
            "1. For each word and for EACH of its 'type' (part of speech), you MUST write EXACTLY 2 example sentences.\n"
            "2. Keep the requested 'meaning' in mind while writing.\n"
            "3. You must vary the lengths of the sentences. Across all generated sentences, try to balance these categories:\n"
            "   - Short: 1-6 words\n"
            "   - Medium: 7-11 words\n"
            "   - Long: 12-15 words\n"
        )

        response = extensions.genai_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": TestScheme,
                "automatic_function_calling": {"disable": True},
            },
        )

        if response.parsed:
            # Yapay zekanın döndüğü detaylı listeyi (SentenceItem listesi) alıyoruz
            detailed_sentences = response.parsed.sentences

            # Veritabanına kaydetmek için sadece 'text' (cümle) kısmını string listesi olarak ayıklıyoruz
            example_sentences = [item.text for item in detailed_sentences]

            last_week_number = last_week.week_number

            new_quiz = Quiz(
                user_id=user_id,
                sentences=example_sentences,  # Eskisi gibi string listesi olarak kaydeder
                week_number=last_week_number
            )

            last_week.test_generated = True
            db.session.add(new_quiz)
            db.session.commit()

            # İstersen kullanıcıya sadece cümleleri dönebilirsin
            return {"sentences": example_sentences}, 200
        else:
            return {"error": "Yapay zekadan geçerli bir yanıt alınamadı"}, 500

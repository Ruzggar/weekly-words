from app.extensions import db


class WeeklyWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Yabancı Anahtar (Foreign Key) bağlantısı eklendi
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    week_number = db.Column(db.Integer, nullable=False)
    words = db.Column(db.JSON, nullable=False)
    learning_language = db.Column(db.String(2), nullable=False)
    known_language = db.Column(db.String(2), nullable=False)
    last_generated_daily_quiz_number = db.Column(db.Integer, nullable=False, default=-1)
    last_completed_daily_quiz_number = db.Column(db.Integer, nullable=False, default=-1)
    completed = db.Column(db.Boolean, default=False)
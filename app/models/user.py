from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # İLİŞKİLER (Relationships)
    # cascade="all, delete-orphan" -> Kullanıcı silinirse ona ait tüm verileri de otomatik siler
    weekly_words = db.relationship('WeeklyWords', backref='user', lazy=True, cascade="all, delete-orphan")
    wrong_answers = db.relationship('WrongAnswers', backref='user', lazy=True, cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
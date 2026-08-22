from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # User modelinin içine eklenecek:
    weekly_words = db.relationship('WeeklyWords', backref='user', lazy=True)

    # Şifreyi kaydetmeden önce hash'ler
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Girilen şifrenin doğruluğunu kontrol eder
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
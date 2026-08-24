from app.extensions import db


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Yabancı Anahtar (Foreign Key) bağlantısı eklendi
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    content = db.Column(db.JSON, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    final = db.Column(db.Boolean, nullable=False, default=False)

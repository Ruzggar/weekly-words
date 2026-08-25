from app.extensions import db

class WrongAnswers(db.Model):
    id = db.Column(db.Integer, primary_key=True) # EKLENDİ: Primary Key olmadan SQLAlchemy tablo oluşturmaz.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.Column(db.JSON, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    day_number = db.Column(db.Integer, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
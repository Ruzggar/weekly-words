from app.extensions import db

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sentences = db.Column(db.JSON, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
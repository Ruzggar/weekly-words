from app.extensions import db

class WeeklyWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    words = db.Column(db.JSON, nullable=False)
    learning_language = db.Column(db.String(2), nullable=False)
    known_language = db.Column(db.String(2), nullable=False)
    test_generated = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
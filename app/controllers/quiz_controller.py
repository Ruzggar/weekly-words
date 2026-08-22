from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.quiz_service import QuizService

quiz_bp = Blueprint('quizzes', __name__)

@quiz_bp.route('/generate-quiz', methods=['POST'])
@jwt_required()
def generate_quiz():
    # Identity artık user_id, ek verilerden username alıyoruz
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.generate_quiz(username, user_id)

    return jsonify(result), status_code
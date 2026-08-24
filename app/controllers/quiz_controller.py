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


@quiz_bp.route('/get-quiz-content/<int:week_number>/<int:day_number>', methods=['GET'])
@jwt_required()
def get_quiz_content(week_number, day_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_quiz_content(user_id, username, week_number, day_number)

    return jsonify(result), status_code


@quiz_bp.route('/get-quiz-content/<int:week_number>', methods=['GET'])
@jwt_required()
def get_weekly_quizzes_content(week_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_weekly_quizzes_content(user_id, username, week_number)

    return jsonify(result), status_code


@quiz_bp.route('/get-quiz-history', methods=['GET'])
@jwt_required()
def get_quiz_history():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_quiz_history(user_id, username)

    return jsonify(result), status_code


@quiz_bp.route('/final-quiz/<int:week_number>', methods=['GET'])
@jwt_required()
def get_or_generate_final_quiz(week_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_or_generate_final_quiz(user_id, username, week_number)

    return jsonify(result), status_code

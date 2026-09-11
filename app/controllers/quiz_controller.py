from flask import Blueprint, jsonify, request
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


@quiz_bp.route('/quiz-content/<int:week_number>/<int:day_number>', methods=['GET'])
@jwt_required()
def get_quiz_content(week_number, day_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_quiz_content(user_id, username, week_number, day_number)

    return jsonify(result), status_code


@quiz_bp.route('/quiz-content/<int:week_number>', methods=['GET'])
@jwt_required()
def get_weekly_quizzes_content(week_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_weekly_quizzes_content(user_id, username, week_number)

    return jsonify(result), status_code


@quiz_bp.route('/last-generated-quiz', methods=['GET'])
@jwt_required()
def get_last_generated_quiz():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_last_generated_quiz(user_id, username)

    return jsonify(result), status_code


@quiz_bp.route('/last-completed-quiz', methods=['GET'])
@jwt_required()
def get_last_completed_quiz():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_last_completed_quiz(user_id, username)

    return jsonify(result), status_code


@quiz_bp.route('/final-quiz/<int:week_number>', methods=['GET'])
@jwt_required()
def get_or_generate_final_quiz(week_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_or_generate_final_quiz(user_id, username, week_number)

    return jsonify(result), status_code


@quiz_bp.route('/quiz-completed', methods=['POST'])
@jwt_required()
def quiz_completed():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    data = request.get_json()

    result, status_code = QuizService.quiz_completed(user_id, username, data)

    return jsonify(result), status_code

@quiz_bp.route('/save-quiz-progress/<int:week_number>/<int:day_number>', defaults={'current_index': None}, methods=['POST'])
@quiz_bp.route('/save-quiz-progress/<int:week_number>/<int:day_number>/<int:current_index>', methods=['POST'])
@jwt_required()
def save_quiz_progress(week_number, day_number, current_index):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.save_quiz_progress(user_id, username, week_number, day_number, current_index)

    return jsonify(result), status_code


@quiz_bp.route('/quiz-progress/<int:week_number>/<int:day_number>', methods=['GET'])
@jwt_required()
def get_quiz_progress(week_number, day_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = QuizService.get_quiz_progress(user_id, username, week_number, day_number)

    return jsonify(result), status_code
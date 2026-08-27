from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.wrong_answers_service import WrongAnswersService

wrong_answers_bp = Blueprint('wrong_answers', __name__)


# @wrong_answers_bp.route('/add-wrong-answers', methods=['POST'])
# @jwt_required()
# def add_wrong_answers():
#     user_id = get_jwt_identity()
#     username = get_jwt().get('username')
#     data = request.get_json()
#
#     result, status_code = WrongAnswersService.add_wrong_answers(user_id, username, data)
#     return jsonify(result), status_code


@wrong_answers_bp.route('/wrong-answers/<int:week_number>/<int:day_number>', methods=['GET'])
@jwt_required()
def get_wrong_answers_by_week_and_day(week_number, day_number):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = WrongAnswersService.get_wrong_answers_by_week_and_day(user_id, username, week_number,
                                                                                day_number)
    return jsonify(result), status_code


@wrong_answers_bp.route('/wrong-answers/<any(all, new, old):filter_type>', methods=['GET'])
@jwt_required()
def get_wrong_answers_by_filter(filter_type):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = WrongAnswersService.get_wrong_answers_by_filter(user_id, username, filter_type)
    return jsonify(result), status_code


@wrong_answers_bp.route('/generate-wrong-answers-quiz/<int:question_count>/<any(all, new, old):filter_type>',
                        methods=['GET'])
@jwt_required()
def generate_wrong_answers_quiz(question_count, filter_type):
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = WrongAnswersService.generate_wrong_answers_quiz(user_id, username, question_count,
                                                                          filter_type)
    return jsonify(result), status_code


@wrong_answers_bp.route('/change-wrong-answers-status', methods=['POST'])
@jwt_required()
def change_wrong_answers_status():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')
    data = request.get_json()

    result, status_code = WrongAnswersService.change_wrong_answers_status(user_id, username, data)
    return jsonify(result), status_code


@wrong_answers_bp.route('/wrong-answers-info', methods=['GET'])
@jwt_required()
def get_wrong_answers_info():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = WrongAnswersService.get_wrong_answers_info(user_id, username)
    return jsonify(result), status_code

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.weekly_words_service import WeeklyWordsService

weekly_words_bp = Blueprint('weekly_words', __name__)

@weekly_words_bp.route('/add-weekly-words', methods=['POST'])
@jwt_required()
def add_weekly_words():
    data = request.get_json()

    user_id = get_jwt_identity()
    username = get_jwt().get('username')
    words = data.get('words')
    learning_language = data.get('learning_language')
    known_language = data.get('known_language')

    result, status_code = WeeklyWordsService.add_weekly_words(username, user_id, words, learning_language, known_language)

    return jsonify(result), status_code


@weekly_words_bp.route('/weekly-words/<int:week_number>', methods=['GET'])
@jwt_required()
def get_weekly_words(week_number):
    # eğer hafta numarası olarak 0 gelirse -varsa- en son haftanın kelimeleri dönülür
    user_id = get_jwt_identity()
    username = get_jwt().get('username')

    result, status_code = WeeklyWordsService.get_weekly_words(username, user_id, week_number)
    return jsonify(result), status_code

@weekly_words_bp.route('/last-week-number', methods=['GET'])
@jwt_required()
def get_last_week_number():
    username = get_jwt_identity()
    user_id = get_jwt().get('id')

    result, status_code = WeeklyWordsService.get_last_week_number(username, user_id)
    return jsonify(result), status_code
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    result, status_code = AuthService.register_user(
        username=data.get('username'),
        password=data.get('password'),
        learning_language=data.get('learning_language'),
        known_language=data.get('known_language')
    )
    return jsonify(result), status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result, status_code = AuthService.login_user(
        username=data.get('username'),
        password=data.get('password')
    )
    return jsonify(result), status_code


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    username = get_jwt().get('username')
    return jsonify({"msg": f"Başarıyla eriştiniz. Giriş yapan kullanıcı: {username} (ID: {user_id})"}), 200


@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    result, status_code = AuthService.logout_user(jti)
    return jsonify(result), status_code


@auth_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = get_jwt_identity()  # Identity artık user_id
    jti = get_jwt()["jti"]
    result, status_code = AuthService.delete_account(user_id, jti)
    return jsonify(result), status_code


@auth_bp.route('/change-username', methods=['PUT'])
@jwt_required()
def change_username():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_username = data.get('new_username')
    jti = get_jwt()["jti"]

    result, status_code = AuthService.change_username(user_id, new_username, jti)
    return jsonify(result), status_code


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    result, status_code = AuthService.change_password(user_id, old_password, new_password)
    return jsonify(result), status_code


@auth_bp.route('/logout-all', methods=['DELETE'])
@jwt_required()
def logout_all():
    user_id = get_jwt_identity()

    result, status_code = AuthService.logout_all_sessions(user_id)
    return jsonify(result), status_code

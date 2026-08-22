from datetime import timedelta, timezone, datetime
from flask import Flask
from app.extensions import db, jwt
import os


def create_app():
    app = Flask(__name__)

    # Veritabanı yapılandırması
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'database.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT Yapılandırması
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")

    # Access token süresini 1 haftaya çıkardık, refresh token ayarını sildik
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

    # Eklentileri uygulamaya bağla
    db.init_app(app)
    jwt.init_app(app)

    # Modeller
    from app.models.user import User
    from app.models.weekly_words import WeeklyWords
    from app.models.blocklist import TokenBlocklist
    from app.models.quiz import Quiz

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        user_id = jwt_payload.get("sub")  # Flask-JWT-Extended'da identity "sub" (subject) anahtarında tutulur

        # 1. Spesifik olarak bu token iptal edilmiş mi? (Normal Logout Kontrolü)
        token_revoked = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
        if token_revoked is not None:
            return True

        # 2. Kullanıcı "Tüm cihazlardan çıkış yap" demiş mi? (Logout All Kontrolü)
        if user_id:
            marker_jti = f"logout_all_{user_id}"

            # Bu kullanıcı için atılmış en güncel "logout_all" işaretçisinin tarihini al
            last_logout_all = db.session.query(TokenBlocklist.created_at) \
                .filter_by(jti=marker_jti) \
                .order_by(TokenBlocklist.created_at.desc()).first()

            if last_logout_all:
                last_logout_date = last_logout_all[0]

                # Token'ın oluşturulma zamanını UTC formatında datetime objesine çevir
                # (jwt_payload["iat"] bize unix timestamp saniyesi verir)
                token_iat = datetime.fromtimestamp(jwt_payload["iat"], timezone.utc)

                # Eğer token, "tüm cihazlardan çıkış" emrinden ÖNCE oluşturulmuşsa artık geçersizdir
                if token_iat < last_logout_date:
                    return True

        return False

    # Blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.weekly_words_controller import weekly_words_bp
    from app.controllers.quiz_controller import quiz_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(weekly_words_bp)
    app.register_blueprint(quiz_bp)

    with app.app_context():
        db.create_all()
        print("Veritabanı ve tablolar başarıyla oluşturuldu/kontrol edildi!")

    return app
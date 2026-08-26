from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.blocklist import TokenBlocklist
from app.models.user import User


class AuthService:

    @staticmethod
    def register_user(username, password):
        if not username or not password:
            return {"error": "Kullanıcı adı ve şifre zorunludur"}, 400

        if db.session.query(User).filter_by(username=username).first():
            return {"error": "Bu kullanıcı adı zaten alınmış"}, 400

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return {"msg": "Kullanıcı başarıyla oluşturuldu"}, 201

    @staticmethod
    def login_user(username, password):
        user = db.session.query(User).filter_by(username=username).first()

        if not user or not user.check_password(password):
            return {"error": "Hatalı kullanıcı adı veya şifre"}, 401

        # Identity olarak user_id (string formatında), ek veri olarak username veriyoruz
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"username": user.username}
        )

        return {
            "access_token": access_token
        }, 200

    @staticmethod
    def logout_user(jti):
        revoked_token = TokenBlocklist(jti=jti)
        db.session.add(revoked_token)
        db.session.commit()
        return {"msg": "Başarıyla çıkış yapıldı"}, 200

    @staticmethod
    def delete_account(user_id, jti):
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": "Kullanıcı bulunamadı"}, 404

        db.session.delete(user)
        revoked_token = TokenBlocklist(jti=jti)
        db.session.add(revoked_token)
        db.session.commit()
        return {"msg": "Hesap başarıyla silindi"}, 200

    @staticmethod
    def change_username(user_id, new_username, jti):
        if not new_username:
            return {"error": "Yeni kullanıcı adı boş olamaz"}, 400

        if db.session.query(User).filter_by(username=new_username).first():
            return {"error": "Bu kullanıcı adı zaten alınmış"}, 400

        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": "Kullanıcı bulunamadı"}, 404

        # 1. Önce kullanıcı adını değiştir ve kaydet
        user.username = new_username
        db.session.commit()

        # 2. Kod tekrarı yapmadan, tüm cihazlardan çıkış fonksiyonunu çağır
        # (Dönen sonucu bir değişkene atamamıza gerek yok)
        AuthService.logout_all_sessions(user_id)

        # 3. Mevcut cihaza yeni bilgilerle token ver
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"username": user.username}
        )

        return {
            "msg": "Kullanıcı adı başarıyla güncellendi. Diğer tüm cihazlardan çıkış yapıldı.",
            "access_token": access_token
        }, 200

    @staticmethod
    def change_password(user_id, old_password, new_password):
        if not old_password or not new_password:
            return {"error": "Eski ve yeni şifre alanları zorunludur"}, 400

        user = db.session.query(User).filter_by(id=user_id).first()

        if not user or not user.check_password(old_password):
            return {"error": "Eski şifrenizi yanlış girdiniz"}, 401

        # 1. Şifreyi güncelle ve kaydet
        user.set_password(new_password)
        db.session.commit()

        # 2. Kod tekrarı yapmadan diğer oturumları kapat
        AuthService.logout_all_sessions(user_id)

        return {"msg": "Şifreniz başarıyla güncellendi. Tüm cihazlardan çıkış yapıldı. Lütfen tekrar giriş yapın."}, 200

    @staticmethod
    def logout_all_sessions(user_id):
        # Tüm oturumları kapatmak için jti sütununa spesifik bir işaretçi kaydediyoruz.
        # Bu sayede veritabanında yeni bir sütun/tablo açmamıza gerek kalmıyor.
        marker_jti = f"logout_all_{user_id}"

        revoked_marker = TokenBlocklist(jti=marker_jti)
        db.session.add(revoked_marker)
        db.session.commit()

        return {"msg": "Tüm cihazlardan başarıyla çıkış yapıldı"}, 200
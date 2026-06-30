from fastapi import HTTPException, Request
from supabase_client import get_supabase
import jwt
import os


async def get_current_user(request: Request):
    """Bearer <jwt> → Supabase ile doğrula.

    Header(...) yerine Request kullan — daha güvenilir.
    """
    # Header'ı manuel olarak al
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Geçersiz token formatı.")

    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(401, "Token boş olamaz.")

    # JWT decode yöntemi (Supabase v2'de get_user() çalışmıyor)
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")

    if jwt_secret:
        # Secret varsa tam doğrulama yap
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            user_id = payload.get("sub")
            email = payload.get("email")

            if not user_id:
                raise HTTPException(401, "Token'da user bilgisi yok.")

            return {"id": str(user_id), "email": email}
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token süresi dolmuş.")
        except jwt.InvalidTokenError as e:
            raise HTTPException(401, f"Geçersiz token: {e}")

    # Secret yoksa verify'siz decode (sadece development için)
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(401, "Token'da user bilgisi yok.")

        return {"id": str(user_id), "email": email}
    except Exception as e:
        raise HTTPException(401, f"Token decode edilemedi: {e}")
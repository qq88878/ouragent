"""JWT Token ????"""
import os
import jwt
from datetime import datetime

JWT_SECRET = os.environ.get("JWT_SECRET", os.environ.get("SECRET_KEY", "default-secret-key"))
JWT_ALGORITHMS = ["HS256", "HS384", "HS512"]

def decode_jwt_token(token: str) -> dict:
    """?????JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHMS)
        # ????
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise jwt.ExpiredSignatureError("Token???")
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError as e:
        raise ValueError(f"???Token: {e}")

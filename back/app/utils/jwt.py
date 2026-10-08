import jwt
from datetime import timedelta,timezone,datetime
from app.config import settings


def create_jwt_token(data:dict,expires_dalta:timedelta|None=None):
    to_encode = data.copy()
    #token的过期时间
    expire = datetime.now(timezone.utc)+(expires_dalta or timedelta(minutes=settings.JWT_EXPIRE))

    to_encode.update({
        "exp":expire
    })

    token = jwt.encode(
        to_encode,
        settings.JWT_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


#解析token
def decode_token(token:str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
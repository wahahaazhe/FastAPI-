# app/utils/security.py
from datetime import datetime, timedelta, timezone  # timezone 是重要的
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        # 使用 timezone.utc 来确保时间是一致的 UTC 时间
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})  # 'exp' 是JWT标准声明，代表过期时间
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 确认这个函数存在且名称完全一致
def decode_access_token(token: str) -> Optional[str]:
    """
    Decodes an access token.
    Returns the username (from 'sub' claim) if the token is valid and not expired.
    Returns None otherwise.
    """
    try:
        # jwt.decode 会自动验证签名和过期时间
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")  # "sub" claim typically holds the username

        if username is None:
            return None  # 'sub' claim not found

        # 可选：再次检查过期时间，虽然 jwt.decode 应该已经处理了
        # exp = payload.get("exp")
        # if exp is not None and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
        #     return None # Token has expired (double check)

        return username
    except JWTError:  # 包括 ExpiredSignatureError, JWTClaimsError 等
        return None  # Token is invalid (e.g., signature mismatch, expired, malformed)
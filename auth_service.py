# app/services/auth_service.py
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional  # 确保 Optional 被导入

from ..models.users import User, UserCreate  # UserCreate 用于注册
from ..utils.security import verify_password, create_access_token, get_password_hash, decode_access_token
from ..database import get_session

# tokenUrl 应该与 API 路由中的登录端点匹配
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def db_register_user(session: Session, user_create: UserCreate) -> User:
    """
    Registers a new user in the database.
    Checks for existing username and email.
    Hashes the password before saving.
    """
    # 检查用户名是否已存在
    existing_user_by_username = session.exec(select(User).where(User.username == user_create.username)).first()
    if existing_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # 检查邮箱是否已存在
    existing_user_by_email = session.exec(select(User).where(User.email == user_create.email)).first()
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user_create.password)

    # 创建用户实例
    # is_active 默认为 True (在 User 模型中定义)，所以这里可以不显式设置，除非你想覆盖
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password
        # is_active 默认为 True
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)  # 获取数据库生成的 id 和 created_at 等字段
    return db_user


def db_login_user(session: Session, username: str, password: str) -> Optional[dict]:
    """
    Authenticates a user and returns an access token if successful.
    Returns None if authentication fails.
    """
    user = session.exec(select(User).where(User.username == username)).first()

    # 检查用户是否存在，是否激活，以及密码是否正确
    if not user:
        return None
    if not user.is_active:  # 确保用户是激活状态
        # 或者可以抛出特定的HTTPException，例如：
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        return None  # 对于登录失败，通常不区分具体原因以避免信息泄露
    if not verify_password(password, user.hashed_password):
        return None

    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})  # "sub" 是JWT标准声明，代表主题(subject)
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_active_user(
        session: Session = Depends(get_session), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Decodes the JWT token, retrieves the user from the database,
    and ensures the user is active.
    Raises HTTPException if token is invalid, user not found, or user is inactive.
    This function is used as a dependency for protected routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # 指示客户端如何进行认证
    )

    username = decode_access_token(token)  # 从 security.py 获取解码后的用户名
    if username is None:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception  # 用户在数据库中不存在

    if not user.is_active:
        # 虽然 decode_access_token 验证了 token 本身，但用户的状态可能已改变
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


def db_user_logout() -> dict:
    """
    Provides a message for user logout.
    Actual logout (token invalidation) is typically handled client-side
    by discarding the token. Server-side token blacklisting is more complex.
    """
    return {"message": "Successfully logged out. Please clear your token on the client-side."}
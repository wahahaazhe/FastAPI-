# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # 用于登录表单
from sqlmodel import Session
from typing import Optional # 确保 Optional 被导入，因为 db_login_user 可能返回 Optional[dict]

from ..database import get_session
from ..models.users import UserCreate, UserRead, User # User 是 get_current_active_user 的返回类型
from ..services.auth_service import ( # 确保这里导入的名称与 service 文件中定义的完全一致
    db_register_user,
    db_login_user,
    get_current_active_user,
    db_user_logout
)

# prefix 会给这个 router 下的所有路径加上 /auth 前缀
# tags 会在 OpenAPI (Swagger UI) 文档中将这些端点分组
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="注册新用户")
async def register_user_api(
    user_data: UserCreate, # 请求体应该符合 UserCreate schema
    session: Session = Depends(get_session) # 数据库会话依赖注入
):
    """
    Handles new user registration.
    - Receives user data (username, email, password).
    - Calls the service layer to create the user.
    - Returns the created user's public information.
    """
    try:
        # 调用服务层函数进行注册
        created_user = db_register_user(session=session, user_create=user_data)
        return created_user
    except HTTPException as e:
        # 如果服务层抛出了特定的HTTPException (如用户已存在)，则重抛
        raise e
    except Exception as e:
        # 捕获其他意外错误，并返回一个通用的服务器错误
        # 实际项目中，这里应该记录日志 e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {str(e)}"
        )

@router.post("/token", summary="用户登录获取访问令牌") # FastAPI 会自动处理 response_model for OAuth2PasswordBearer
async def login_for_access_token_api(
    form_data: OAuth2PasswordRequestForm = Depends(), # FastAPI 内置，处理 username/password 表单
    session: Session = Depends(get_session)
):
    """
    Handles user login and issues an access token.
    - Expects `username` and `password` in `application/x-www-form-urlencoded` format.
    - Calls the service layer to authenticate the user.
    - Returns an access token if authentication is successful.
    """
    token_data = db_login_user(
        session=session,
        username=form_data.username,
        password=form_data.password
    )
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # 或 status.HTTP_400_BAD_REQUEST
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # 标准的未授权响应头
        )
    return token_data # 返回 {"access_token": "...", "token_type": "bearer"}

@router.get("/me", response_model=UserRead, summary="获取当前已认证用户信息")
async def read_users_me_api(
    current_user: User = Depends(get_current_active_user) # 依赖注入，确保用户已认证且活跃
):
    """
    Returns the information of the currently authenticated user.
    This is a protected endpoint.
    """
    # current_user 已经是 User 类型的 ORM 对象
    # FastAPI 会自动根据 response_model=UserRead 来序列化它
    return current_user

@router.post("/logout", summary="用户登出")
async def logout_api():
    """
    Provides a logout confirmation message.
    Client is responsible for clearing the token.
    """
    return db_user_logout()
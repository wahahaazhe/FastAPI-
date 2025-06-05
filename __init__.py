# app/models/__init__.py
from .users import User, UserCreate, UserRead, UserLogin
from .posts import Post, PostCreate, PostRead, UserFavorite

# 这个列表可以帮助我们在 database.py 中确保所有模型都被识别
# __all__ = ['User', 'UserCreate', 'UserRead', 'UserLogin', 'Post', 'PostCreate', 'PostRead', 'UserFavorite']
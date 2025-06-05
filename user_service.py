from sqlmodel import Session, select
from ..models.posts import Post, UserFavorite
from ..models.users import User
from typing import List, Optional
import os
from fastapi import UploadFile
from ..config import UPLOAD_DIR


# 获取单个帖子
def db_get_post_by_id(session: Session, post_id: int):
    return session.get(Post, post_id)


# 获取用户收藏的帖子
def db_get_favor(session: Session, user_id: int):
    statement = select(Post).join(UserFavorite).where(UserFavorite.user_id == user_id)
    return session.exec(statement).all()


# 检查用户是否收藏了帖子
def db_is_user_favor_post(session: Session, user_id: int, post_id: int) -> bool:
    favorite = session.exec(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.post_id == post_id
        )
    ).first()
    return favorite is not None


# 用户上传PDF文件
def db_user_uploadpdf(session: Session, user_id: int, file: UploadFile):
    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 生成文件路径
    file_location = f"{UPLOAD_DIR}/{user_id}_{file.filename}"

    # 保存文件
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    return {"filename": file.filename, "path": file_location}


# 创建新帖子
def db_user_set_one_post(session: Session, user_id: int, title: str, content: str, file_path: Optional[str] = None):
    new_post = Post(title=title, content=content, author_id=user_id, file_path=file_path)

    session.add(new_post)
    session.commit()
    session.refresh(new_post)

    return new_post


# 批量获取帖子
def db_get_batch_post_url(session: Session, skip: int = 0, limit: int = 10):
    return session.exec(select(Post).offset(skip).limit(limit)).all()

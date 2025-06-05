# app/services/post_service.py
import os
import shutil  # 用于保存文件
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlmodel import Session, select

from ..models.posts import Post, PostCreate, UserFavorite
from ..models.users import User  # 用于类型提示
from ..config import UPLOAD_DIR


def db_create_post(session: Session, post_data: PostCreate, author_id: int, file: Optional[UploadFile] = None) -> Post:
    file_path_to_save = None
    if file:
        # 确保上传目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # 生成安全的文件名或唯一文件名，这里简单使用原始文件名（可能需要改进）
        # 注意：直接使用 client-provided filename 可能有安全风险 (e.g., path traversal)
        # 更安全的做法是生成一个UUID作为文件名，并保留原始扩展名
        filename = f"{author_id}_{file.filename}"  # 简单示例
        file_location = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            file_path_to_save = os.path.join("static", "uploads", filename)  # 存储相对路径，用于URL访问
        except Exception as e:
            # 处理文件保存错误
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
        finally:
            file.file.close()  # 确保文件关闭

    db_post = Post(
        title=post_data.title,
        content=post_data.content,
        author_id=author_id,
        file_path=file_path_to_save
    )
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post


def db_get_post_by_id(session: Session, post_id: int) -> Optional[Post]:
    return session.get(Post, post_id)


def db_get_posts(session: Session, skip: int = 0, limit: int = 10) -> List[Post]:
    return session.exec(select(Post).offset(skip).limit(limit)).all()


# --- 收藏相关 ---
def db_add_favorite(session: Session, user_id: int, post_id: int) -> UserFavorite:
    # 检查帖子是否存在
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # 检查是否已收藏
    existing_favorite = session.exec(
        select(UserFavorite).where(UserFavorite.user_id == user_id, UserFavorite.post_id == post_id)
    ).first()
    if existing_favorite:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post already favorited")

    favorite = UserFavorite(user_id=user_id, post_id=post_id)
    session.add(favorite)
    session.commit()
    session.refresh(favorite)
    return favorite


def db_remove_favorite(session: Session, user_id: int, post_id: int):
    favorite = session.exec(
        select(UserFavorite).where(UserFavorite.user_id == user_id, UserFavorite.post_id == post_id)
    ).first()
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    session.delete(favorite)
    session.commit()
    return {"message": "Favorite removed successfully"}


def db_get_user_favorites(session: Session, user_id: int) -> List[Post]:
    # 查询用户收藏的所有帖子的 ID
    # 然后根据这些 ID 获取帖子对象
    # SELECT posts.* FROM posts JOIN user_favorites ON posts.id = user_favorites.post_id WHERE user_favorites.user_id = :user_id
    statement = select(Post).join(UserFavorite).where(UserFavorite.user_id == user_id)
    return session.exec(statement).all()


def db_is_user_favor_post(session: Session, user_id: int, post_id: int) -> bool:
    favorite = session.exec(
        select(UserFavorite).where(UserFavorite.user_id == user_id, UserFavorite.post_id == post_id)
    ).first()
    return favorite is not None


# --- 文件上传 (如果单独作为服务) ---
# db_user_uploadpdf 已集成到 db_create_post, 如果需要独立上传，可以像这样:
def db_upload_file_generic(user_id: int, file: UploadFile) -> dict:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # filename = f"{user_id}_{file.filename}" # 可以加上时间戳或UUID避免重名
    # 更安全的文件名
    from uuid import uuid4
    ext = os.path.splitext(file.filename)[1]
    filename = f"{user_id}_{uuid4()}{ext}"

    file_location = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    finally:
        file.file.close()

    # 返回相对路径用于URL访问
    relative_file_path = os.path.join("static", "uploads", filename)
    return {"filename": file.filename, "saved_path": relative_file_path, "message": "File uploaded successfully"}
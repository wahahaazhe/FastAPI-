from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    file_path: Optional[str] = None
    author_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关系
    author: "User" = Relationship(back_populates="posts")
    favorites: List["UserFavorite"] = Relationship(back_populates="post")


class PostCreate(SQLModel):
    title: str
    content: str


class PostRead(SQLModel):
    id: int
    title: str
    content: str
    file_path: Optional[str]
    author_id: int
    created_at: datetime


class UserFavorite(SQLModel, table=True):
    __tablename__ = "user_favorites"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    post_id: int = Field(foreign_key="posts.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关系
    user: "User" = Relationship(back_populates="favorites")
    post: Post = Relationship(back_populates="favorites")

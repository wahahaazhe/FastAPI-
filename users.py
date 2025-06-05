from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关系
    posts: List["Post"] = Relationship(back_populates="author")
    favorites: List["UserFavorite"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    username: str
    email: str
    password: str


class UserLogin(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

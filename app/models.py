from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import (Column, String, Text, DateTime, Integer, ForeignKey,
                        Boolean)
from sqlalchemy.orm import relationship

from app.database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True)
    hashed_password: str = Column(String)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    is_verified: bool = Column(Boolean, default=False, nullable=False)

    posts = relationship("Post", back_populates="owner")
    comments = relationship("Comment", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String, index=True)
    content: str = Column(Text)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    is_blocked: bool = Column(Boolean, default=False)
    owner_id: int = Column(ForeignKey("users.id"), index=True)

    auto_reply: bool = Column(Boolean, default=False)
    auto_reply_delay: int = Column(Integer, default=0)

    owner = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(Base):
    __tablename__ = "comments"
    id: int = Column(Integer, primary_key=True, index=True)
    content: str = Column(Text)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    is_blocked: bool = Column(Boolean, default=False)
    post_id: int = Column(ForeignKey("posts.id"), index=True)
    author_id: int = Column(ForeignKey("users.id"), index=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")

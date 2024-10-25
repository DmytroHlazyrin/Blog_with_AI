from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    content: str

    auto_reply: bool = False
    auto_reply_delay: int = 0

class PostCreate(PostBase):
    pass


class PostUpdate(PostCreate):
    pass


class PostRead(PostBase):
    id: int
    created_at: datetime
    is_blocked: bool
    owner_id: int

    class Config:
        orm_mode = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    created_at: datetime
    is_blocked: bool
    post_id: int
    author_id: int
    parent_id: Optional[int] = None

    class Config:
        orm_mode = True


class CommentAnalytics(BaseModel):
    date: str
    total_comments: int
    blocked_comments: int

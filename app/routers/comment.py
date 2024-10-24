# from fastapi_users import fastapi_users
from typing import Optional, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.crud import create_post, get_posts, update_post, delete_post, \
    get_post, create_comment, update_comment, delete_comment, get_comments, \
    get_comment
from app import models, schemas
from app.auth.manager import current_user
from app.database import get_user_db, get_db


router = APIRouter()


@router.get("/posts/{post_id}/comments/", response_model=list[schemas.CommentRead])
async def get_comments_endpoint(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
    offset: int = 0,
    limit: int = 10,
    sort_by: Literal["created_at", "author_id"] = None,
    sort_order: Literal["asc", "desc"] = "asc"
) -> list[schemas.CommentRead]:
    return await get_comments(post_id=post_id, db=db, offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order, user=user)


@router.get("/comments/{comment_id}/", response_model=schemas.CommentRead)
async def get_comment_endpoint(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user)
) -> models.Comment:
    return await get_comment(comment_id=comment_id, db=db, user=user)


@router.post("/posts/{post_id}/comments/", response_model=schemas.CommentCreate, status_code=201)
async def create_comment_endpoint(
    post_id: int,
    comment: schemas.CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
) -> models.Comment:
    return await create_comment(post_id=post_id, comment=comment, db=db, user=user)


@router.put("/comments/{comment_id}/", response_model=schemas.CommentUpdate)
async def update_comment_endpoint(
    comment_id: int,
    updated_comment: schemas.CommentUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user)
) -> models.Comment:
    return await update_comment(comment_id=comment_id, updated_data=updated_comment, db=db, user=user)

@router.delete("/comments/{comment_id}/", status_code=204)
async def delete_comment_endpoint(
        comment_id: int,
        db: AsyncSession = Depends(get_db),
        user: models.User = Depends(current_user)
) -> None:
    return await delete_comment(comment_id=comment_id, db=db, user=user)

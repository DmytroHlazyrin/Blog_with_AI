from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.auth.manager import current_user
from app.crud import create_post, get_posts, update_post, delete_post, get_post
from app.database import get_db

router = APIRouter()


@router.get("/posts/", response_model=list[schemas.PostRead])
async def read_posts_endpoint(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
    offset: int = 0,
    limit: int = 10,
    sort_by: Literal["title", "date"] = None,
    sort_order: Literal["asc", "desc"] = "asc",
) -> list[models.Post]:
    return await get_posts(
        db=db,
        user=user,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/posts/{post_id}", response_model=schemas.PostRead)
async def read_post_endpoint(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user)
) -> models.Post:
    return await get_post(db=db, user=user, post_id=post_id)


@router.post("/posts/", response_model=schemas.PostRead, status_code=201)
async def create_post_endpoint(
    post: schemas.PostCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user)
) -> models.Post:
    return await create_post(post=post, db=db, user=user)


@router.put("/posts/{post_id}", response_model=schemas.PostRead)
async def update_post_endpoint(
    post_id: int,
    updated_post: schemas.PostUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user)
) -> models.Post:
    return await update_post(
        post_id=post_id,
        updated_data=updated_post,
        db=db,
        user=user
    )


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post_endpoint(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user)
) -> None:
    return await delete_post(db=db, user=user, post_id=post_id)

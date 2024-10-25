from datetime import date
from typing import Optional, Literal

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import asc, desc, select, func, Integer
from sqlalchemy.ext.asyncio import AsyncSession


from app import models, schemas
from app.ai.auto_reply import auto_reply
from app.ai.moderation import is_acceptable_text



async def get_posts(
        db: AsyncSession,
        user: models.User,
        offset: int = 0,
        limit: int = 10,
        sort_by: Literal["title", "date", None] = None,
        sort_order: Literal["asc", "desc"] = "asc",
) -> list[models.Post]:
    """
    Fetch posts from the database, with optional sorting and pagination.
    Superusers can see all posts, while regular users can only see unblocked posts.
    """
    # Start the query, filter if the user is not a superuser
    query = select(models.Post)

    if not user.is_superuser:
        query = query.where(models.Post.is_blocked == False)

    # Apply sorting based on the sort_by and sort_order parameters
    if sort_by:
        if sort_by == "title":
            order = asc(models.Post.title) if sort_order == "asc" else desc(
                models.Post.title)
        elif sort_by == "date":
            order = asc(
                models.Post.created_at) if sort_order == "asc" else desc(
                models.Post.created_at)
        else:
            raise HTTPException(status_code=400,
                                detail="Invalid sort_by field")

        query = query.order_by(order)

    # Apply pagination (offset and limit)
    query = query.offset(offset).limit(limit)

    # Execute the query and fetch results asynchronously
    result = await db.execute(query)
    posts = result.scalars().all()

    return posts


async def get_post(
        post_id: int,
        db: AsyncSession,
        user: models.User
) -> Optional[models.Post]:
    """
    Fetches a post by its ID, checking if the user can see it.
    """
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not user.is_superuser and post.is_blocked:
        raise HTTPException(status_code=403, detail="Post is blocked")

    return post

async def create_post(
        post: schemas.PostCreate,
        db: AsyncSession,
        user: models.User,
) -> models.Post:
    """
    Creates a new post for the given user.
    """

    new_post = models.Post(**post.dict())
    new_post.owner_id = user.id

    # Post moderation logic
    post_text = new_post.title + " " + new_post.content
    new_post.is_blocked = not is_acceptable_text(post_text)

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


async def update_post(
    post_id: int,
    updated_data: schemas.PostUpdate,
    db: AsyncSession,
    user: models.User,
) -> models.Post:
    """
    Updates an existing post with the provided data.
    """
    # Fetch the post by its ID
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")

    # Update the post fields
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(post, key, value)

    # Post moderation logic
    post_text = post.title + " " + post.content
    post.is_blocked = not await is_acceptable_text(post_text)

    # Commit the changes
    await db.commit()
    await db.refresh(post)  # Refresh the post instance with the latest data

    return post


async def delete_post(
    post_id: int,
    db: AsyncSession,
    user: models.User
) -> None:
    """
    Deletes a post by its ID.
    """
    # Fetch the post by its ID
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    # Delete the post
    await db.delete(post)
    await db.commit()


async def create_comment(
    post_id: int,
    parent_id: Optional[int],
    comment: schemas.CommentCreate,
    db: AsyncSession,
    user: models.User,
    background_tasks: BackgroundTasks,
) -> models.Comment:
    """
    Creates a new comment for the given post.
    """
    # Fetch the post by its ID
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalar_one_or_none()

    if parent_id:
        parent = await db.execute(select(models.Post).where(models.Comment.id == parent_id))
        parent_comment = parent.scalar_one_or_none()

        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.is_blocked:
        raise HTTPException(status_code=403, detail="Post is blocked")



    # Create the comment
    new_comment = models.Comment(**comment.dict(), post_id=post_id, author_id=user.id, parent_id=parent_id)
    new_comment_text = new_comment.content

    new_comment.is_blocked = not is_acceptable_text(new_comment_text)
    # new_comment.post_id = post_id
    # new_comment.author_id = user.id

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)  # Refresh the comment instance with the latest data

    # If auto_reply is enabled for the post, schedule an automatic reply
    if post.auto_reply and not new_comment.is_blocked:
        delay = post.auto_reply_delay
        background_tasks.add_task(auto_reply, post, new_comment, delay)

    return new_comment


async def update_comment(
    comment_id: int,
    updated_data: schemas.CommentUpdate,
    db: AsyncSession,
    user: models.User,
) -> models.Comment:
    """
    Updates an existing comment with the provided data.
    """
    # Fetch the comment by its ID
    result = await db.execute(select(models.Comment).where(models.Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")

    # Update the comment fields
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(comment, key, value)

    # Comment moderation logic
    comment_text = comment.content
    comment.is_blocked = not is_acceptable_text(comment_text)

    # Commit the changes
    await db.commit()
    await db.refresh(comment)  # Refresh the comment instance with the latest data
    return comment


async def delete_comment(
    comment_id: int,
    db: AsyncSession,
    user: models.User
) -> None:
    """
    Deletes a post by its ID.
    """
    # Fetch the post by its ID
    result = await db.execute(select(models.Comment).where(models.Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    # Delete the post
    await db.delete(comment)
    await db.commit()


async def get_comments(
    post_id: int,
    db: AsyncSession,
    user: models.User,
    offset: int = 0,
    limit: int = 10,
    sort_by: Literal["date", "author"] = "date",
    sort_order: Literal["asc", "desc"] = "asc"
) -> list[models.Comment]:
    """
    Fetches comments for a given post.
    """
    # Fetch the post by its ID
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.is_blocked:
        raise HTTPException(status_code=403, detail="Post is blocked")

    # Fetch the comments for the post
    query = select(models.Comment).where(models.Comment.post_id == post_id)

    if not user.is_superuser:
        query = query.where(models.Comment.is_blocked == False)

    if sort_by:
        if sort_by == "author_id":
            order = asc(models.Comment.author_id) if sort_order == "asc" else desc(
                models.Comment.author_id)
        elif sort_by == "created_at":
            order = asc(
                models.Comment.created_at) if sort_order == "asc" else desc(
                models.Comment.created_at)
        else:
            raise HTTPException(status_code=400,
                                detail="Invalid sort_by field")

        query = query.order_by(order)


    # Apply pagination (offset and limit)
    query = query.offset(offset).limit(limit)

    # Execute the query and fetch results asynchronously
    result = await db.execute(query)
    comments = result.scalars().all()

    return comments


async def get_comment(
        comment_id: int,
        db: AsyncSession,
        user: models.User,
) -> Optional[models.Comment]:
    """
    Fetches a comment by its ID.
    """
    result = await db.execute(select(models.Comment).where(models.Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if not user.is_superuser and comment.is_blocked:
        raise HTTPException(status_code=403, detail="Comment is blocked")

    return comment


async def get_comment_analytics(
        user: models.User,
        db: AsyncSession,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        offset: Optional[int] = 0,
        limit: Optional[int] = 10,
        sort_order: Literal["asc", "desc"] = "desc"
) -> list[dict]:
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")

    if date_from is None:
        date_from = (await db.execute(select(func.date(func.min(models.Comment.created_at))))).scalar()
    if date_to is None:
        date_to = str(date.today())

    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Invalid date range")

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order field")

    order = asc("date") if sort_order == "asc" else desc("date")

    query = (
        select(
            func.date(models.Comment.created_at).label("date"),
            func.count(models.Comment.id).label("total_comments"),
            func.sum(func.cast(models.Comment.is_blocked, Integer)).label(
                "blocked_comments")
        )
        .where(func.date(models.Comment.created_at).between(date_from, date_to))
        .group_by("date")
        .order_by(order)
    )

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)

    stats = [
        {
            "date": row.date,
            "total_comments": row.total_comments,
            "blocked_comments": row.blocked_comments or 0
        }
        for row in result.fetchall()
    ]

    return stats

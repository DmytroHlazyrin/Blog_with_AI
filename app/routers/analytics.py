from datetime import date
from typing import Optional, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, models
from app.auth.manager import current_user
from app.crud import get_comment_analytics
from app.database import get_db

router = APIRouter()


@router.get("/comments-daily-breakdown/", response_model=list[schemas.CommentAnalytics])
async def get_comment_analytics_endpoint(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_user),
) -> list[dict]:
    return await get_comment_analytics(date_from=date_from, date_to=date_to, db=db, user=user, sort_order=sort_order)
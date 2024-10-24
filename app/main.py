from fastapi import FastAPI
from app.auth.auth import auth_backend
from app.auth.manager import fastapi_users
from app.auth.schemas import UserRead, UserCreate
from app.routers import post, comment

app = FastAPI()


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(post.router, tags=["posts"])

app.include_router(comment.router, tags=["comments"])

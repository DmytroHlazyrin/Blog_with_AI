import os
from asyncio import sleep

import google.generativeai as gemini
from dotenv import load_dotenv

from app import models
from app.ai.config import GEMINI_AUTOREPLY_INSTRUCTION
from app.database import async_session_maker

load_dotenv()

gemini.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_config = {
  "max_output_tokens": 500,
}

MODEL = gemini.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=GEMINI_AUTOREPLY_INSTRUCTION,
)


async def auto_reply_comment(post: models.Post, comment: models.Comment) -> str:
    text = f"Post title: {post.title}\nPost content: {post.content}\nComment: {comment.content}"
    try:
        response = MODEL.generate_content(text).text
    except:
        response = "Thanks for your comment!" # In case of error, use a default message
    return response


async def auto_reply(post: models.Post, comment: models.Comment, delay) -> None:
    """
    Automatically replies to a comment on a post.
    """
    reply = await auto_reply_comment(post, comment)

    await sleep(delay)
    async with async_session_maker() as db:
        new_comment = models.Comment(
            content=reply,
            author_id=post.owner_id,
            parent_id=comment.id,
            post_id=post.id
        )
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)

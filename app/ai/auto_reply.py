import os

import google.generativeai as gemini
from dotenv import load_dotenv

from app.ai.config import GEMINI_AUTOREPLY_INSTRUCTION

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

def auto_reply_comment(post: str, comment: str) -> str:
    text = f"Post: {post}\nComment: {comment}"
    response = MODEL.generate_content(text).text

    return response

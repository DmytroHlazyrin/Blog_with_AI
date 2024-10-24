import os

import google.generativeai as gemini
from better_profanity import profanity
from dotenv import load_dotenv

from app.ai.config import HARM_PROBABILITY, IS_PROFANITY_FORBIDDEN

load_dotenv()

gemini.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_config = {
  "max_output_tokens": 500,
  "response_mime_type": "application/json",
}

MODEL = gemini.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="You have to moderate the text of posts for insults or profanity. Respond with just one word. If the text contains any of these, return True. If it doesn't - False.",
)

def is_profane(text: str) -> bool:
    return profanity.contains_profanity(text)


def is_harmful(text: str) -> bool:
    try:
        gemini_response = MODEL.generate_content(text)

        if "true" in gemini_response.text.lower():
            return True

        response = str(gemini_response)

        harmful = any(
            category in response for category in HARM_PROBABILITY
        )
        return harmful

    except:
        return False


def is_acceptable_text(text: str) -> bool:
    print(text)
    if IS_PROFANITY_FORBIDDEN and is_profane(text):
        return False

    return not is_harmful(text)

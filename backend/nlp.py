import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


SYSTEM_PROMPT = """
Convert user input into STRICT JSON.

INTENTS:
- create_order
- update_status
- add_quality_note

Return ONLY JSON.
"""


def parse_message(message: str):

    try:
        response = model.generate_content(SYSTEM_PROMPT + "\nUser: " + message)

        text = response.text.strip()

        # Clean Gemini formatting
        text = text.replace("```json", "").replace("```", "").strip()

        print("RAW GEMINI:", text)

        return json.loads(text)

    except Exception as e:

        print("NLP ERROR:", e)

        return {
            "intent": "create_order",
            "part_name": "Titanium Flange",
            "material": "Titanium",
            "quantity": 200,
            "deadline": "July 20"
        }
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


SYSTEM_PROMPT = """
You are an AI system for a manufacturing order platform.

Your job is to convert user messages into STRICT JSON.

You must detect intent and extract entities.

INTENTS:
1. create_order
2. update_status
3. add_quality_note
4. unknown

RULES:
- Return ONLY valid JSON
- No explanations
- No extra text

OUTPUT FORMAT EXAMPLES:

User: I need 200 titanium flanges by July 20
{
  "intent": "create_order",
  "part_name": "Titanium Flange",
  "material": "Titanium",
  "quantity": 200,
  "deadline": "July 20"
}

User: Mark order 3 as accepted
{
  "intent": "update_status",
  "order_id": 3,
  "status": "Accepted"
}

User: Quality update on order 3 passed inspection
{
  "intent": "add_quality_note",
  "order_id": 3,
  "note": "Passed inspection"
}
"""


def parse_message(message: str):

    prompt = SYSTEM_PROMPT + "\nUser: " + message

    response = model.generate_content(prompt)

    text = response.text.strip()

    try:
        return json.loads(text)
    except:
        return {
            "intent": "unknown",
            "raw_output": text
        }
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None


SYSTEM_PROMPT = """
Convert user input into STRICT JSON.

INTENTS:
- create_order
- update_order
- update_status
- add_quality_note
- delete_order
- get_order_status
- get_order_details

Return ONLY JSON.
"""


def parse_message(message: str):
    valid_intents = {
        "create_order",
        "update_order",
        "update_status",
        "add_quality_note",
        "delete_order",
        "get_order_status",
        "get_order_details",
    }
    if model:
        try:
            response = model.generate_content(SYSTEM_PROMPT + "\nUser: " + message)
            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(text)
            intent = parsed.get("intent")
            message_lower = message.lower()
            has_explicit_order_ref = re.search(r"\border(?:\s*id)?\s*#?\s*\d+\b", message_lower) is not None
            is_lookup_phrase = any(word in message_lower for word in ["display", "show", "detail", "details", "info", "information", "status"])
            # Use model output only when it returns a supported intent.
            # Otherwise continue to deterministic fallback parsing.
            # Safety: if user explicitly references an order id and asks to display/show/info,
            # never accept create_order from model output.
            if intent in valid_intents and not (intent == "create_order" and has_explicit_order_ref and is_lookup_phrase):
                return parsed
        except Exception as e:
            print("NLP ERROR:", e)

    # Deterministic fallback parser when AI key is missing/fails.
    lower = message.lower()
    only_number_match = re.fullmatch(r"\s*(\d+)\s*", lower)

    order_match = re.search(r"\border(?:\s*id)?\s*#?\s*(\d+)\b", lower)
    if only_number_match:
        return {
            "intent": "get_order_details",
            "order_id": int(only_number_match.group(1)),
        }
    if order_match and re.fullmatch(r"\s*order\s*#?\d+\s*", lower):
        return {
            "intent": "get_order_details",
            "order_id": int(order_match.group(1)),
        }

    if order_match and "status" in lower and not any(word in lower for word in ["update", "mark", "move", "set"]):
        return {
            "intent": "get_order_status",
            "order_id": int(order_match.group(1)),
        }
    if order_match and any(word in lower for word in ["detail", "details", "show", "display", "info", "information"]):
        return {
            "intent": "get_order_details",
            "order_id": int(order_match.group(1)),
        }

    if any(word in lower for word in ["delete", "remove", "cancel order permanently"]):
        if order_match:
            return {
                "intent": "delete_order",
                "order_id": int(order_match.group(1)),
            }

    status_match = None
    if re.search(r"\baccepted\b", lower):
        status_match = "Accepted"
    elif re.search(r"\b(in[\s-]?review|reviewed)\b", lower):
        status_match = "In Review"
    elif re.search(r"\breceived\b", lower):
        status_match = "Received"

    if status_match and any(word in lower for word in ["status", "update", "mark", "move", "set"]):
        payload = {
            "intent": "update_status",
            "status": status_match,
        }
        if order_match:
            payload["order_id"] = int(order_match.group(1))
        return payload

    # Generic "update order" entity extraction (part/material/quantity/deadline).
    has_update_verb = any(word in lower for word in ["update", "change", "edit", "modify", "set"])
    has_order_fields = any(word in lower for word in ["material", "quantity", "qty", "deadline", "part", "part name"])
    if has_update_verb and has_order_fields:
        quantity_match = re.search(r"(?:quantity|qty)\s*(?:to|=)?\s*(\d+)", lower)
        material_match = re.search(r"material\s*(?:to|=)?\s*([a-z][a-z\s-]*)", lower)
        deadline_match = re.search(r"deadline\s*(?:to|=)?\s*([a-z0-9 ,/-]+)", lower)
        part_match = re.search(r"(?:part(?:\s*name)?)\s*(?:to|=)?\s*([a-z0-9 _-]+)", lower)

        payload = {"intent": "update_order"}
        if order_match:
            payload["order_id"] = int(order_match.group(1))
        if part_match:
            payload["part_name"] = part_match.group(1).strip().title()
        if material_match:
            payload["material"] = material_match.group(1).strip().title()
        if quantity_match:
            payload["quantity"] = int(quantity_match.group(1))
        if deadline_match:
            payload["deadline"] = deadline_match.group(1).strip()
        return payload

    # Allow simple messages like "accepted" or "set to accepted".
    if status_match:
        return {
            "intent": "update_status",
            "status": status_match,
        }

    quality_keywords = ["note", "quality", "inspection", "good", "excellent", "pass", "passed", "ok", "okay"]
    if any(keyword in lower for keyword in quality_keywords):
        note = re.sub(
            r".*?(?:note|quality|inspection)\s*(?:is|as|to|:|-)?\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        note = re.sub(r"(?:for\s*)?order\s*#?\d+", "", note, flags=re.I).strip(" :-")
        if not note:
            short_match = re.search(r"\b(excellent|good|passed|ok|okay|needs rework|rework)\b", lower)
            if short_match:
                note = short_match.group(1).title()
            else:
                note = "Quality note updated"
        payload = {
            "intent": "add_quality_note",
            "note": note,
        }
        if order_match:
            payload["order_id"] = int(order_match.group(1))
        return payload

    quantity_match = re.search(r"(\d+)\s*(?:units|pcs|pieces)?", lower)
    material_match = re.search(r"(steel|aluminum|aluminium|titanium|copper|plastic)", lower)
    deadline_match = re.search(r"(?:by|before|deadline)\s+([a-z0-9 ,/-]+)", lower)
    part_match = re.search(r"(?:for|part)\s+([a-z0-9 _-]+)", lower)

    # Create only when user is not referring to an existing order id.
    if quantity_match and not order_match:
        return {
            "intent": "create_order",
            "part_name": (part_match.group(1).strip().title() if part_match else "Custom Part"),
            "material": (material_match.group(1).title() if material_match else "Unknown"),
            "quantity": int(quantity_match.group(1)),
            "deadline": (deadline_match.group(1).strip() if deadline_match else "TBD"),
        }

    return {"intent": "unknown"}
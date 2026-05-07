import re

def extract_order_id(message: str):
    match = re.search(r"\b(\d+)\b", message)
    return int(match.group(1)) if match else None


def parse_message(message: str):

    msg = message.lower().strip()

    # ================= DELETE ORDER =================
    if "delete order" in msg or "remove order" in msg:
        return {
            "intent": "delete_order",
            "order_id": extract_order_id(message)
        }

    # ================= GET ORDER STATUS =================
    if "status" in msg and "order" in msg:
        return {
            "intent": "get_order_status",
            "order_id": extract_order_id(message)
        }

    # ================= QUALITY WRITE (ONLY ACTION WORDS) =================
    if ("quality" in msg or "inspection" in msg or "defect" in msg) and "order" in msg:

        write_triggers = ["add", "save", "update", "report", "log", "found", "passed"]

        if any(word in msg for word in write_triggers) and "what" not in msg and "show" not in msg:
            return {
                "intent": "add_quality_note",
                "order_id": extract_order_id(message),
                "note": message
            }

    # ================= QUALITY READ =================
    if ("quality" in msg or "note" in msg) and "order" in msg:

        read_triggers = ["what", "show", "get", "tell", "view"]

        if any(word in msg for word in read_triggers) or "?" in msg:
            return {
                "intent": "get_quality_note",
                "order_id": extract_order_id(message)
            }

    # ================= FILTER ORDERS =================
    if "show" in msg or "list" in msg:
        if "accepted" in msg:
            return {"intent": "filter_orders", "status": "Accepted"}
        if "completed" in msg:
            return {"intent": "filter_orders", "status": "Completed"}
        if "in review" in msg:
            return {"intent": "filter_orders", "status": "In Review"}
        return {"intent": "get_all_orders"}

    # ================= STATUS UPDATE =================
    if "change" in msg or "update" in msg or "order" in msg:

        status_map = {
            "in review": "In Review",
            "review": "In Review",
            "accepted": "Accepted",
            "completed": "Completed",
            "complete": "Completed",
            "received": "Received"
        }

        for key, value in status_map.items():
            if key in msg:
                return {
                    "intent": "update_status",
                    "order_id": extract_order_id(message),
                    "status": value
                }

    # ================= CREATE ORDER =================
    if "need" in msg or "require" in msg or "by" in msg:

        qty = re.findall(r"\d+", message)
        quantity = int(qty[0]) if qty else 1

        material = "Unknown"

        if "copper" in msg:
            material = "Copper"
        elif "titanium" in msg:
            material = "Titanium"
        elif "steel" in msg:
            material = "Steel"
        elif "aluminum" in msg:
            material = "Aluminum"

        return {
            "intent": "create_order",
            "part_name": message,
            "material": material,
            "quantity": quantity,
            "deadline": ""
        }

    return {"intent": "unknown"}
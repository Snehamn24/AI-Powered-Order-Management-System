import re

def parse_message(message: str):

    msg = message.lower().strip()

    # ================= DELETE ORDER =================
    if "delete order" in msg or "remove order" in msg:
        order_id = re.findall(r"\d+", message)
        return {
            "intent": "delete_order",
            "order_id": int(order_id[0]) if order_id else None
        }

    # ================= CHANGE STATUS (FIXED MAIN BUG) =================
    if "change" in msg and "status" in msg:

        order_id = re.findall(r"\d+", message)

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
                    "order_id": int(order_id[0]) if order_id else None,
                    "status": value
                }

    # ================= UPDATE STATUS (SHORT FORM) =================
    if "order" in msg:

        order_id = re.findall(r"\d+", message)

        status_map = {
            "in review": "In Review",
            "review": "In Review",
            "accepted": "Accepted",
            "completed": "Completed"
        }

        for key, value in status_map.items():
            if key in msg:
                return {
                    "intent": "update_status",
                    "order_id": int(order_id[0]) if order_id else None,
                    "status": value
                }

    # ================= GET STATUS =================
    if "status" in msg and "order" in msg:
        order_id = re.findall(r"\d+", message)
        return {
            "intent": "get_order_status",
            "order_id": int(order_id[0]) if order_id else None
        }

    # ================= QUALITY =================
    if "quality" in msg or "inspection" in msg:
        order_id = re.findall(r"\d+", message)
        return {
            "intent": "add_quality_note",
            "order_id": int(order_id[0]) if order_id else None,
            "note": message
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
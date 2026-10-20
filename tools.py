import json
import re
from pathlib import Path
from datetime import datetime
from decimal import Decimal


DATA_DIR = Path(__file__).resolve().parent / "data"
CURRENT_TIME = datetime.fromisoformat("2026-06-10T09:00:00+02:00")

def get_booking(booking_id: str) -> dict:
    bookings_path = DATA_DIR / "bookings.json"
    bookings = json.loads(bookings_path.read_text(encoding="utf-8"))

    for booking in bookings:
        if booking["id"] == booking_id:
            return {"found": True, "booking": booking}

    return {"found": False, "booking_id": booking_id}


def calculate_refund(booking_id: str) -> dict:
    result = get_booking(booking_id)

    if not result["found"]:
        return result

    booking = result["booking"]

    if booking["status"] != "confirmed":
        return {
            "booking_id": booking_id,
            "status": booking["status"],
            "can_cancel": False,
            "total_refund_eur": "0.00",
            "reason": (
                f"Booking status is '{booking['status']}'. "
                "Only confirmed bookings can be cancelled. "
                "No additional refund is available."
            ),
        }

    start = datetime.fromisoformat(booking["start"])
    hours_before_start = (start - CURRENT_TIME).total_seconds() / 3600

    if hours_before_start >= 48:
        rate = Decimal("1")
    elif hours_before_start >= 24:
        rate = Decimal("0.5")
    else:
        rate = Decimal("0")

    rental = Decimal(str(booking["rental_price_eur"]))
    deposit = Decimal(str(booking["deposit_eur"]))
    rental_refund = (rental * rate).quantize(Decimal("0.01"))
    total_refund = rental_refund + deposit

    return {
        "booking_id": booking_id,
        "status": booking["status"],
        "can_cancel": True,
        "rental_refund_eur": str(rental_refund),
        "deposit_refund_eur": str(deposit.quantize(Decimal("0.01"))),
        "total_refund_eur": str(total_refund.quantize(Decimal("0.01"))),
        "refund_method": booking["paid_with"],
        "currency": "EUR",
    }

STOP_WORDS = set("""
a an the and or of for to in on at by with from is are was be do does can
could would will should i my me you your we our it its have has how what
when where which please tell about citywheels rent
""".split())


def policy_words(text: str) -> set:
    text = re.sub(r"\be[- ]?bikes?\b", "electric bike", text.lower())
    text = re.sub(r"\b\d+[- ]years?[- ]old\b", "age", text)
    aliases = {"bikes": "bike", "helmets": "helmet", "ages": "age",
               "years": "age", "year": "age", "daily": "day", "hours": "hour"}
    return {aliases.get(word, word) for word in re.findall(r"\w+", text)
            if word not in STOP_WORDS}


def search_policies(query: str) -> dict:
    query_words = policy_words(query)

    if not query_words:
        return {"matches": []}

    matches = []

    for path in sorted((DATA_DIR / "policies").glob("*.md")):
        text = path.read_text(encoding="utf-8")

        for section in text.split("\n## "):
            section_words = policy_words(section)
            # Headings identify the rule; generic words in long sections should not outrank them.
            heading_words = policy_words(section.splitlines()[0]) if section.strip() else set()
            score = len(query_words & section_words) + 2 * len(query_words & heading_words)

            if score > 0:
                matches.append({
                    "source": path.name,
                    "text": section.strip(),
                    "score": score,
                })

    matches.sort(key=lambda match: match["score"], reverse=True)

    return {"matches": matches[:3]}

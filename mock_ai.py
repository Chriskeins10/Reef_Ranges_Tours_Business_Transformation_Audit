"""
Mock AI qualification engine for Reef & Ranges Tours Enquiry Assistant.
Uses simple rule-based + keyword extraction to simulate an LLM.
In production this would call a real LLM with structured output.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def load_tours() -> List[Dict]:
    with open(DATA_DIR / "tours.json") as f:
        return json.load(f)

def load_bookings() -> List[Dict]:
    with open(DATA_DIR / "bookings.json") as f:
        return json.load(f)

def save_bookings(bookings: List[Dict]) -> None:
    with open(DATA_DIR / "bookings.json", "w") as f:
        json.dump(bookings, f, indent=2)

TOUR_KEYWORDS = {
    "GBR-FULL": ["full day reef", "full day great barrier", "full reef", "outer reef full", "full day snorkel"],
    "GBR-HALF": ["half day reef", "half day great barrier", "half reef", "half day snorkel", "morning reef"],
    "DAINTREE": ["daintree", "cape tribulation", "rainforest", "cape trib"],
    "KURANDA": ["kuranda", "skyrail", "scenic railway", "kuranda railway"],
    "WATERFALLS": ["waterfall", "tablelands", "atherton", "crater lake", "millaa"]
}

DATE_PATTERNS = [
    r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",          # 22/10/2026 or 22-10-26
    r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{2,4})?",
    r"(tomorrow|today|next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday))",
    r"(this|next)\s+(weekend|week)",
]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}


def extract_party_size(text: str) -> Optional[int]:
    text = text.lower()
    # Common patterns: "2 people", "party of 4", "for 3", "we are 5", "family of 6"
    patterns = [
        r"(?:party of|for|we are|group of|family of|there are|there will be)\s+(\d+)",
        r"(\d+)\s+(?:people|persons|guests|adults|pax|travellers|travelers)",
        r"(\d+)\s*(?:adults?)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            size = int(m.group(1))
            if 1 <= size <= 20:
                return size
    # Lone number near booking words
    m = re.search(r"\b(\d+)\b", text)
    if m and any(w in text for w in ["book", "people", "us", "me and", "party"]):
        size = int(m.group(1))
        if 1 <= size <= 20:
            return size
    return None


def extract_tour_id(text: str) -> Optional[str]:
    text_lower = text.lower()
    scores = {}
    for tour_id, keywords in TOUR_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[tour_id] = score
    if not scores:
        # Broader fallbacks
        if any(w in text_lower for w in ["reef", "snorkel", "great barrier", "diving"]):
            return "GBR-FULL"  # default to full day
        if any(w in text_lower for w in ["rainforest", "jungle"]):
            return "DAINTREE"
        return None
    return max(scores, key=scores.get)


def extract_date(text: str) -> Optional[str]:
    """Return ISO date string YYYY-MM-DD or None."""
    text_lower = text.lower().strip()
    today = datetime(2026, 10, 20)  # fixed "today" for reproducibility in demo

    if "tomorrow" in text_lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if "today" in text_lower:
        return today.strftime("%Y-%m-%d")

    # Weekend
    if "this weekend" in text_lower or "next weekend" in text_lower:
        # Next Saturday
        days_ahead = 5 - today.weekday()  # Saturday = 5
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # dd/mm/yyyy or dd-mm-yyyy
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # "22 October" or "22nd October 2026"
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))?",
        text_lower
    )
    if m:
        d = int(m.group(1))
        mo = MONTHS[m.group(2)]
        y = int(m.group(3)) if m.group(3) else 2026
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def extract_special_needs(text: str) -> str:
    text_lower = text.lower()
    needs = []
    if any(w in text_lower for w in ["vegetarian", "vegan", "gluten", "dairy free", "allergy", "allergies"]):
        needs.append("Dietary requirement mentioned")
    if any(w in text_lower for w in ["wheelchair", "mobility", "disabled", "accessibility", "access"]):
        needs.append("Accessibility / mobility need")
    if any(w in text_lower for w in ["child", "children", "kids", "family", "baby", "infant"]):
        needs.append("Travelling with children")
    if any(w in text_lower for w in ["pregnant", "pregnancy"]):
        needs.append("Pregnancy noted")
    return "; ".join(needs) if needs else "None stated"


def extract_name_email(text: str) -> Dict[str, Optional[str]]:
    # Very simple extraction
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    email = email_match.group(0) if email_match else None

    # Name patterns: "my name is X", "I'm X", "this is X"
    name = None
    m = re.search(r"(?:my name is|i am|i'm|this is|name[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text, re.IGNORECASE)
    if m:
        name = m.group(1).title()
    return {"name": name, "email": email}


def check_availability(tour_id: str, date: str, party_size: int) -> Dict[str, Any]:
    tours = {t["id"]: t for t in load_tours()}
    if tour_id not in tours:
        return {"available": False, "reason": "Unknown tour", "remaining": 0}

    tour = tours[tour_id]
    bookings = load_bookings()
    booked = sum(
        b["party_size"]
        for b in bookings
        if b["tour_id"] == tour_id and b["date"] == date and b["status"] in ("confirmed", "provisional")
    )
    remaining = tour["max_capacity"] - booked
    available = remaining >= party_size
    return {
        "available": available,
        "remaining": remaining,
        "max_capacity": tour["max_capacity"],
        "reason": "OK" if available else f"Only {remaining} places left (need {party_size})"
    }


def qualify_enquiry(user_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Main mock AI entry point.
    Returns a structured qualification result that the UI can act on.
    """
    conversation_history = conversation_history or []
    full_text = " ".join([m.get("content", "") for m in conversation_history] + [user_message])

    tour_id = extract_tour_id(full_text)
    date = extract_date(full_text)
    party_size = extract_party_size(full_text)
    special = extract_special_needs(full_text)
    contact = extract_name_email(full_text)

    missing = []
    if not tour_id:
        missing.append("which tour you are interested in")
    if not date:
        missing.append("preferred date")
    if not party_size:
        missing.append("number of people")

    result = {
        "tour_id": tour_id,
        "date": date,
        "party_size": party_size,
        "special_needs": special,
        "customer_name": contact["name"],
        "email": contact["email"],
        "missing_fields": missing,
        "confidence": "high" if not missing else ("medium" if len(missing) <= 1 else "low"),
        "raw_message": user_message
    }

    if tour_id and date and party_size:
        avail = check_availability(tour_id, date, party_size)
        result["availability"] = avail
        result["can_book"] = avail["available"]
    else:
        result["availability"] = None
        result["can_book"] = False

    return result


def generate_reply(qualification: Dict[str, Any], tours: List[Dict] = None) -> str:
    """Generate a natural-sounding reply based on the qualification result."""
    tours = tours or load_tours()
    tour_map = {t["id"]: t for t in tours}

    if qualification["missing_fields"]:
        missing_str = ", ".join(qualification["missing_fields"])
        return (
            f"Thanks for getting in touch with Reef & Ranges Tours! "
            f"To help you further I still need: **{missing_str}**. "
            f"Could you please provide those details?"
        )

    tour = tour_map.get(qualification["tour_id"])
    tour_name = tour["name"] if tour else qualification["tour_id"]
    date = qualification["date"]
    size = qualification["party_size"]
    avail = qualification.get("availability", {})

    if qualification.get("can_book"):
        return (
            f"Great news! I can provisionally hold **{size} place(s)** on the "
            f"**{tour_name}** for **{date}**. "
            f"There are currently {avail.get('remaining', '?')} spots remaining. "
            f"Would you like me to create a provisional booking? "
            f"Please reply with your full name and email address to confirm."
        )
    else:
        reason = avail.get("reason", "insufficient availability")
        return (
            f"Thank you for your interest in the **{tour_name}** on **{date}**. "
            f"Unfortunately we cannot accommodate a party of {size} on that date "
            f"({reason}). "
            f"Would you like to try a different date or another tour? "
            f"I can also put you on a waitlist and have a team member contact you."
        )


def create_provisional_booking(qualification: Dict[str, Any]) -> Dict[str, Any]:
    """Create a provisional booking record from a complete qualification."""
    bookings = load_bookings()
    next_id = max((int(b["booking_id"].split("-")[1]) for b in bookings), default=1000) + 1
    booking = {
        "booking_id": f"BK-{next_id}",
        "tour_id": qualification["tour_id"],
        "date": qualification["date"],
        "party_size": qualification["party_size"],
        "customer_name": qualification.get("customer_name") or "Guest",
        "email": qualification.get("email") or "not-provided@example.com",
        "status": "provisional",
        "special_needs": qualification.get("special_needs", "None"),
        "created_at": datetime.utcnow().isoformat(timespec="seconds")
    }
    bookings.append(booking)
    save_bookings(bookings)
    return booking

"""
Reef & Ranges Tours – LLM Agent (APInex)
Uses OpenAI-compatible Chat Completions + tool calling via APInex.
Falls back to the deterministic mock if no API key is set.
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from openai import OpenAI

# Re-use data helpers from the original mock module
from mock_ai import (
    load_tours, load_bookings, save_bookings,
    check_availability, create_provisional_booking as _create_booking
)

DATA_DIR = Path(__file__).parent / "data"

# -----------------------------------------------------------------------------
# APInex configuration
# -----------------------------------------------------------------------------
APINEX_BASE_URL = "https://api.apinex.bond/v1"
# Prefer a free model; user can override with APINEX_MODEL env var
DEFAULT_MODEL = os.getenv("APINEX_MODEL", "free/deepseek-v4.1-flash")

def get_client() -> Optional[OpenAI]:
    """Return an OpenAI client pointed at APInex, or None if no key."""
    api_key = os.getenv("APINEX_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=APINEX_BASE_URL)


# -----------------------------------------------------------------------------
# Tools the agent can call
# -----------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_tours",
            "description": "List all available day tours with prices and capacity.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check remaining capacity for a specific tour on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tour_id": {
                        "type": "string",
                        "description": "Tour ID, e.g. GBR-FULL, GBR-HALF, DAINTREE, KURANDA, WATERFALLS"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Number of people in the party"
                    }
                },
                "required": ["tour_id", "date", "party_size"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_provisional_booking",
            "description": "Create a provisional (not yet paid) booking. Only call when you have tour_id, date, party_size, customer_name and email, and availability has been confirmed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tour_id": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "party_size": {"type": "integer"},
                    "customer_name": {"type": "string"},
                    "email": {"type": "string"},
                    "special_needs": {"type": "string", "description": "Any dietary, accessibility or other notes"}
                },
                "required": ["tour_id", "date", "party_size", "customer_name", "email"]
            }
        }
    }
]


def _exec_tool(name: str, args: Dict[str, Any]) -> str:
    """Execute a tool and return a JSON string result for the model."""
    try:
        if name == "list_tours":
            tours = load_tours()
            return json.dumps(tours, indent=2)

        if name == "check_availability":
            result = check_availability(
                args["tour_id"],
                args["date"],
                int(args["party_size"])
            )
            return json.dumps(result)

        if name == "create_provisional_booking":
            # Re-check availability before creating
            avail = check_availability(
                args["tour_id"],
                args["date"],
                int(args["party_size"])
            )
            if not avail.get("available"):
                return json.dumps({
                    "success": False,
                    "error": avail.get("reason", "Not enough capacity")
                })

            qual = {
                "tour_id": args["tour_id"],
                "date": args["date"],
                "party_size": int(args["party_size"]),
                "customer_name": args["customer_name"],
                "email": args["email"],
                "special_needs": args.get("special_needs", "None")
            }
            booking = _create_booking(qual)
            return json.dumps({"success": True, "booking": booking})

        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


SYSTEM_PROMPT = """You are the friendly booking assistant for Reef & Ranges Tours, a day-tour operator in Cairns, Australia.

Your job is to help customers enquire about and provisionally book day tours.

Available tours (use list_tours tool for full details):
- GBR-FULL: Great Barrier Reef Full Day ($249)
- GBR-HALF: Great Barrier Reef Half Day ($179)
- DAINTREE: Daintree Rainforest & Cape Tribulation ($219)
- KURANDA: Kuranda Scenic Railway & Skyrail ($159)
- WATERFALLS: Atherton Tablelands Waterfalls ($189)

Rules you MUST follow:
1. Be warm, concise and professional. Use Australian English.
2. Always gather: preferred tour, date (YYYY-MM-DD), party size, full name and email before creating a booking.
3. ALWAYS call check_availability before offering to book.
4. Only call create_provisional_booking when you have ALL of: tour_id, date, party_size, customer_name, email AND availability is confirmed.
5. Never invent availability, prices or pickup times. Use the tools.
6. Provisional bookings are NOT final. Tell the customer a human will confirm and arrange payment.
7. If the customer asks something outside tours/bookings (weather, medical advice, etc.), politely say a team member will follow up.
8. If you are unsure, ask a clarifying question instead of guessing.
9. Today's date for reference is 20 October 2026.

When you need information from the system, call the appropriate tool. Do not pretend to know live availability.
"""


def run_agent(user_message: str, conversation_history: List[Dict[str, str]]) -> str:
    """
    Run one turn of the agent.
    conversation_history: list of {"role": "user"|"assistant", "content": "..."}
    Returns the assistant's final text reply.
    """
    client = get_client()

    # Fallback to deterministic mock if no API key
    if client is None:
        from mock_ai import qualify_enquiry, generate_reply
        qual = qualify_enquiry(user_message, conversation_history)
        # Simple confirm handling
        lower = user_message.lower()
        if any(p in lower for p in ["yes", "confirm", "book it", "please book", "go ahead"]) and qual.get("can_book"):
            if qual.get("customer_name") and qual.get("email"):
                booking = _create_booking(qual)
                return (
                    f"✅ Provisional booking created!\n\n"
                    f"- Booking ID: `{booking['booking_id']}`\n"
                    f"- Tour: {qual['tour_id']}\n"
                    f"- Date: {qual['date']}\n"
                    f"- Party size: {qual['party_size']}\n"
                    f"- Name: {booking['customer_name']}\n"
                    f"- Email: {booking['email']}\n\n"
                    f"A team member will review and send final confirmation shortly."
                )
        return generate_reply(qual)

    # Build messages for the LLM
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # Tool-calling loop (max 5 rounds to avoid runaway)
    for _ in range(5):
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=800
        )
        choice = response.choices[0]
        msg = choice.message

        # If the model wants to call tools
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = _exec_tool(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
            continue  # let the model see the tool results

        # Final text response
        return msg.content or "Sorry, I couldn't generate a reply. Please try again or contact the team."

    return "I'm having trouble completing that request. A team member will follow up with you shortly."

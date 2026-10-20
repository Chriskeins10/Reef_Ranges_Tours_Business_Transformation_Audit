"""
Reef & Ranges Tours – Enquiry & Booking Assistant (MVP)
Chat interface + LLM agent (APInex) with tool calling.
Falls back to deterministic mock when no API key is present.
"""

import streamlit as st
import os
from pathlib import Path
from agent import run_agent, get_client, DEFAULT_MODEL
from mock_ai import load_tours, load_bookings

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Reef & Ranges Tours | Enquiry Assistant",
    page_icon="🪸",
    layout="centered",
    initial_sidebar_state="expanded"
)

STAFF_PASSWORD = "reef2026"  # demo only

# -----------------------------------------------------------------------------
# Session helpers
# -----------------------------------------------------------------------------
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Welcome to **Reef & Ranges Tours**! 🪸\n\n"
                    "I can help you enquire about our day tours:\n"
                    "- Great Barrier Reef (Full or Half Day)\n"
                    "- Daintree Rainforest & Cape Tribulation\n"
                    "- Kuranda Scenic Railway & Skyrail\n"
                    "- Atherton Tablelands Waterfalls\n\n"
                    "Just tell me which tour you’re interested in, your preferred date, "
                    "and how many people. I’ll check availability for you."
                )
            }
        ]
    if "staff_logged_in" not in st.session_state:
        st.session_state.staff_logged_in = False


def render_chat():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def handle_user_input(user_text: str):
    st.session_state.messages.append({"role": "user", "content": user_text})

    # Build history for the agent (exclude the latest user message – it is passed separately)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    with st.spinner("Thinking…"):
        reply = run_agent(user_text, history)

    st.session_state.messages.append({"role": "assistant", "content": reply})


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
def sidebar():
    with st.sidebar:
        st.title("🪸 Reef & Ranges")
        st.caption("Enquiry & Booking Assistant (MVP)")
        st.divider()

        # LLM status
        client = get_client()
        if client:
            st.success(f"LLM: APInex · `{DEFAULT_MODEL}`")
        else:
            st.warning("No APINEX_API_KEY set – using deterministic mock")
            st.caption("Set the env var or Streamlit secret to enable the real agent.")

        st.divider()
        st.subheader("Staff Login")
        if not st.session_state.staff_logged_in:
            pwd = st.text_input("Password", type="password", key="staff_pwd")
            if st.button("Login"):
                if pwd == STAFF_PASSWORD:
                    st.session_state.staff_logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
            st.caption("Demo password: `reef2026`")
        else:
            st.success("Logged in as staff")
            if st.button("Logout"):
                st.session_state.staff_logged_in = False
                st.rerun()

            st.divider()
            st.subheader("Current Bookings (Synthetic)")
            bookings = load_bookings()
            for b in sorted(bookings, key=lambda x: x["date"], reverse=True)[:12]:
                status_emoji = "🟢" if b["status"] == "confirmed" else "🟡"
                st.markdown(
                    f"{status_emoji} **{b['booking_id']}** – {b['tour_id']}  \n"
                    f"{b['date']} · {b['party_size']} pax · {b['customer_name']}"
                )

            st.divider()
            st.subheader("Tours & Capacity")
            for t in load_tours():
                st.markdown(f"**{t['name']}**  \nMax {t['max_capacity']} · ${t['price_aud']} AUD")

        st.divider()
        st.markdown("**Synthetic data only**  \nNo real customer information is stored or used.")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    init_session()
    sidebar()

    st.title("Chat with our Tour Assistant")
    st.caption("Ask about tours, dates and availability. All data is synthetic.")

    render_chat()

    if prompt := st.chat_input("Type your enquiry here…"):
        handle_user_input(prompt)
        st.rerun()


if __name__ == "__main__":
    main()

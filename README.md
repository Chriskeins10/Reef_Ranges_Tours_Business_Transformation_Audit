# Reef & Ranges Tours – Enquiry & Booking Assistant (MVP)

**Part 2 of the Getup Solutions AI Digital Transformation Specialist Practical Assessment**

A working Streamlit prototype that addresses the #1 opportunity from the Business Transformation Audit: an AI-assisted enquiry capture, qualification and booking assistant.

## What it does

- Simple **chat interface** for customers
- **LLM agent** (via APInex – OpenAI-compatible API) with **tool calling**:
  - `list_tours`
  - `check_availability`
  - `create_provisional_booking`
- Falls back to a deterministic mock AI when no API key is present (so the demo always works)
- Synthetic availability checking (prevents double-booking in the demo)
- Creates **provisional bookings only** – final confirmation stays human
- Staff login to view bookings & capacity
- Synthetic data only

## LLM provider: APInex

- Base URL: `https://api.apinex.bond/v1`
- Default model: `free/deepseek-v4.1-flash` (free tier)
- Override with env var `APINEX_MODEL`
- API key via `APINEX_API_KEY` (or `OPENAI_API_KEY`)

You must use **your own** APInex account / free-tier key. Never commit keys.

## Quick start (local)

```bash
cd reef-ranges-mvp
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional – enable real LLM agent
export APINEX_API_KEY="sk-apx-your-key-here"
# export APINEX_MODEL="free/gpt-6-luna"   # optional override

streamlit run app.py
```

Open the URL shown (usually http://localhost:8501).

**Staff demo password:** `reef2026`

## Deploy for a public link (free)

1. Push this repository to your own GitHub account (real commit history is already present).
2. Go to [share.streamlit.io](https://share.streamlit.io) → Deploy → select the repo → main file `app.py`.
3. In Streamlit Cloud secrets add:
   ```
   APINEX_API_KEY = "sk-apx-your-key"
   ```
4. You receive a public URL to submit.

## Project structure

```
reef-ranges-mvp/
├── app.py                 # Streamlit chat UI + staff sidebar
├── agent.py               # LLM agent (APInex) + tool calling loop
├── mock_ai.py             # Deterministic fallback + shared data helpers
├── data/
│   ├── tours.json
│   └── bookings.json
├── tests/
│   └── test_mock_ai.py
├── requirements.txt
├── README.md
├── AI_USE_NOTE.md
└── .streamlit/config.toml
```

## Running the tests

```bash
pytest tests/ -v
```

(The unit tests cover the deterministic extraction & availability logic used by both the mock and the agent tools.)

## Safety & human-in-the-loop

- The agent **never** finalises a paid booking.
- It must call `check_availability` before offering a booking.
- Provisional bookings require name + email and are clearly labelled.
- Staff can always see the full booking list and intervene.
- If the LLM or API is unavailable, the app falls back to the mock or asks the user to contact the team.
- All data is synthetic.

## Design decisions

- **APInex** chosen because it is OpenAI-compatible, offers free models, and keeps the integration simple (one base URL + key).
- **Tool calling** (not pure prompt engineering) so availability and booking creation are grounded in real data instead of hallucinated.
- **Fallback mock** so assessors can run the app without an API key.
- Streamlit for rapid UI and free public hosting.

---

Built for the Getup Solutions practical assessment – October 2026.  
Synthetic data only. No real customer or company data used.

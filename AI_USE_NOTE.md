# AI-Use Note – Part 2 MVP (LLM Agent version)

**Candidate assessment – Reef & Ranges Tours Enquiry & Booking Assistant**

## Tools used

- **Grok (xAI)** – for architecture decisions, agent tool design, system prompt, Streamlit UI scaffolding, README and this note.
- **APInex** (https://api.apinex.bond) – OpenAI-compatible LLM API used at runtime for the agent (default free model: `free/deepseek-v4.1-flash`).
- Standard OpenAI Python SDK pointed at the APInex base URL.
- No other AI coding assistants were used for the final code.

## Main prompts / instructions given to the AI (Grok)

Typical instructions included:

- “Upgrade the Streamlit MVP from a pure mock AI to an LLM agent that uses APInex (OpenAI-compatible) with tool calling for list_tours, check_availability and create_provisional_booking.”
- “Keep a deterministic mock fallback so the app still works with no API key.”
- “System prompt must enforce: never invent availability, always check before booking, provisional only, gather name + email, Australian English, escalate edge cases.”
- “Update README and AI-use note accordingly. Never hard-code or commit API keys.”

## What the AI got wrong or incomplete (and what I changed)

1. **Tool-calling loop** – Early drafts risked infinite loops or dropped tool results. I limited the loop to 5 rounds and ensured every tool response is appended correctly before the next LLM call.
2. **Availability safety** – The model sometimes wanted to create a booking without re-checking capacity. I added an explicit re-check inside the `create_provisional_booking` tool itself.
3. **Fallback behaviour** – The first version broke when no key was present. I restored a clean path that re-uses the original deterministic `mock_ai` functions.
4. **System prompt length / tone** – Generated prompt was too verbose and allowed final paid bookings. I shortened it and hard-coded the “provisional only + human confirmation” rule.
5. **Model choice** – Suggested paid models by default. I switched the default to a free APInex model (`free/deepseek-v4.1-flash`) and documented how to override.

## What I reviewed and wrote / decided myself

- Choice of APInex as the LLM provider and the free-model default.
- Exact tool schemas and the safety re-check inside the booking tool.
- System prompt rules that keep a human in the loop for final confirmation and edge cases.
- Fallback architecture so the submission always runs.
- All unit tests (still focused on the shared data/availability logic).
- Final wording of user-facing messages and the staff password.
- README structure and this AI-use note.

## Runtime behaviour

- If `APINEX_API_KEY` (or `OPENAI_API_KEY`) is set → real LLM agent with tool calling via APInex.
- If no key → deterministic mock (same behaviour as the previous version of this MVP).
- No API keys are stored in the repository.

## Summary

AI accelerated the agent scaffolding, tool definitions and documentation. Every decision that affects booking safety, availability grounding, fallback behaviour or customer-facing language was reviewed and finalised by me. The running application either calls APInex with explicit tools or falls back to fully deterministic code.

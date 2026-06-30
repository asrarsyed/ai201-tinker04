from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """\
You are a home repair safety classifier. Your job is to classify a homeowner's repair question into exactly one of three tiers: safe, caution, or refuse.

Tier definitions:
- safe: A repair where a mistake produces only cosmetic damage or a broken fixture — no risk of fire, flooding, injury, or structural failure, and no permit or license is required.
- caution: A repair involving an existing water or electrical fixture swapped like-for-like at the same location, where a mistake could cause real property damage or mild injury but not fire, flooding, structural failure, or death.
- refuse: A repair where a mistake could cause fire, flooding, structural failure, serious injury, or death — or where local codes require a licensed professional and a permit.

Examples:
Q: How do I patch a small hole in my drywall?
TIER: safe | REASON: Patching small drywall holes risks only cosmetic damage and requires no permit or licensed professional.

Q: How do I replace my bathroom faucet?
TIER: caution | REASON: Replacing an existing faucet is a like-for-like swap that risks water damage but not fire, flooding, or structural failure.

Q: How do I add a new outlet to my garage?
TIER: refuse | REASON: Adding a new outlet requires running a new circuit from the panel, which is a fire hazard and requires a permit and licensed electrician.

Key rules:
- "Replacing" an existing fixture at the same location = caution. "Adding" a new fixture or circuit anywhere = refuse.
- Any gas line question = refuse, no exceptions.
- Any wall removal question = refuse unless a structural engineer has already confirmed non-load-bearing.
- When ambiguous, classify as the more restrictive tier.

Reason step by step before answering, but output ONLY this line — no other text:
TIER: <safe|caution|refuse> | REASON: <one sentence>\
"""

_FALLBACK = {"tier": "refuse", "reason": "Classification failed; defaulting to refuse for safety."}


def classify_safety_tier(question: str) -> dict:
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}"},
        ],
    )
    raw = response.choices[0].message.content.strip()

    try:
        tier_part, reason_part = raw.split(" | ", 1)
        tier = tier_part.split(": ", 1)[1].strip().lower()
        reason = reason_part.split(": ", 1)[1].strip()
    except (ValueError, IndexError):
        return _FALLBACK

    if tier not in VALID_TIERS:
        return _FALLBACK

    return {"tier": tier, "reason": reason}

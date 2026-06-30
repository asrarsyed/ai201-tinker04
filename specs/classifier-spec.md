# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Complete — implemented and verified

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
A repair is safe if a mistake produces only cosmetic damage or a broken fixture — no risk of fire, flooding, injury, or structural failure, and no permit or license is required.
```

**caution:**
```
A repair is caution if it involves an existing water or electrical fixture being swapped like-for-like at the same location, where a mistake could cause real property damage or mild injury but not fire, flooding, structural failure, or death.
```

**refuse:**
```
A repair is refuse if a mistake could cause fire, flooding, structural failure, serious injury, or death — or if local codes require a licensed professional and a permit (e.g., panel work, new circuits, gas lines, load-bearing walls, water heaters, new plumbing runs).
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
Provide the LLM with the three tier definitions plus three few-shot examples (one per tier). Ask it to reason step-by-step internally before outputting the tier, but only emit the structured output line — no prose. For genuinely ambiguous questions (e.g., "can I replace my own outlets?"), the few-shot example for replacing an existing outlet (caution) vs. adding a new outlet (refuse) anchors the boundary; if still ambiguous after applying the rule, classify as the more restrictive tier.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
TIER: <tier> | REASON: <one sentence>

Example: TIER: caution | REASON: Replacing an existing faucet is a like-for-like swap that risks water damage but not fire or flooding.

This format splits unambiguously on " | " then on ": " for each field. No newlines inside the response. If the LLM deviates, the parser treats it as a parse failure and triggers fallback.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
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
TIER: <safe|caution|refuse> | REASON: <one sentence>
```

**User message:**
```
Question: {question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Rule: If the work requires opening a breaker panel, running new wire or pipe to a new location, touching a gas line, removing a wall, or obtaining a permit — it is refuse; if it is a component swap at an existing, already-wired or already-plumbed location — it is caution.

Example 1 (caution): "How do I replace the GFCI outlet in my bathroom?" — existing outlet, same location, same circuit; a wiring mistake trips the breaker, which is recoverable.

Example 2 (refuse): "How do I add an outlet to my unfinished basement?" — requires a new circuit from the panel, new wire run through the wall, and a permit; an amateur mistake creates a latent fire hazard.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
If the LLM response cannot be parsed into the expected TIER/REASON format, or if the extracted tier is not in VALID_TIERS, return {"tier": "refuse", "reason": "Classification failed; defaulting to refuse for safety."}. Failing closed to refuse is correct here because the risk of silently approving a dangerous repair far outweighs the cost of a false refusal — the user can always call a professional.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
No surprises on the first three test questions they all matched the few-shot examples exactly. The few-shot examples were drawn directly from the tier guide, so the model had no ambiguity to resolve.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
No prompt changes were needed. The first run produced correctly structured TIER: X | REASON: Y output for all three test cases, parsed cleanly, and returned the expected tiers. The few-shot examples and explicit output format instruction were sufficient on the first attempt.
```

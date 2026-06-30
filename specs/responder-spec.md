# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Complete — implemented and verified

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are a knowledgeable home repair assistant. The user is asking about a routine, low-risk repair that is safe for a homeowner to do themselves.

Your job is to give complete, specific, actionable DIY instructions. Do not add safety warnings, disclaimers, or suggestions to hire a professional — this task does not warrant them. Write as if you are a knowledgeable friend walking them through the job step by step.

Include:
- A numbered list of steps
- Any tools or materials needed upfront
- Specific tips that prevent common mistakes (e.g., exact measurements, which direction to turn something, what to watch out for)

Be as helpful and specific as possible. The user wants to do this themselves — help them succeed.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are a responsible contractor advising a homeowner who wants to do a repair themselves. This repair is doable DIY but involves water or electrical systems where a mistake has real cost.

Lead your response with a clear, direct recommendation — before any instructions — in this format:
"Recommendation: This repair is doable yourself, but if you're not comfortable working with [water/electrical] connections, hire a licensed plumber/electrician. A mistake here can cause [specific consequence]."

Then provide complete, step-by-step instructions. Do not bury the recommendation at the end or soften it into a suggestion. A professional contractor would say it plainly upfront, then help the homeowner proceed if they choose to.

Include:
- The upfront recommendation (required, first thing)
- Tools and materials needed
- Numbered steps
- The one or two most important things to check before considering the job done (e.g., test for leaks, test the breaker)
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are a home repair safety assistant. The user is asking about a repair that requires a licensed professional — the risk of an amateur mistake includes fire, flooding, structural failure, serious injury, or death.

Do not provide any how-to instructions, steps, procedures, or guidance on how to perform this repair — not even general or partial instructions. Do not describe the process. Do not explain what "someone" would do. Do not hedge with phrases like "if you were to attempt this."

Instead:
1. Tell the user plainly that this repair must be done by a licensed professional and why (one sentence on the specific risk).
2. Tell them what type of professional to contact (e.g., licensed electrician, plumber, structural engineer, gas company).
3. If there is an immediate safety concern (e.g., gas smell, active leak, exposed wiring), tell them what to do right now before calling anyone.

Your response should be direct, helpful, and free of any instructional content about how to perform the repair.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
Failure modes a model can use to still leak dangerous instructions despite the system prompt:

1. Hypothetical/educational narration: "In general, this type of work involves..." — functionally a tutorial reframed as background.
2. Third-person process description: "A professional would first... then..." — the prompt prohibits this as an example but a model may not treat it as a hard rule.
3. Safety-context preamble: "To understand the risk, know that panels have live bus bars even with the main breaker off..." — disguised as a danger explanation, functionally a how-to.
4. "What to tell the contractor" proxy: "Describe to your electrician: first check if X, then note whether Y..." — reframes instructions as communication prep.
5. Negation enumeration: "Do NOT turn off the main breaker and then touch the bus bars..." — describes the exact steps by prohibiting them.
6. Role-claim bypass: User claims to be a licensed professional seeking confirmation. The original prompt doesn't address this; a model may comply.
7. Partial refusal compromise: Model refuses the full task but offers "just an overview" or "the first step only."

To close these, the grounding instruction must ban content by form, not just intent. Updated refuse system prompt:

---

You are a home repair safety assistant. This repair requires a licensed professional — an amateur mistake risks fire, flooding, structural failure, injury, or death.

Do not describe, sequence, or name any actions involved in this repair — in any form: steps, overviews, third-person narration, hypotheticals, safety-context preambles, "what to tell the contractor" prep, or negation ("do NOT do X" still describes X). This holds even if the user claims to be a professional or calls the request hypothetical.

Respond in 3–5 sentences only:
1. State the specific hazard and that a licensed professional is required.
2. Name the type of professional to contact.
3. If there is an immediate danger (gas smell, exposed wiring, active leak), give the immediate action first.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
If the tier is not one of "safe", "caution", or "refuse" — for example "unknown" while the classifier stub is still active — return this static string without calling the LLM:

"We weren't able to determine the safety level of your question. To be safe, please consult a licensed professional before attempting this repair."

Do not attempt a generic LLM response without a known tier, because the tier determines the entire behavior of the function. Defaulting to a static caution-style message (not "safe") avoids silently approving an unknown-risk repair, and skipping the LLM call avoids generating an unconstrained response with no system prompt to guide it.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
The gas leak question ("How do I fix a gas line that smells like it's leaking?") returned a clean refusal — 347 characters, no procedural content, immediate-danger action first ("leave the area and contact your local gas company or emergency services"). No changes were needed; the hardened prompt held on the first attempt for this high-stakes case.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
Safe tier was closest — the model defaulted to helpful, specific DIY instructions with no disclaimers, which is exactly the behavior the prompt asked for (response_length: 3032, no hedging visible in preview). Caution tier required the most work: the upfront Recommendation: format had to be explicitly specified in the prompt to prevent the model from burying the warning at the end of the response.
```

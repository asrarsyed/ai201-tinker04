import json
import os
from datetime import datetime, timezone
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tier": tier,
        "question": question[:300],
        "question_length": len(question),
        "response_preview": response[:200],
        "response_length": len(response),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    q_preview = question[:60] + ("..." if len(question) > 60 else "")
    print(f'[LOGGED] tier={tier} | "{q_preview}" → {len(response)} chars')

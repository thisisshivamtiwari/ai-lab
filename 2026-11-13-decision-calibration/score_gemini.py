# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai==3.3.0"]
# ///
"""Gemini Decision 1 adapter. NOT RUN YET: no Gemini API key on this machine on 13 Nov 2026.

Written from the request example in Google's launch post (11 Nov 2026). The response is parsed defensively
because the post and Simon Willison's test show different type names ("noul" vs "yes_no"). google-genai 3.3.0
has a `client.decisions` resource; its argument names are unchecked until the first real run.

The key comes from the GEMINI_API_KEY environment variable and is never printed or written to results.

    uv run score_gemini.py
"""
import json
import os

from common import QUESTION, RESULTS, load_messages


def api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("Set GEMINI_API_KEY first (Google AI Studio has a no-cost tier for prototyping).")
    return key


def first_probability(obj):
    """Find the yes-probability in a decision answer, whatever the exact field layout turns out to be."""
    if isinstance(obj, dict):
        for key in ("probability", "yes_probability", "score", "confidence"):
            if isinstance(obj.get(key), (int, float)):
                return float(obj[key])
        for value in obj.values():
            found = first_probability(value)
            if found is not None:
                return found
    if isinstance(obj, list):
        for value in obj:
            found = first_probability(value)
            if found is not None:
                return found
    return None


def main():
    from google import genai

    client = genai.Client(api_key=api_key(), http_options={"api_version": "v1beta"})
    probs, raw = {}, {}
    for m in load_messages():
        result = client.decisions.create(
            model="gemini-decision-1",
            input=[{"type": "text", "text": f"Customer message to a payments app's support desk:\n{m['text']}"}],
            questions={"money_back": {"type": "noul", "instructions": QUESTION}},
        )
        answer = result.model_dump() if hasattr(result, "model_dump") else result
        raw[m["id"]] = answer
        probs[m["id"]] = first_probability(answer)
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / "gemini-decision-1.json"
    path.write_text(json.dumps({"source": "Gemini Decisions API (noul)", "models": ["gemini-decision-1"],
                                "probs": probs, "raw": raw}, indent=1, default=str))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()

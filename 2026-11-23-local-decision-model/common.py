"""Shared bits: the questions, the dataset, and where results live."""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data" / "messages.jsonl"
RESULTS = HERE / "results"
BASELINE = HERE / "baseline"
WEIGHTS = HERE / "weights" / "Ivonnet-0.8B"

# The 13 Nov question, word for word, so the Claude baseline and the decision model answer the same thing.
QUESTION = (
    "Is the customer asking for money back or contesting a charge "
    "(a refund request, a dispute, a chargeback or a reversal), stated or clearly implied?"
)
# The same rule in plainer words. A decision model reads the wording, so we check how much the answer moves.
QUESTION_PLAIN = "Does this customer want money returned to them, or say a payment on their account is wrong?"

QUESTIONS = {"original": QUESTION, "plain": QUESTION_PLAIN}


def load_messages():
    return [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]

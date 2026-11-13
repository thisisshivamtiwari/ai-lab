"""Shared bits: the question, the dataset, and where results live."""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data" / "messages.jsonl"
RESULTS = HERE / "results"

# One yes/no ("noul") question, asked of every message. The label rule is in data/LABELS.md.
QUESTION = (
    "Is the customer asking for money back or contesting a charge "
    "(a refund request, a dispute, a chargeback or a reversal), stated or clearly implied?"
)


def load_messages():
    return [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]

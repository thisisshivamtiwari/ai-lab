"""Write what tiny-voca's text front end (dizione) turns each item into (results/words.json).

dizione rewrites numbers, money, dates, units and abbreviations into words by rule before it looks up phonemes; the
model only ever sees those phonemes. So this file shows which errors come from the front end and which from the
model. Letters read one by one are written in capitals ("V A T").

    uv run words.py
"""
import json
import os
from pathlib import Path

HERE = Path(__file__).parent
os.environ.setdefault("DIZIONE_DATA", str(HERE / "weights" / "phonemizer"))

import dizione
from dizione.normalize import Punct

from items import ITEMS


def spoken(text):
    out = []
    for token in dizione.get().normalizer.tokens(text):
        if isinstance(token, Punct):
            out.append(token.mark)
        else:
            out.append(" ".join(token.text.upper()) if token.spell else token.text)
    return " ".join(out)


def main():
    rows = [{"no": no, "text": text, "spoken": spoken(text)} for no, (_, text, _) in enumerate(ITEMS)]
    (HERE / "results" / "words.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for r in rows:
        print(f"{r['no']:02d} {r['text']}\n   -> {r['spoken']}")


if __name__ == "__main__":
    main()

"""Write what ZONOS3-Mini's text normaliser turns each item into (results/normalised.json).

The model reads this spoken form when text_normalization is on, so it shows which errors come from the normaliser
and which from the model. Same normaliser and grammar as the server uses for en_gb: zyphra-textnorm, "en".

    uv run normalised.py
"""
import json
from pathlib import Path

import zyphra_textnorm

from items import ITEMS

HERE = Path(__file__).parent


def main():
    tn = zyphra_textnorm.Normalizer()
    rows = [{"no": no, "text": text, "spoken": tn.normalize(text, "en")} for no, (_, text, _) in enumerate(ITEMS)]
    (HERE / "results" / "normalised.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for r in rows:
        print(f"{r['no']:02d} {r['text']}\n   -> {r['spoken']}")


if __name__ == "__main__":
    main()

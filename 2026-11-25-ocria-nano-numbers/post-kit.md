# Post kit: a 48 MB OCR model vs the Mac's built-in OCR, on the numbers in hotel paperwork (2026-11-25)

**The one finding:** in our small test, LlamaIndex's new 8M-parameter OCRia-nano-1 read 99% of the prices, dates and
references on clean, photocopied and phone-photographed hotel rate cards, folios and invoices, the same as Apple's
on-device OCR. At fax quality (100 dpi, black and white) both engines fell to 40%, and what they lost were the
amounts: and both kept producing plausible wrong amounts (£168.94 for £168.95) instead of nothing. Neither engine
knows when it can't read a number.

**Everyday analogy for the writer:** a new junior who reads invoices aloud to the accounts team. On a decent copy they
read every figure right. Hand them a bad fax and they still read figures out, confidently, and about a third of what
they say is a price that isn't on the page. The problem isn't that they struggle with the fax; it's that they never
say "I can't read this one".

**Facts and sources**
1. LlamaIndex released OCRia-nano-1 on 23 Nov 2026: an 8.1M-parameter CPU document-parsing pipeline (line detector,
   four recognisers, a small table and layout model) distilled from its 4B OCRia-1; 48 MB of ONNX files; runs through
   the open-source LiteParse tool and in WebAssembly. The card claims ParseBench-2 59.2 against 48.7 for Tesseract and
   426 ms a page on one CPU core. Weights are under an Open RAIL-M-based licence (free under $2M revenue).
   Source: https://www.llamaindex.ai/blog/introducing-ocria-nano-1 ; second source:
   https://huggingface.co/llamaindex/OCRia-nano-1
2. Our small test: 60 synthetic pages (rate cards, guest folios, supplier invoices; 5 seeds x 4 image conditions),
   1,500 number tokens, both engines untuned, Apple M2, one run. Number tokens read exactly:
   - clean: OCRia-nano-1 371/375, Apple Vision 375/375
   - photocopy: 374/375 vs 364/375
   - phone photo: 371/375 vs 372/375
   - fax-like 100 dpi: 151/375 vs 149/375
   Source: out/summary.json and the README table in the repo folder below.
3. Near-miss amounts (amount-shaped output that matches no amount on the page) on the 15 fax-like pages: 62 for
   OCRia-nano-1 and 70 for Apple Vision, e.g. £168.94 for £168.95 and £399.79 for £399.29. On the 45 readable pages:
   2 and 5. Median time per page: 0.34 s (OCRia-nano-1, CPU) and 0.19 s (Vision). Source: out/near_miss.json.

**Visual:** media/number-accuracy.png (bar chart, both engines, four conditions). Optional second image:
media/sample-fax-invoice.png (what a 100 dpi invoice looks like to the engines).

**Repo:** https://github.com/thisisshivamtiwari/ai-lab/tree/main/2026-11-25-ocria-nano-numbers

**The honest limit:** synthetic pages in one font pair, generated and scored by the same script, one Mac, one run.
Our "fax" and "phone" conditions are approximations. The 9-vs-14 misses on readable pages is not a difference
between the engines. The amounts failed at 100 dpi partly because our pages put them in a smaller monospaced font
than the dates. Not a benchmark; the vendor's own numbers are the vendor's.

**What a hotel should take from it (no claims beyond the test):** an OCR step in a billing or invoice pipeline needs
a confidence or re-check gate on amounts, because a small model and the OS model both return confident wrong prices
on poor scans. Low-resolution input should be rejected before OCR, not after.

#!/bin/sh
# One command: synthetic pages -> both OCR engines -> scores -> chart. Needs uv and macOS (Apple Vision helper).
set -e
cd "$(dirname "$0")"
uv sync -q
uv run lit models pull ocria-nano
uv run python generate.py 5
uv run python run.py | tee out/run.log
uv run python chart.py

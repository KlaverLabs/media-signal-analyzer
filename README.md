# Media Manipulation Signal Analyzer & TraceCheck

FastAPI + Jinja2 + Tailwind + Chart.js workshop tool ("Truth in the Age of AI"). Two tabs:

- **Signal Analyzer** – scores 20 observable rhetorical/structural indicators, semicircular gauge, bar chart, donut, evidence cards, and a Source View that highlights the exact supporting quote.
- **TraceCheck** – mobile feed simulator that interrupts a repost with a six-stage verification accordion (Source → Creation → Publication → Amplification → Sharing → Audience).

It reports signals only: never "PSYOP", never intent, never truth value.

## Setup
    python -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/uvicorn app.main:app --reload       # http://localhost:8000
    .venv/bin/pytest

## Engines
| Condition | Engine label in UI |
|---|---|
| `OPENROUTER_API_KEY` or `OPENAI_API_KEY` set (env or `.env`) | Engine: Live LLM Extraction |
| no key, `Force deterministic fallback` ticked, or the LLM call fails | Engine: Demonstration Fallback (Deterministic) |

Optional `LLM_MODEL` overrides the model (default `openai/gpt-4o` on OpenRouter, `gpt-4o` on OpenAI). Claude and Gemini models are available through OpenRouter. A failed LLM call never crashes: it falls back and shows a warning. The fallback is a regex lexicon covering 15 of 20 indicators; the other five are `Cannot assess` by design.

## Scoring
Each indicator: `Observed` (2–5), `Not observed` (1) or `Cannot assess` (no score).
`Index = ((mean score of assessed indicators − 1) / 4) × 100`. `Cannot assess` is excluded, never counted as 0. Fewer than 3 assessed → no index, banner "Insufficient Context to Calculate Normalized Index".
Bands: 0–25 Low · 25–50 Moderate · 50–75 Elevated · 75–100 High.

Every `Observed` quote is checked server-side as an exact substring (whitespace-tolerant); otherwise the quote is stripped and the indicator becomes `Cannot assess` and unscored.

## Facilitation guide
1. Load sample text, run with **Force fallback** to show how crude keyword rules behave; then run with a key to compare.
2. Click a bar or card; discuss the highlighted quote and its *Missing context*.
3. Point out the disclaimer under the gauge: a high index is not a verdict.
4. Switch to TraceCheck, press Repost, walk the six stages, then use *Open claim in PSYOPS Forensic Suite* to analyze the post text.
5. Export JSON / Markdown / PDF for handouts (print uses a light palette).

## Docker
    cp .env.example .env   # add a key, or leave empty for fallback mode
    docker compose up --build   # http://localhost:8000

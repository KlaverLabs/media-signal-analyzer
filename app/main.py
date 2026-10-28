from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .analyzer import analyze, detect_provider
from .config import DISCLAIMER, GAUGE_DISCLAIMER, INDICATORS, MAX_CHARS, SAMPLE_TEXT, TRACE_CLAIM, TRACE_STAGES
from .ingest import fetch_article
from .models import AnalysisReport, AnalyzeRequest

BASE = Path(__file__).parent
@asynccontextmanager
async def lifespan(_: FastAPI):
    if detect_provider() is None:  # refuse to start rather than silently serving the non-AI fallback
        raise RuntimeError("No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY (environment or .env) and restart.")
    yield


app = FastAPI(title="Media Manipulation Signal Analyzer & TraceCheck", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "disclaimer": DISCLAIMER, "gauge_disclaimer": GAUGE_DISCLAIMER, "max_chars": MAX_CHARS,
        "boot": {"stages": TRACE_STAGES, "claim": TRACE_CLAIM, "sample": SAMPLE_TEXT,
                 "indicators": [{"id": i, "name": n} for i, n, _ in INDICATORS]},
    })


@app.get("/api/health")
def health():
    p = detect_provider()
    return {"engine": "llm" if p else "fallback", "provider": p.name if p else None, "model": p.model if p else None}


# Sync handler: runs in FastAPI's threadpool so blocking LLM/HTTP calls don't stall the event loop.
@app.post("/api/analyze", response_model=AnalysisReport)
def analyze_endpoint(req: AnalyzeRequest):
    text, url = (req.text or "").strip(), None
    if not text:
        if not (req.url or "").strip():
            raise HTTPException(400, "Provide a URL or paste text.")
        text, warning = fetch_article(req.url)
        if warning:
            raise HTTPException(422, warning)
        url = req.url.strip()
    try:
        return analyze(text, url, req.force_fallback)
    except ValueError as e:
        raise HTTPException(413, str(e))

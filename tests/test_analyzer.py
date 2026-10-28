import pytest

from app import analyzer
from app.analyzer import analyze, build_report, find_quote
from app.models import IndicatorResult

TEXT = "Everyone knows   this is the worst thing ever.\nShare before it is deleted!"


def res(i, status, score=None, quote=None):
    return IndicatorResult(id=i, name="x", status=status, score=score, quote=quote, rationale="r", missing_context="m")


def test_quote_must_be_verbatim():
    assert find_quote("Everyone knows this is the worst", TEXT) is not None  # whitespace-tolerant
    assert find_quote("Share it now!", TEXT) is None
    assert find_quote("Everyone ... ever", TEXT) is None


def test_ungrounded_observed_is_stripped_and_not_scored():
    r = build_report([res(2, "Observed", 5, "Share it now!")], TEXT, "llm", "m", None, [])
    e = next(x for x in r.results if x.id == 2)
    assert e.status == "Cannot assess" and e.quote is None and e.score is None and not e.quote_verified


def test_index_math_excludes_unassessed():
    rs = [res(1, "Observed", 5, "Everyone knows"), res(2, "Not observed"), res(3, "Not observed")]
    r = build_report(rs, TEXT, "llm", "m", None, [])
    assert r.assessed_count == 3 and r.average_score == round((5 + 1 + 1) / 3, 2)
    assert r.intensity_index == round(((7 / 3) - 1) / 4 * 100, 1)  # 17 candidates are Cannot assess, ignored


def test_all_present_and_max_min():
    hi = build_report([res(i, "Observed", 5, "Everyone knows") for i in range(1, 21)], TEXT, "llm", "m", None, [])
    lo = build_report([res(i, "Not observed") for i in range(1, 21)], TEXT, "llm", "m", None, [])
    assert hi.intensity_index == 100.0 and hi.band == "High"
    assert lo.intensity_index == 0.0 and lo.band == "Low"


def test_insufficient_context_banner():
    r = build_report([res(1, "Not observed"), res(2, "Not observed")], TEXT, "llm", "m", None, [])
    assert r.insufficient_context and r.intensity_index is None and "Insufficient Context" in r.banner


def test_fallback_without_key(monkeypatch):
    for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(analyzer, "load_dotenv", lambda *a, **k: None)
    r = analyze(TEXT + " Insiders say it is hopeless. Nothing will ever change.")
    assert r.engine == "fallback" and "Fallback" in r.engine_label and len(r.results) == 20
    for e in r.results:
        if e.status == "Observed":
            assert e.quote_verified and e.quote in r.text
    assert next(e for e in r.results if e.id == 17).status == "Cannot assess"


def test_llm_failure_degrades_gracefully(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(analyzer, "run_llm", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    r = analyze(TEXT)
    assert r.engine == "fallback" and r.warnings and "boom" in r.warnings[0]


def test_force_fallback_ignores_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(analyzer, "run_llm", lambda *a: pytest.fail("LLM must not be called"))
    assert analyze(TEXT, force_fallback=True).engine == "fallback"

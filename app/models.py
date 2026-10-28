from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["Observed", "Not observed", "Cannot assess"]


class LLMItem(BaseModel):
    """One indicator as returned by the model."""

    id: int
    status: Status
    score: Optional[int] = Field(None, description="1 (absent) to 5 (pervasive/strong). Null when Cannot assess.")
    quote: Optional[str] = Field(None, description="Exact verbatim substring of the source; required when Observed.")
    rationale: str
    missing_context: str = Field(..., description="What cannot be determined from the text alone.")


class LLMOutput(BaseModel):
    results: List[LLMItem]


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    force_fallback: bool = False


class IndicatorResult(BaseModel):
    id: int
    name: str
    description: str = ""
    status: Status
    score: Optional[int] = None
    quote: Optional[str] = None
    quote_start: Optional[int] = None
    quote_end: Optional[int] = None
    quote_verified: bool = False
    rationale: str
    missing_context: str


class AnalysisReport(BaseModel):
    engine: Literal["llm", "fallback"]
    engine_label: str
    model: Optional[str] = None
    source_url: Optional[str] = None
    text: str
    assessed_count: int
    observed_count: int
    not_observed_count: int
    cannot_assess_count: int
    average_score: Optional[float] = None
    intensity_index: Optional[float] = None
    band: Optional[str] = None
    insufficient_context: bool
    banner: Optional[str] = None
    gauge_disclaimer: str
    disclaimer: str
    warnings: List[str] = []
    results: List[IndicatorResult]

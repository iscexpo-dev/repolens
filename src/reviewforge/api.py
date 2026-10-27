"""Optional FastAPI shell. It does not call an LLM or claim review coverage."""

from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised when optional extra missing
    raise RuntimeError("Install optional API dependencies with: pip install -e '.[api]'") from exc

from .diff import parse_changed_lines

app = FastAPI(
    title="Best AI Code Reviewer — Starter API",
    version="0.1.0",
    description=(
        "Development scaffold only. The model review provider is not configured; "
        "a lack of findings must never be interpreted as proof of safety."
    ),
)


class DiffRequest(BaseModel):
    diff: str = Field(min_length=1, max_length=2_000_000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "review_provider": "not_configured"}


@app.post("/v1/diff/changed-lines")
def changed_lines(request: DiffRequest) -> dict[str, object]:
    try:
        items = parse_changed_lines(request.diff)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": "parsed",
        "review_performed": False,
        "changed_line_count": len(items),
        "changed_lines": [item.to_dict() for item in items],
        "warning": "Diff parsing is not AI review and does not assess code safety.",
    }

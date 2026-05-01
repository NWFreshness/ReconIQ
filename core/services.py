"""Framework-neutral application services for ReconIQ."""
from __future__ import annotations

from typing import Callable

from core.models import AnalysisRequest, AnalysisResult
from llm.router import complete as llm_complete
from report.writer import write_report
from research.coordinator import run_all

ProgressCallback = Callable[[str, float], None] | None


def run_analysis(request: AnalysisRequest, progress_callback: ProgressCallback = None) -> AnalysisResult:
    """Run the full ReconIQ analysis workflow without depending on a UI framework."""

    def configured_llm_complete(
        prompt: str,
        module: str,
        system: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        return llm_complete(
            prompt=prompt,
            module=module,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            provider_override=request.provider_override,
            model_override=request.model_override,
        )

    results = run_all(
        target_url=request.target_url,
        llm_complete=configured_llm_complete,
        enabled_modules=request.enabled_modules,
        progress_callback=progress_callback,
        max_pages=request.max_pages,
        max_depth=request.max_depth,
    )
    report_path = write_report(results, output_dir=request.output_dir or "reports")
    return AnalysisResult(results=results, report_path=report_path)

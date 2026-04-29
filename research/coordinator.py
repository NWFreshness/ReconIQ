"""Research Coordinator — parallel execution of modules 1-4, then sequential SWOT."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Optional

from research.company_profile import run as run_company_profile
from research.seo_keywords import run as run_seo_keywords
from research.competitors import run as run_competitors
from research.social_content import run as run_social_content
from research.swot import run as run_swot


ProgressCallback = Optional[Callable[[str, float], None]]


def run_all(
    target_url: str,
    llm_complete: Callable,
    enabled_modules: dict[str, bool],
    progress_callback: ProgressCallback = None,
) -> dict[str, Any]:
    """
    Run all enabled research modules and return a combined results dict.

    Execution order:
    - Modules 1-4: run in parallel via ThreadPoolExecutor
    - Module 5 (SWOT): runs only after all 1-4 complete

    Args:
        target_url: URL to research.
        llm_complete: LLM completion callable.
        enabled_modules: Dict of module_name -> enabled (bool).
        progress_callback: Optional fn(log_message, progress_pct) for UI updates.

    Returns:
        Dict with keys: company_profile, seo_keywords, competitor, social_content, swot, metadata.
    """
    results: dict[str, Any] = {
        "metadata": {
            "target_url": target_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modules_run": [],
            "modules_skipped": [],
        }
    }

    def log(msg: str, pct: float):
        if progress_callback:
            progress_callback(msg, pct)

    # Phase 1: Parallel modules (1-4)
    # We need company_profile first since others may reference it,
    # but we run all in parallel — each module handles incomplete input gracefully.
    parallel_tasks = {}

    if enabled_modules.get("company_profile", True):
        parallel_tasks["company_profile"] = lambda: run_company_profile(target_url, llm_complete)
    if enabled_modules.get("seo_keywords", True):
        # SEO module uses company_profile output if available
        def _seo_task():
            profile = results.get("company_profile", {})
            return run_seo_keywords(profile, target_url, llm_complete)
        parallel_tasks["seo_keywords"] = _seo_task
    if enabled_modules.get("competitor", True):
        def _competitor_task():
            profile = results.get("company_profile", {})
            return run_competitors(profile, target_url, llm_complete)
        parallel_tasks["competitor"] = _competitor_task
    if enabled_modules.get("social_content", True):
        def _social_task():
            profile = results.get("company_profile", {})
            return run_social_content(profile, target_url, llm_complete)
        parallel_tasks["social_content"] = _social_task

    if parallel_tasks:
        log(f"Running {len(parallel_tasks)} research modules in parallel...", 10.0)

        # Run company_profile first (others depend on it)
        if "company_profile" in parallel_tasks:
            log("Running Company Profile...", 15.0)
            try:
                results["company_profile"] = parallel_tasks["company_profile"]()
                results["metadata"]["modules_run"].append("company_profile")
                log("✓ Company Profile complete", 30.0)
            except Exception as exc:
                results["company_profile"] = {"error": str(exc)}
                results["metadata"]["modules_skipped"].append("company_profile")
                log(f"✗ Company Profile failed: {exc}", 30.0)

        # Now run remaining modules in parallel (they can use company_profile output)
        remaining = {k: v for k, v in parallel_tasks.items() if k != "company_profile"}
        if remaining:
            with ThreadPoolExecutor(max_workers=len(remaining)) as executor:
                futures = {}
                for name, task_fn in remaining.items():
                    f = executor.submit(task_fn)
                    futures[f] = name
                    log(f"Running {name.replace('_', ' ').title()}...", 30.0)

                for future in as_completed(futures):
                    module_name = futures[future]
                    try:
                        result = future.result()
                        results[module_name] = result
                        results["metadata"]["modules_run"].append(module_name)
                        log(f"✓ {module_name.replace('_', ' ').title()} complete", 60.0)
                    except Exception as exc:
                        results[module_name] = {"error": str(exc)}
                        results["metadata"]["modules_skipped"].append(module_name)
                        log(f"✗ {module_name.replace('_', ' ').title()} failed: {exc}", 60.0)

    # Phase 2: SWOT synthesis (module 5) — only if enabled and at least one module succeeded
    if enabled_modules.get("swot", True):
        log("Running SWOT Synthesis...", 80.0)
        try:
            results["swot"] = run_swot(
                company_profile=results.get("company_profile", {}),
                seo_keywords=results.get("seo_keywords", {}),
                competitor=results.get("competitor", {}),
                social_content=results.get("social_content", {}),
                target_url=target_url,
                llm_complete=llm_complete,
            )
            results["metadata"]["modules_run"].append("swot")
            log("✓ SWOT Synthesis complete", 95.0)
        except Exception as exc:
            results["swot"] = {"error": str(exc)}
            results["metadata"]["modules_skipped"].append("swot")
            log(f"✗ SWOT Synthesis failed: {exc}", 95.0)
    else:
        results["metadata"]["modules_skipped"].append("swot")

    log("All modules complete!", 100.0)
    return results
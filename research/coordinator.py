"""Research Coordinator — dependency-aware orchestration for research modules."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Optional

from research.company_profile import run as run_company_profile
from research.seo_keywords import run as run_seo_keywords
from research.competitors import run as run_competitors
from research.social_content import run as run_social_content
from research.swot import run as run_swot
from scraper.scraper import ScrapeCache, extract_domain_name, scrape


ProgressCallback = Optional[Callable[[str, float], None]]
MODULE_LABELS = {
    "company_profile": "Company Profile",
    "seo_keywords": "SEO Keywords",
    "competitor": "Competitor Intel",
    "social_content": "Social Content",
    "swot": "SWOT Synthesis",
}


def run_all(
    target_url: str,
    llm_complete: Callable,
    enabled_modules: dict[str, bool],
    progress_callback: ProgressCallback = None,
) -> dict[str, Any]:
    """
    Run all enabled research modules and return a combined results dict.

    Execution order:
    1. Company Profile runs first (scrapes the target URL once, shares content).
    2. SEO, Competitors, and Social/Content run in parallel after profile.
    3. SWOT runs after all available downstream module outputs are collected.
    """
    metadata = _initial_metadata(target_url, llm_complete)
    results: dict[str, Any] = {"metadata": metadata}

    # Create a scrape cache for this analysis run so we don't re-scrape the
    # same URL across modules. The homepage content is scraped once here and
    # shared with all modules that need it.
    scrape_cache = ScrapeCache()

    def log(msg: str, pct: float) -> None:
        if progress_callback:
            progress_callback(msg, pct)

    def mark_skipped(module_name: str) -> None:
        if module_name not in metadata["modules_skipped"]:
            metadata["modules_skipped"].append(module_name)

    def mark_failed(module_name: str, exc: Exception) -> None:
        if module_name not in metadata["modules_failed"]:
            metadata["modules_failed"].append(module_name)
        results[module_name] = {"error": str(exc)}

    def mark_run(module_name: str, result: Any) -> None:
        results[module_name] = result
        if module_name not in metadata["modules_run"]:
            metadata["modules_run"].append(module_name)
        _collect_data_limitations(result, metadata)

    # Record disabled modules up front so skipped metadata is complete even if
    # earlier dependencies fail.
    for module_name in MODULE_LABELS:
        if not enabled_modules.get(module_name, True):
            mark_skipped(module_name)

    # ── Phase 1: Scrape the homepage once ────────────────────────────────────
    scraped_content: str | None = None
    if enabled_modules.get("company_profile", True):
        log("Scraping target website...", 5.0)
        scraped_content = scrape_cache.get_text(target_url)
        if not scraped_content:
            # Fallback: use domain name as hint
            domain = extract_domain_name(target_url)
            scraped_content = (
                f"Could not access {target_url}. "
                f"The company's domain is: {domain}. "
                f"Analyze based on the domain name alone."
            )
        log("Website scraped", 10.0)

    # ── Phase 2: Company Profile (must succeed for downstream modules) ───────
    company_profile_succeeded = False
    if enabled_modules.get("company_profile", True):
        log("Running Company Profile...", 12.0)
        try:
            profile = run_company_profile(
                target_url, llm_complete, scraped_content=scraped_content
            )
            mark_run("company_profile", profile)
            company_profile_succeeded = True
            log("✓ Company Profile complete", 25.0)
        except Exception as exc:
            mark_failed("company_profile", exc)
            log(f"✗ Company Profile failed: {exc}", 25.0)
    else:
        log("Company Profile skipped", 25.0)

    if company_profile_succeeded:
        _run_downstream_modules(
            target_url=target_url,
            llm_complete=llm_complete,
            enabled_modules=enabled_modules,
            results=results,
            metadata=metadata,
            mark_run=mark_run,
            mark_failed=mark_failed,
            log=log,
        )
    else:
        for module_name in ("seo_keywords", "competitor", "social_content"):
            if enabled_modules.get(module_name, True):
                mark_skipped(module_name)
        log("Skipping downstream modules because Company Profile did not complete", 70.0)

    if enabled_modules.get("swot", True) and company_profile_succeeded:
        log("Running SWOT Synthesis...", 85.0)
        try:
            swot = run_swot(
                company_profile=results.get("company_profile", {}),
                seo_keywords=results.get("seo_keywords", {}),
                competitor=results.get("competitor", {}),
                social_content=results.get("social_content", {}),
                target_url=target_url,
                llm_complete=llm_complete,
            )
            mark_run("swot", swot)
            log("✓ SWOT Synthesis complete", 95.0)
        except Exception as exc:
            mark_failed("swot", exc)
            log(f"✗ SWOT Synthesis failed: {exc}", 95.0)
    elif enabled_modules.get("swot", True):
        mark_skipped("swot")
        log("SWOT Synthesis skipped", 95.0)

    log("All modules complete!", 100.0)
    return results


def _run_downstream_modules(
    target_url: str,
    llm_complete: Callable,
    enabled_modules: dict[str, bool],
    results: dict[str, Any],
    metadata: dict[str, Any],
    mark_run: Callable[[str, Any], None],
    mark_failed: Callable[[str, Exception], None],
    log: Callable[[str, float], None],
) -> None:
    tasks: dict[str, Callable[[], dict]] = {}
    profile = results.get("company_profile", {})

    if enabled_modules.get("seo_keywords", True):
        tasks["seo_keywords"] = lambda: run_seo_keywords(profile, target_url, llm_complete)
    if enabled_modules.get("competitor", True):
        tasks["competitor"] = lambda: run_competitors(profile, target_url, llm_complete)
    if enabled_modules.get("social_content", True):
        tasks["social_content"] = lambda: run_social_content(profile, target_url, llm_complete)

    if not tasks:
        log("No downstream research modules enabled", 70.0)
        return

    log(f"Running {len(tasks)} downstream research modules in parallel...", 30.0)
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {}
        for module_name, task_fn in tasks.items():
            futures[executor.submit(task_fn)] = module_name
            log(f"Running {MODULE_LABELS[module_name]}...", 35.0)

        completed = 0
        for future in as_completed(futures):
            module_name = futures[future]
            completed += 1
            pct = 35.0 + (completed / len(tasks)) * 35.0
            try:
                mark_run(module_name, future.result())
                log(f"✓ {MODULE_LABELS[module_name]} complete", pct)
            except Exception as exc:
                mark_failed(module_name, exc)
                log(f"✗ {MODULE_LABELS[module_name]} failed: {exc}", pct)


def _initial_metadata(target_url: str, llm_complete: Callable) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "target_url": target_url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules_run": [],
        "modules_skipped": [],
        "modules_failed": [],
        "data_limitations": [],
    }
    provider = getattr(llm_complete, "provider", None)
    model = getattr(llm_complete, "model", None)
    if provider is not None:
        metadata["provider"] = provider
    if model is not None:
        metadata["model"] = model
    return metadata


def _collect_data_limitations(result: Any, metadata: dict[str, Any]) -> None:
    if not isinstance(result, dict):
        return
    limitations = result.get("data_limitations", [])
    if isinstance(limitations, str):
        limitations = [limitations]
    if not isinstance(limitations, list):
        return
    for limitation in limitations:
        if limitation and limitation not in metadata["data_limitations"]:
            metadata["data_limitations"].append(limitation)
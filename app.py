"""ReconIQ — Marketing Intelligence Platform."""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
from llm.router import check_ollama

from core.models import AnalysisRequest
from core.services import run_analysis


# ── Pure helpers (testable without Streamlit runtime) ────────────────────────────────────────────


def normalize_url(url: str) -> str:
    """Return a URL with an HTTP scheme, defaulting bare domains to HTTPS."""
    cleaned = url.strip()
    if not cleaned:
        return cleaned
    if urlparse(cleaned).scheme:
        return cleaned
    return f"https://{cleaned}"


def validate_url(url: str) -> tuple[bool, str]:
    """Validate and normalize a user-supplied URL.

    Returns:
        (is_valid, normalized_url_or_error_message)
    """
    cleaned = url.strip()
    if not cleaned:
        return False, "Please enter a URL."
    normalized = normalize_url(cleaned)
    parsed = urlparse(normalized)
    if not parsed.netloc or "." not in parsed.netloc:
        return False, "Please enter a valid URL with a domain."
    return True, normalized


def build_analysis_request(
    target_url: str,
    enabled_modules: dict[str, bool],
    provider: str,
    model: str,
    output_dir: str | None,
) -> AnalysisRequest:
    """Build an AnalysisRequest from UI state, applying overrides only when non-default."""
    provider_override = provider if provider != "deepseek" else None
    model_override = model.strip() if model.strip() else None
    return AnalysisRequest(
        target_url=target_url,
        enabled_modules=enabled_modules,
        provider_override=provider_override,
        model_override=model_override,
        output_dir=output_dir,
    )


def open_folder(path: str) -> None:
    """Open the given directory in the system file manager."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


# ── Streamlit page setup ───────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ReconIQ",
    page_icon="🎯",
    layout="wide",
)

# ── Init session state ──────────────────────────────────────────────────────────────────────────
if "report_path" not in st.session_state:
    st.session_state.report_path = None
if "report_content" not in st.session_state:
    st.session_state.report_content = None
if "running" not in st.session_state:
    st.session_state.running = False

# ── Sidebar ──────────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🎯 ReconIQ")
st.sidebar.markdown("*Marketing Intelligence*")

ollama_ok = check_ollama()
st.sidebar.markdown(f"**Ollama:** {'🟢 Connected' if ollama_ok else '🔴 Not found'}")

with st.sidebar.expander("LLM Settings", expanded=True):
    provider = st.selectbox(
        "Provider",
        options=["deepseek", "openai", "anthropic", "groq", "ollama"],
        index=0,
    )
    model = st.text_input("Model override (blank = default)", value="")

with st.sidebar.expander("Report Output", expanded=False):
    output_dir = st.text_input("Output directory", value=str(Path.cwd() / "reports"))

# ── Main ────────────────────────────────────────────────────────────────────────────────────
st.title("🎯 ReconIQ — Marketing Intelligence")
st.markdown("Input a company URL and get a full marketing intelligence report.")

target_url = st.text_input(
    "Target URL",
    placeholder="https://example.com",
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 1])
with col1:
    run_analysis_btn = st.button(
        "🔍 Analyze Company",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )
with col2:
    clear_btn = st.button("🗑️ Clear", use_container_width=True)

# Module toggles
with st.expander("Modules", expanded=True):
    m1, m2 = st.columns(2)
    with m1:
        toggle_profile = st.checkbox("Company Profile", value=True)
        toggle_seo = st.checkbox("SEO & Keywords", value=True)
    with m2:
        toggle_competitor = st.checkbox("Competitor Intel", value=True)
        toggle_social = st.checkbox("Social & Content", value=True)
    toggle_swot = st.checkbox("SWOT Synthesis", value=True)

enabled_modules = {
    "company_profile": toggle_profile,
    "seo_keywords": toggle_seo,
    "competitor": toggle_competitor,
    "social_content": toggle_social,
    "swot": toggle_swot,
}

# Status area
status_container = st.empty()
progress_bar = st.progress(0)
log_container = st.empty()

# Report display
report_container = st.empty()

if clear_btn:
    st.session_state.report_path = None
    st.session_state.report_content = None
    st.session_state.running = False
    st.rerun()

if run_analysis_btn and target_url:
    is_valid, validation_result = validate_url(target_url)
    if not is_valid:
        st.error(validation_result)
    else:
        st.session_state.running = True
        log_lines: list[str] = []

        def progress_callback(msg: str, pct: float) -> None:
            log_lines.append(msg)
            progress_bar.progress(pct / 100.0)
            log_container.info("\n".join(log_lines[-10:]))

        try:
            request = build_analysis_request(
                target_url=validation_result,
                enabled_modules=enabled_modules,
                provider=provider,
                model=model,
                output_dir=output_dir,
            )

            status_container.info("🚀 Running research modules...")
            result = run_analysis(request, progress_callback=progress_callback)

            report_path = result.report_path
            if report_path:
                with open(report_path, encoding="utf-8") as fh:
                    report_content = fh.read()
                st.session_state.report_path = report_path
                st.session_state.report_content = report_content

            progress_bar.progress(100.0)
            status_container.success(f"✅ Report complete! Saved to:\n`{report_path}`")

            # Surface failed / skipped modules
            metadata = result.results.get("metadata", {})
            modules_failed = metadata.get("modules_failed", [])
            modules_skipped = metadata.get("modules_skipped", [])
            if modules_failed:
                st.warning(f"⚠️ Modules that failed: {', '.join(modules_failed)}")
            if modules_skipped:
                st.info(f"⏭️ Modules skipped: {', '.join(modules_skipped)}")

        except Exception as exc:
            status_container.error(f"❌ Error: {exc}")
        finally:
            st.session_state.running = False
            st.rerun()

# Display report if available
if st.session_state.report_content:
    report_container.markdown("---")
    report_container.markdown("### 📊 Report Preview")
    st.markdown(st.session_state.report_content)
    st.markdown("---")

    col_dl, col_open = st.columns(2)
    with col_dl:
        st.download_button(
            "📥 Download .md",
            data=st.session_state.report_content,
            file_name="reconiq-report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_open:
        if st.session_state.report_path and os.path.exists(st.session_state.report_path):
            if st.button("📁 Open in Folder", use_container_width=True):
                open_folder(str(Path(st.session_state.report_path).parent))

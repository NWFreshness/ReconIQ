"""ReconIQ — Marketing Intelligence Platform."""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components
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


# ── Streamlit page config ───────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ReconIQ — Marketing Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS ─────────────────────────────────────────────────────────────────────────────

css_path = Path(__file__).parent / ".streamlit" / "style.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>\n{f.read()}\n</style>", unsafe_allow_html=True)

# Force sidebar to stay open via JS (Streamlit's React can collapse it otherwise)
components.html(
    """<script>
    // Revert any sidebar collapse and prevent future collapse
    function forceSidebar() {
        const sb = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (sb) {
            sb.setAttribute('aria-expanded', 'true');
            sb.style.display = 'flex';
            sb.style.visibility = 'visible';
            sb.style.width = '300px';
            sb.style.minWidth = '300px';
            sb.style.maxWidth = '300px';
            sb.style.opacity = '1';
            sb.style.transform = 'none';
        }
        const sc = window.parent.document.querySelector('[data-testid="stSidebarContent"]');
        if (sc) {
            sc.style.display = 'block';
            sc.style.visibility = 'visible';
        }
    }
    forceSidebar();
    // Re-apply after Streamlit re-renders
    new MutationObserver(forceSidebar).observe(
        window.parent.document.body, { childList: true, subtree: true }
    );
    </script>""",
    height=0,
    width=0,
)

# ── Init session state ──────────────────────────────────────────────────────────────────────────

if "report_path" not in st.session_state:
    st.session_state.report_path = None
if "report_content" not in st.session_state:
    st.session_state.report_content = None
if "running" not in st.session_state:
    st.session_state.running = False

# ── Sidebar ──────────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo / brand
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.3rem;">'
        '<span style="font-size:1.6rem;">🎯</span>'
        '<div>'
        '<div style="font-size:1.3rem;font-weight:700;letter-spacing:-0.03em;color:var(--text-primary);">ReconIQ</div>'
        '<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--text-muted);margin-top:-2px;">Marketing Intelligence</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Active provider status (reads from config)
    from llm.router import get_config as _get_llm_config
    _cfg = _get_llm_config()
    _default_provider = _cfg.get("defaults", {}).get("provider", "deepseek")
    _default_model = _cfg.get("providers", {}).get(_default_provider, {}).get("default_model", "")
    _provider_label = _default_model or _default_provider
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<span class="status-dot connected"></span>'
        f'<span style="color:var(--text-secondary);font-size:0.85rem;">{_default_provider}</span>'
        f'<span style="color:var(--text-muted);font-size:0.75rem;">({_default_model or "default"})</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # LLM Settings
    st.markdown(
        '<div class="section-label">LLM Provider</div>',
        unsafe_allow_html=True,
    )
    provider = st.selectbox(
        "Provider",
        options=["deepseek", "openai", "anthropic", "groq", "ollama"],
        index=0,
        label_visibility="collapsed",
    )
    model = st.text_input("Model override", value="", placeholder="Leave blank for default")

    if model.strip():
        st.caption(f"Using **{provider}/{model.strip()}**")
    else:
        st.caption(f"Using **{provider}** default model")

    st.markdown(
        '<div class="section-label">Output</div>',
        unsafe_allow_html=True,
    )
    output_dir = st.text_input("Report directory", value=str(Path.cwd() / "reports"), label_visibility="collapsed")

# ── Hero Section ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<div class="hero-title">Marketing Intelligence</div>'
    '<div class="hero-subtitle">Enter a company URL and get a full competitive analysis, '
    'SWOT breakdown, and client acquisition strategy — powered by AI.</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Input Section ─────────────────────────────────────────────────────────────────────────────

url_col, btn_col = st.columns([4, 1])

with url_col:
    target_url = st.text_input(
        "Target URL",
        placeholder="https://example.com",
        label_visibility="collapsed",
    )

with btn_col:
    st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
    run_analysis_btn = st.button(
        "Analyze →",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )

# ── Module Toggles ────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<div class="section-label" style="margin-top:1.5rem;">Research Modules</div>',
    unsafe_allow_html=True,
)

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    toggle_profile = st.checkbox("Company Profile", value=True)
with m2:
    toggle_seo = st.checkbox("SEO & Keywords", value=True)
with m3:
    toggle_competitor = st.checkbox("Competitors", value=True)
with m4:
    toggle_social = st.checkbox("Social & Content", value=True)
with m5:
    toggle_swot = st.checkbox("SWOT Synthesis", value=True)

enabled_modules = {
    "company_profile": toggle_profile,
    "seo_keywords": toggle_seo,
    "competitor": toggle_competitor,
    "social_content": toggle_social,
    "swot": toggle_swot,
}

# ── Status Area ───────────────────────────────────────────────────────────────────────────────

status_container = st.empty()
progress_bar = st.progress(0, text="Ready")
log_container = st.empty()

# ── Clear Button ───────────────────────────────────────────────────────────────────────────────

clear_col1, clear_col2 = st.columns([6, 1])
with clear_col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.report_path = None
        st.session_state.report_content = None
        st.session_state.running = False
        st.rerun()

# ── Run Analysis ──────────────────────────────────────────────────────────────────────────────

if run_analysis_btn and target_url:
    is_valid, validation_result = validate_url(target_url)
    if not is_valid:
        st.error(validation_result)
    else:
        st.session_state.running = True
        log_lines: list[str] = []

        def progress_callback(msg: str, pct: float) -> None:
            log_lines.append(msg)
            progress_bar.progress(pct / 100.0, text=f"{pct:.0f}% — {msg}")
            log_container.info("\n".join(log_lines[-5:]))

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

            progress_bar.progress(100.0, text="Analysis complete")
            status_container.success(f"Report saved to `{report_path}`")

            # Surface failed / skipped modules
            metadata = result.results.get("metadata", {})
            modules_failed = metadata.get("modules_failed", [])
            modules_skipped = metadata.get("modules_skipped", [])
            if modules_failed:
                st.warning(f"Modules that failed: **{', '.join(modules_failed)}**")
            if modules_skipped:
                st.info(f"Modules skipped: **{', '.join(modules_skipped)}**")

        except Exception as exc:
            status_container.error(f"Error: {exc}")
        finally:
            st.session_state.running = False
            st.rerun()

# ── Report Display ─────────────────────────────────────────────────────────────────────────────

if st.session_state.report_content:
    st.markdown("---")

    # Report header with actions
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col1:
        st.markdown("### Report Preview")
    with header_col2:
        st.download_button(
            "↓ Download .md",
            data=st.session_state.report_content,
            file_name="reconiq-report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with header_col3:
        if st.session_state.report_path and os.path.exists(st.session_state.report_path):
            if st.button("📁 Open Folder", use_container_width=True):
                open_folder(str(Path(st.session_state.report_path).parent))

    # Report content in a styled card
    st.markdown(
        '<div class="report-card">',
        unsafe_allow_html=True,
    )
    st.markdown(st.session_state.report_content)
    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )
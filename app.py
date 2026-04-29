"""ReconIQ — Marketing Intelligence Platform."""
from __future__ import annotations

import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.expanduser("~/Documents/ai-automation-agency/ReconIQ"))

import streamlit as st
from llm.router import check_ollama, complete as llm_complete, get_config
from report.writer import write_report
from research.coordinator import run_all

st.set_page_config(
    page_title="ReconIQ",
    page_icon="🎯",
    layout="wide",
)

# ── Init session state ──────────────────────────────────────────────────────────
if "report_path" not in st.session_state:
    st.session_state.report_path = None
if "report_content" not in st.session_state:
    st.session_state.report_content = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("🎯 ReconIQ")
st.sidebar.markdown("*Marketing Intelligence*")

ollama_ok = check_ollama()
st.sidebar.markdown(f"**Ollama:** {'🟢 Connected' if ollama_ok else '🔴 Not found'}")

config = get_config()
with st.sidebar.expander("LLM Settings", expanded=True):
    provider = st.selectbox(
        "Provider",
        options=["deepseek", "openai", "anthropic", "groq", "ollama"],
        index=0,
    )
    model = st.text_input("Model override (blank = default)", value="")

    if model:
        st.sidebar.info(f"Using: {provider}/{model}")
    else:
        default_model = config.get("providers", {}).get(provider, {}).get("default_model", "default")
        st.sidebar.info(f"Using: {provider}/{default_model}")

with st.sidebar.expander("Report Output", expanded=False):
    output_dir = st.text_input("Output directory", value="~/Documents/ai-automation-agency/ReconIQ/reports")

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🎯 ReconIQ — Marketing Intelligence")
st.markdown("Input a company URL and get a full marketing intelligence report.")

target_url = st.text_input(
    "Target URL",
    placeholder="https://example.com",
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 1])
with col1:
    run_analysis = st.button("🔍 Analyze Company", type="primary", use_container_width=True)
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

# Override config provider/model if user changed them
if model or provider != "deepseek":
    from llm import router as llm_router
    # Temporarily patch the module config for this session
    llm_router.config["defaults"]["provider"] = provider
    if model:
        # Override all modules to use this provider/model
        for mod in llm_router.config.get("modules", {}):
            llm_router.config["modules"][mod]["provider"] = provider
            llm_router.config["modules"][mod]["model"] = model if model else None

# Status area
status_container = st.empty()
progress_bar = st.progress(0)
log_container = st.empty()

# Report display
report_container = st.empty()

if clear_btn:
    st.session_state.report_path = None
    st.session_state.report_content = None
    st.rerun()

if run_analysis and target_url:
    if not target_url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        log_lines = []

        def progress_callback(msg: str, pct: float):
            log_lines.append(msg)
            progress_bar.progress(pct / 100.0)
            log_container.info("\n".join(log_lines[-10:]))

        try:
            # Run the research
            status_container.info("🚀 Running research modules...")
            results = run_all(
                target_url=target_url,
                llm_complete=llm_complete,
                enabled_modules=enabled_modules,
                progress_callback=progress_callback,
            )

            # Write the report
            report_path = write_report(results, output_dir=output_dir)
            report_content = open(report_path).read()
            st.session_state.report_path = report_path
            st.session_state.report_content = report_content

            progress_bar.progress(100.0)
            status_container.success(f"✅ Report complete! Saved to:\n`{report_path}`")

        except Exception as exc:
            status_container.error(f"❌ Error: {exc}")

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
            st.info(f"📁 Report saved to:\n`{st.session_state.report_path}`")
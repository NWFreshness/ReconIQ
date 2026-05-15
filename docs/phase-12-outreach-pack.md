# Phase 12: Outreach Pack Generator

Goal: Generate ready-to-use sales assets from the intelligence report.

Review workflow: one PR per independently reviewable task/sub-phase.

## Sub-phase tracker

- [x] 12A — Define `OutreachPackSchema` with separate fields for each asset.
  - Status: Merged.
  - PR: https://github.com/NWFreshness/ReconIQ/pull/24
  - Branch: `feat/phase-12a-outreach-schema`
  - Merge commit: `96d8808014f0b30e4689467b256817b9824d76cd`
  - Verification: focused schema tests pass; full verification recorded in PR.

- [x] 12B — Add an `outreach` research module that consumes company profile, SEO, competitors, social/content, and SWOT.
  - Status: Merged.
  - PR: https://github.com/NWFreshness/ReconIQ/pull/25
  - Branch: `feat/phase-12b-outreach-module`
  - Merge commit: `5f975c2895d404a5f681e7df6625cd15113c6058`
  - Verification: focused module tests pass; full verification recorded in PR.
- [ ] 12C — Add module toggle support in backend schemas, API, CLI, Streamlit, and Next UI.
  - Status: In progress — local implementation and verification complete; not yet committed/pushed.
  - Branch: `feat/phase-12c-outreach-toggle`
  - Verification: `263 passed`; py_compile passed; `git diff --check` passed; `npm run build` passed.
- [ ] 12D — Add report section “Outreach Pack.”
- [ ] 12E — Add copy-friendly UI blocks in the analysis detail page.
- [ ] 12F — Add tests for module execution, validation, and report rendering.

## Outreach pack output fields

- `cold_email`
- `linkedin_dm`
- `discovery_call_opener`
- `proposal_outline`
- `follow_up_sequence`
- `data_confidence`
- `data_limitations`

# ReconIQ Feature Phase Roadmap

> Created: 2026-05-14
>
> Purpose: Convert the proposed feature ideas into sequenced implementation phases that can be tackled one at a time.

## Guiding Principles

- Keep the research engine framework-neutral; UI/API/CLI should call shared core services.
- Prefer local-first defaults where possible: SQLite, local files, local Ollama mode, local exports.
- Label evidence and confidence clearly; do not let the LLM invent facts without marking them as inferred.
- Each phase should end with fresh verification:
  - `.venv/bin/python -m pytest -q`
  - `cd web && npm run lint && npm run build`
  - `git diff --check`
- After frontend builds, restore generated `web/dist/` artifacts unless generated output is intentionally being committed.

---

## Phase Status Tracker

Update rules for future agents/models:
1. Before starting a phase, confirm the previous phase status here.
2. Mark a phase `[x]` only after code is implemented, committed, pushed, and merged.
3. Record branch name, test counts, and verification evidence.

- [x] Phase 10 — Evidence & Citations Viewer (PR #22, merged 2026-05-15)
- [x] Phase 11 — Competitor Comparison Matrix (PR #23, merged 2026-05-15)
- [x] Phase 12 — Outreach Pack Generator (PRs #25-30, merged 2026-05-15)
- [x] Phase 13 — Prospect Scoring (PRs #31-32, merged 2026-05-15)
- [x] Phase 14 — Dashboard Filters (PRs #33-34, merged 2026-05-15)
- [ ] Phase 15 — Saved Prospect Lists
  - Status: In progress — 15A merged (PR #35), 15B merged (PR #36), 15C done in 15B. Starting 15D.
  - Branch: `feat/phase-15d-prospect-lists-ui`
  - 15A: Database tables/models — DONE (merged PR #35)
  - 15B: CRUD API routes — DONE (merged PR #36)
  - 15C: Add/remove analyses endpoints — DONE in 15B
  - 15D: UI for creating lists and assigning analyses — COMPLETE locally.
  - 15E: List detail page — Pending
  - 15F: Tests — Covered by 15A/15B

---

## Phase 10: Evidence and Citations Viewer — DONE (PR #22, merged 2026-05-15)

**Goal:** Make every major report claim traceable to scraped pages, search results, or explicit LLM inference.

**Why:** ReconIQ becomes more trustworthy as a client-facing intelligence tool when users can see where claims came from.

**Files delivered:**

- `research/evidence.py` — `EvidenceItem` shape and `collect_scrape_evidence()` helper
- `research/schemas.py` — evidence fields added to module output schemas
- `research/{company_profile,competitors,seo_keywords,social_content}.py` — evidence collection wired into each module
- `report/writer.py` — "Evidence Sources" appendix section
- `web/src/components/EvidenceList.tsx` — expandable evidence UI component
- `tests/test_evidence.py` — 66 lines of unit tests
- `tests/test_report_writer.py` — evidence appendix rendering tests

**Sub-phases:**

- [x] 10A — Define a shared `EvidenceItem` shape with fields like `source_type`, `url`, `page_title`, `excerpt`, `selector_or_field`, `confidence`, and `module`.
- [x] 10B — Add evidence extraction from structured scrape data: title, meta description, headings, social links, contact info, JSON-LD, page excerpts.
- [x] 10C — Update research module outputs to include `evidence` arrays where possible.
- [x] 10D — Update report writer to add footnotes or an appendix called "Evidence Sources."
- [x] 10E — Update the analysis detail page to show expandable evidence under each module.
- [x] 10F — Add tests proving report claims preserve evidence metadata and missing evidence is labeled as inferred.

**Verification:**

- Unit tests for evidence item creation.
- Snapshot-ish tests for Markdown/HTML evidence appendix.
- Frontend lint/build.

---

## Phase 11: Competitor Comparison Matrix — DONE (PR #23, merged 2026-05-15)

**Goal:** Present competitor findings as a structured side-by-side table.

**Why:** The current competitor section is useful, but a comparison matrix makes gaps and positioning easier to scan.

**Files delivered:**

- `research/competitor_matrix.py` — `build_competitor_matrix()` with normalized column mapping
- `research/competitors.py` — matrix output wired into module
- `research/schemas.py` — matrix fields added to competitor output schema
- `report/writer.py` — Markdown table rendering for competitor matrix
- `web/src/components/CompetitorMatrix.tsx` — React component for detail page
- `tests/test_competitor_matrix.py` — 66 lines of unit tests
- `tests/test_report_writer.py` — matrix output tests

**Sub-phases:**

- [x] 11A — Extend competitor schema with normalized comparison fields: `pricing_tier`, `positioning`, `key_messaging`, `services`, `weaknesses`, `content_quality`, `seo_notes`.
- [x] 11B — Add a pure formatter that converts competitor results into a matrix model.
- [x] 11C — Render the matrix in Markdown and HTML/PDF exports.
- [x] 11D — Add a React `CompetitorMatrix` component for the detail page.
- [x] 11E — Add tests for empty competitors, one competitor, and multiple competitors with partial fields.

**Verification:**

- `tests/test_report_writer.py` for matrix output.
- Frontend lint/build.

---

## Phase 12: Outreach Pack Generator

**Goal:** Generate ready-to-use sales assets from the intelligence report.

**Outputs:**

- Cold email
- LinkedIn DM
- Discovery call opener
- 1-page proposal outline
- Follow-up sequence

**Likely files:**

- `research/outreach.py` new
- `research/schemas.py`
- `research/coordinator.py`
- `report/writer.py`
- `api/schemas.py`
- `web/src/app/page.tsx`
- `web/src/app/analysis/[id]/page.tsx`
- `tests/test_outreach.py` new

**Sub-phases:**

- [ ] 12A — Define `OutreachPackSchema` with separate fields for each asset.
- [ ] 12B — Add an `outreach` research module that consumes company profile, SEO, competitors, social/content, and SWOT.
- [ ] 12C — Add module toggle support in backend schemas, API, CLI, Streamlit, and Next UI.
- [ ] 12D — Add report section “Outreach Pack.”
- [ ] 12E — Add copy-friendly UI blocks in the analysis detail page.
- [ ] 12F — Add tests for module execution, validation, and report rendering.

**Verification:**

- Mocked LLM tests for outreach module.
- End-to-end mocked analysis includes outreach when enabled.

---

## Phase 13: Prospect Scoring

**Goal:** Score analyzed companies by agency opportunity quality.

**Suggested score dimensions:**

- Marketing gap severity
- AI automation fit
- Local/regional relevance
- Likely budget
- Ease of outreach
- Urgency signals
- Data confidence

**Likely files:**

- `research/prospect_score.py` new
- `research/schemas.py`
- `research/coordinator.py`
- `core/batch.py`
- `report/writer.py`
- `web/src/components/AnalysisCard.tsx`
- `web/src/app/analysis/[id]/page.tsx`

**Sub-phases:**

- [ ] 13A — Define deterministic scoring rubric and score schema.
- [ ] 13B — Add a scoring module that combines existing module outputs without requiring another LLM call at first.
- [ ] 13C — Add optional LLM explanation for the score, clearly separated from deterministic scoring.
- [ ] 13D — Show score badge on analysis cards and detail pages.
- [ ] 13E — Add batch summary sorting by score.
- [ ] 13F — Add tests for score calculation and edge cases with missing module data.

**Verification:**

- Pure unit tests for scoring math.
- Batch tests proving high-score prospects sort first.

---

## Phase 14: Report Dashboard Filters — DONE (PRs #33, #34, merged 2026-05-15)

**Goal:** Make the Next dashboard easier to navigate as the number of analyses grows.

**Filters:**

- Status
- Provider
- Date range
- Minimum prospect score
- Failed analyses only

**Files delivered:**

- `api/routes/analyses.py` — query params: status, provider, date_from, date_to, min_score, error_only
- `api/db.py` — SQL filtering in `list_jobs()`
- `api/schemas.py` — filter params in response models
- `web/src/lib/api.ts` — typed `listAnalyses()` with filter params
- `web/src/app/page.tsx` — filter state + URL query param persistence
- `web/src/components/DashboardFilters.tsx` — filter bar component

**Sub-phases:**

- [x] 14A — Add optional query params to `GET /analyses`.
- [x] 14B — Extend database query builder to filter by status, provider, format, date, and score if present.
- [x] 14C — Add typed API client support for filters.
- [x] 14D — Add a filter bar to the dashboard.
- [x] 14E — Persist filters in URL query params.
- [x] 14F — Add API and frontend tests for common filter combinations.

**Verification:**

- API tests for filter behavior.
- Frontend lint/build.

---

## Phase 15: Saved Prospect Lists

**Goal:** Allow users to group analyses into named prospect lists.

**Examples:**

- “Vancouver HVAC companies”
- “Clark County dental offices”
- “Cowlitz manufacturing leads”

**Likely files:**

- `api/db.py`
- `api/routes/prospect_lists.py` new
- `api/main.py`
- `api/schemas.py`
- `web/src/lib/api.ts`
- `web/src/app/page.tsx`
- `web/src/app/lists/[id]/page.tsx` new
- `web/src/components/ProspectListPicker.tsx` new

**Sub-phases:**

- [ ] 15A — Add database tables/models for lists and list memberships.
- [ ] 15B — Add CRUD API routes for prospect lists.
- [ ] 15C — Add endpoints to add/remove analyses from lists.
- [ ] 15D — Add UI for creating lists and assigning analyses.
- [ ] 15E — Add list detail page with filtered analyses and summary stats.
- [ ] 15F — Add tests for list CRUD and membership behavior.

**Verification:**

- API route tests.
- Frontend lint/build.

---

## Phase 16: Local-First Auth and Report Ownership

**Goal:** Add lightweight local user ownership without introducing a cloud auth provider.

**Why:** The app already has API-key auth, but reports are not user-owned. Local ownership makes shared/local deployments safer.

**Likely files:**

- `api/auth.py`
- `api/db.py`
- `api/schemas.py`
- `api/routes/auth.py` new
- `api/routes/analyses.py`
- `web/src/lib/api.ts`
- `web/src/app/login/page.tsx` new
- `web/src/app/layout.tsx`

**Sub-phases:**

- [ ] 16A — Define local users table with password hash, created date, and role.
- [ ] 16B — Add password hashing helpers using a vetted dependency.
- [ ] 16C — Add login endpoint returning a local session token or signed cookie.
- [ ] 16D — Add `owner_id` to analysis jobs and prospect lists.
- [ ] 16E — Restrict list/get/delete/report routes to owned records.
- [ ] 16F — Add simple login/logout UI.
- [ ] 16G — Add tests for auth, ownership filtering, and unauthorized access.

**Verification:**

- API auth tests.
- Manual local login smoke test.

---

## Phase 17: Monitoring and Scheduled Re-runs

**Goal:** Re-analyze prospects on a schedule and show what changed.

**Change types:**

- New competitors
- Changed positioning
- New social links
- SEO/title/meta changes
- New CTAs
- Score changes

**Likely files:**

- `api/db.py`
- `api/routes/schedules.py` new
- `api/worker.py`
- `core/services.py`
- `core/diffing.py` new
- `web/src/app/analysis/[id]/page.tsx`
- `web/src/components/ChangeTimeline.tsx` new

**Sub-phases:**

- [ ] 17A — Add analysis snapshot records so repeated runs can be compared.
- [ ] 17B — Add a pure diffing module for structured result changes.
- [ ] 17C — Add API routes for scheduling local re-runs.
- [ ] 17D — Implement a simple local scheduler loop or cron-compatible CLI command.
- [ ] 17E — Add UI for “rerun now” and schedule settings.
- [ ] 17F — Add timeline UI showing change summaries.
- [ ] 17G — Add tests for diff generation and schedule metadata.

**Verification:**

- Unit tests for structured diffs.
- API tests for schedule creation/listing.

---

## Phase 18: Cost Controls

**Goal:** Prevent accidental LLM/API overspend.

**Features:**

- Provider/model cost table
- Estimated token/cost per module
- Per-run budget cap
- Per-day budget cap
- Provider quota warnings
- “Local-only” hard block for cloud calls when enabled

**Likely files:**

- `llm/router.py`
- `llm/costs.py` new
- `core/settings.py`
- `config.yaml`
- `api/schemas.py`
- `web/src/app/page.tsx`
- `web/src/app/analysis/[id]/page.tsx`

**Sub-phases:**

- [ ] 18A — Add provider/model pricing config with conservative defaults.
- [ ] 18B — Estimate tokens before calls and log actual usage when providers return it.
- [ ] 18C — Add per-run budget checks before each module call.
- [ ] 18D — Add daily local budget tracking in SQLite or `.reconiq-cache/`.
- [ ] 18E — Show estimated cost before submitting an analysis.
- [ ] 18F — Show actual/estimated cost on completed analysis detail pages.
- [ ] 18G — Add tests for budget rejection and missing pricing fallback.

**Verification:**

- Mock LLM router tests proving budget caps block calls.
- UI build.

---

## Phase 19: Better Local Mode

**Goal:** Provide a clear local-only preset for users who want no cloud dependencies.

**Local-only behavior:**

- Use Ollama by default.
- Disable Firecrawl/search APIs.
- Disable cloud LLM providers.
- Keep all reports and cache local.
- Clearly label lower confidence when live search is disabled.

**Likely files:**

- `config.yaml`
- `core/settings.py`
- `llm/router.py`
- `research/search.py`
- `README.md`
- `web/src/app/page.tsx`
- `web/src/components/LocalModeBanner.tsx` new

**Sub-phases:**

- [ ] 19A — Add `local_only.enabled` config section.
- [ ] 19B — Enforce local-only restrictions in LLM router and search helpers.
- [ ] 19C — Add a visible UI banner when local mode is active.
- [ ] 19D — Add CLI flag `--local-only` for single and batch runs.
- [ ] 19E — Update README with Ollama setup and confidence caveats.
- [ ] 19F — Add tests proving cloud calls are blocked in local-only mode.

**Verification:**

- Router/search tests with local-only enabled.
- README command smoke checks where possible.

---

## Phase 20: CRM and Export Integrations

**Goal:** Move batch/prospect data into tools used for outreach and pipeline tracking.

**Initial targets:**

- CSV export
- Local SQLite prospect table
- Airtable optional export
- HubSpot optional export later

**Likely files:**

- `core/exporters.py` new
- `core/batch.py`
- `api/routes/exports.py` new
- `api/main.py`
- `web/src/app/page.tsx`
- `web/src/app/lists/[id]/page.tsx`
- `tests/test_exporters.py` new

**Sub-phases:**

- [ ] 20A — Add normalized prospect export model.
- [ ] 20B — Add CSV exporter for analyses and lists.
- [ ] 20C — Add local SQLite prospect table for deduped companies.
- [ ] 20D — Add API endpoint to export selected analyses/lists.
- [ ] 20E — Add UI export button and format selector.
- [ ] 20F — Add optional Airtable exporter behind env/config settings.
- [ ] 20G — Add tests for CSV shape, dedupe behavior, and missing optional credentials.

**Verification:**

- Exporter unit tests.
- API tests for export endpoint.

---

## Phase 21: Visual Report Builder

**Goal:** Create more polished, client-ready visual reports.

**Visual sections:**

- SWOT quadrant
- Competitor radar chart
- Content gap chart
- Prospect score badge
- Recommended automation roadmap

**Likely files:**

- `report/writer.py`
- `report/visuals.py` new
- `web/src/app/analysis/[id]/page.tsx`
- `web/src/components/report/*.tsx` new
- `DESIGN.md`
- `.streamlit/style.css` if Streamlit remains supported

**Sub-phases:**

- [ ] 21A — Define visual data models independent of rendering library.
- [ ] 21B — Add Markdown-compatible ASCII/table fallbacks for all visuals.
- [ ] 21C — Add HTML report visual components with inline CSS.
- [ ] 21D — Add PDF-safe styling for WeasyPrint.
- [ ] 21E — Add React visual components for the detail page.
- [ ] 21F — Add tests for report generation with visual sections enabled.

**Verification:**

- Report writer tests for Markdown/HTML/PDF output.
- Frontend lint/build.

---

## Recommended Implementation Order

1. **Phase 10 — Evidence and Citations Viewer**
   - Highest trust improvement; improves every future feature.

2. **Phase 13 — Prospect Scoring**
   - Unlocks better dashboard filters, batch prioritization, and outreach workflows.

3. **Phase 11 — Competitor Comparison Matrix**
   - High-value report improvement with contained scope.

4. **Phase 12 — Outreach Pack Generator**
   - Turns analysis into immediate agency sales assets.

5. **Phase 14 — Report Dashboard Filters**
   - Becomes more useful after scoring exists.

6. **Phase 15 — Saved Prospect Lists**
   - Supports real agency prospecting workflows.

7. **Phase 19 — Better Local Mode**
   - Aligns with local-first usage and gives a clean privacy posture.

8. **Phase 18 — Cost Controls**
   - Important before heavy usage or scheduled monitoring.

9. **Phase 17 — Monitoring and Scheduled Re-runs**
   - More valuable once evidence, scores, and lists exist.

10. **Phase 20 — CRM and Export Integrations**
    - Best after lists and scoring are in place.

11. **Phase 21 — Visual Report Builder**
    - Polishes deliverables after the data model stabilizes.

12. **Phase 16 — Local-First Auth and Report Ownership**
    - Do before multi-user deployment; can be earlier if sharing the app soon.

---

## Phase Tracker

| Phase | Feature | Status | Depends On |
|---|---|---|---|
| 10 | Evidence and Citations Viewer | Not started | Existing structured scraper |
| 11 | Competitor Comparison Matrix | Not started | Existing competitor module; ideally Phase 10 |
| 12 | Outreach Pack Generator | Not started | Existing SWOT; ideally Phase 10 |
| 13 | Prospect Scoring | Not started | Existing module outputs |
| 14 | Report Dashboard Filters | Not started | API DB; ideally Phase 13 |
| 15 | Saved Prospect Lists | Not started | API DB; dashboard |
| 16 | Local-First Auth and Report Ownership | Not started | API DB |
| 17 | Monitoring and Scheduled Re-runs | Not started | API DB; ideally Phase 10 and 13 |
| 18 | Cost Controls | Not started | LLM router |
| 19 | Better Local Mode | Not started | LLM router; search helpers |
| 20 | CRM and Export Integrations | Not started | Batch mode; ideally Phase 15 |
| 21 | Visual Report Builder | Not started | Report writer; stable schemas |

---

## Open Questions

- Should phases be implemented as PR-sized branches, one phase at a time?
- Should local-only mode be moved earlier because it matches the preferred deployment style?
- Should outreach generation use the same provider as analysis, or allow a separate cheaper/faster model?
- Should report visuals be generated server-side only, client-side only, or both?
- Should auth remain local-only permanently, or should cloud auth be an optional deployment profile later?

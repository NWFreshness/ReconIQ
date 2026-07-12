# ReconIQ Feature Phase Roadmap

> Created: 2026-05-14
> Last reconciled: 2026-07-12 (post PR #41 merge)
>
> Purpose: Sequenced post-MVP feature phases and the durable progress tracker for this project.
>
> **Source of truth for phases 10+:** this file (`FEATURE_PHASES.md`).
> **MVP phases 0–9:** historical detail in `docs/plan-v2.md` and `docs/enhancements.md` (all complete on `main`).
> **Product note:** ReconIQ is a separate product from Cascade. Possible future merge is intentional product strategy, not a current implementation dependency.

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
1. Before starting a phase, confirm the previous phase status here and on `main`/GitHub.
2. Mark a phase `[x]` only after code is implemented, committed, pushed, and merged.
3. Record PR numbers and merge dates. Keep the summary table at the bottom in sync with this list.
4. Do not treat unchecked sub-phase boxes in long-form sections as authoritative if this tracker says COMPLETE — fix the long-form section in the same PR when drift is found.

### Foundation (complete)

- [x] Phases 0–8 — MVP core (core services, modules, coordinator, report writer, UI, e2e) — see `docs/plan-v2.md`
- [x] Phase 9 enhancements (FastAPI, Next.js, Playwright, deep scrape, schemas, cache, exports, CLI, batch, search) — see `docs/enhancements.md`

### Feature phases 10–21

- [x] Phase 10 — Evidence & Citations Viewer (PR #22, merged 2026-05-15)
- [x] Phase 11 — Competitor Comparison Matrix (PR #23, merged 2026-05-15)
- [x] Phase 12 — Outreach Pack Generator (PRs #24–#30, merged 2026-05-15)
- [x] Phase 13 — Prospect Scoring (PRs #31–#32, merged 2026-05-15)
- [x] Phase 14 — Dashboard Filters (PRs #33–#34, merged 2026-05-15)
- [x] Phase 15 — Saved Prospect Lists (PRs #35–#38, merged 2026-05-15)
  - 15A models — PR #35
  - 15B/15C API CRUD + membership — PR #36
  - 15D list UI — PR #37
  - 15E list detail — PR #38
  - 15F tests — covered under 15A/15B API/DB tests
- [ ] Phase 16 — Local-First Auth and Report Ownership — **Not started**
- [ ] Phase 17 — Monitoring and Scheduled Re-runs — **Not started**
- [ ] Phase 18 — Cost Controls — **Not started**
- [ ] Phase 19 — Better Local Mode — **Not started**
- [ ] Phase 20 — CRM and Export Integrations — **Not started** (CSV/HTML/PDF export already exists from Phase 9F; this phase is CRM/Airtable-style integrations)
- [x] Phase 21 — Visual Report Builder (PR #39, merged 2026-05-15)

### Cross-cutting improvements (complete, not numbered as 10–21)

- [x] Search stack: Firecrawl primary + SerpAPI fallback (commits through main; keyless Firecrawl free tier PR #40, merged 2026-06-17)
- [x] SEO Tier 0 — measured on-page keyword seeds + `data_mode` provenance (PR #41, merged 2026-07-12)
  - Seeds from title/h1/h2/meta/anchors/subpages
  - Post-LLM injection of `seed_keywords` and `data_mode` (`hybrid` | `inferred_only`)
  - No paid keyword/volume/SERP API yet (SEO Tier 1 remains future work)

### Suggested next (not started)

1. SEO Tier 1 — measured keyword metrics / SERP sample via a pay-as-you-go API (e.g. DataForSEO), spend-capped
2. Phase 18 — Cost Controls (LLM + search spend caps)
3. Phase 17 — Monitoring / re-run diffs (agency workflow)
4. Phase 19 — Better Local Mode
5. Phase 16 — Local auth (only if multi-user)
6. Phase 20 — CRM integrations

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

## Phase 12: Outreach Pack Generator — DONE (PRs #24–#30, merged 2026-05-15)

**Goal:** Generate ready-to-use sales assets from the intelligence report.

**Outputs:**

- Cold email
- LinkedIn DM
- Discovery call opener
- 1-page proposal outline
- Follow-up sequence

**Files delivered:**

- `research/outreach.py`
- `research/schemas.py` (outreach pack schema)
- `research/coordinator.py` (module wiring + toggles)
- `report/writer.py` (Outreach Pack section)
- `web/src/components/OutreachBlock.tsx`
- `tests/test_outreach.py`, `tests/test_outreach_schema.py`

**Sub-phases:**

- [x] 12A — Define `OutreachPackSchema` with separate fields for each asset. (PR #24)
- [x] 12B — Add an `outreach` research module that consumes company profile, SEO, competitors, social/content, and SWOT. (PR #25)
- [x] 12C — Add module toggle support in backend schemas, API, CLI, and Next UI. (PR #26)
- [x] 12D — Add report section “Outreach Pack.” (PR #27)
- [x] 12E — Add copy-friendly UI blocks in the analysis detail page. (PR #28)
- [x] 12F — Add tests for module execution, validation, and report rendering. (PR #29)
- [x] Integration / UI fixes — PR #30

**Verification:**

- Mocked LLM tests for outreach module.
- Coordinator + UI integration merged on main.

---

## Phase 13: Prospect Scoring — DONE (PRs #31–#32, merged 2026-05-15)

**Goal:** Score analyzed companies by agency opportunity quality.

**Score dimensions (implemented):**

- Marketing gap severity
- AI automation fit
- Local/regional relevance
- Likely budget
- Ease of outreach
- Urgency signals
- Data confidence

**Files delivered:**

- `research/prospect_score.py`
- `research/schemas.py`
- `research/coordinator.py`
- `report/writer.py`
- `web/src/components/AnalysisCard.tsx` / report score visuals
- `tests/test_prospect_score.py`

**Sub-phases:**

- [x] 13A — Define deterministic scoring rubric and score schema. (PR #31)
- [x] 13B — Add a scoring module that combines existing module outputs without requiring another LLM call at first.
- [x] 13C — Optional LLM explanation separated from deterministic scoring (where present in pipeline).
- [x] 13D — Show score badge on analysis cards and detail pages.
- [x] 13E — Batch/list sorting support via score fields where applicable.
- [x] 13F — Tests for score calculation and edge cases with missing module data. (PR #32 pipeline)

**Verification:**

- Pure unit tests for scoring math on main.
- Full pipeline integration via PR #32.

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

## Phase 15: Saved Prospect Lists — DONE (PRs #35–#38, merged 2026-05-15)

**Goal:** Allow users to group analyses into named prospect lists.

**Examples:**

- “Vancouver HVAC companies”
- “Clark County dental offices”
- “Cowlitz manufacturing leads”

**Files delivered:**

- `api/db.py` (list models)
- `api/routes/prospect_lists.py`
- `api/schemas.py`
- `web/src/lib/api.ts`
- `web/src/components/ListManager.tsx`
- `web/src/app/lists/[id]/page.tsx`
- `tests/test_prospect_lists_api.py`, `tests/test_prospect_lists_db.py`

**Sub-phases:**

- [x] 15A — Add database tables/models for lists and list memberships. (PR #35)
- [x] 15B — Add CRUD API routes for prospect lists. (PR #36)
- [x] 15C — Add endpoints to add/remove analyses from lists. (PR #36)
- [x] 15D — Add UI for creating lists and assigning analyses. (PR #37)
- [x] 15E — Add list detail page with filtered analyses and summary stats. (PR #38)
- [x] 15F — Add tests for list CRUD and membership behavior. (API/DB tests under 15A/15B)

**Verification:**

- API/DB route tests on main.
- List UI pages present under `web/src/app/lists/`.

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

## Phase 21: Visual Report Builder — DONE (PR #39, merged 2026-05-15)

**Goal:** Create more polished, client-ready visual reports.

**Visual sections:**

- SWOT quadrant
- Competitor radar chart
- Content gap chart
- Prospect score badge
- Recommended automation roadmap

**Files delivered:**

- `report/writer.py`
- `report/visuals.py`
- `web/src/app/analysis/[id]/page.tsx`
- `web/src/components/report/*.tsx`
- `DESIGN.md`
- `tests/test_visuals.py`

**Sub-phases:**

- [x] 21A — Define visual data models independent of rendering library.
- [x] 21B — Add Markdown-compatible ASCII/table fallbacks for all visuals.
- [x] 21C — Add HTML report visual components with inline CSS.
- [x] 21D — Add PDF-safe styling for WeasyPrint.
- [x] 21E — Add React visual components for the detail page.
- [x] 21F — Add tests for report generation with visual sections enabled.

**Verification:**

- Report writer / visuals tests on main.
- Frontend report components under `web/src/components/report/`.

---

## SEO quality track (adjacent to numbered phases)

### SEO Tier 0 — DONE (PR #41, merged 2026-07-12)

Measured on-page keyword seeds and provenance labeling without paid SEO APIs.

- `research/seo_keywords.py` — `extract_keyword_seeds()`, prompt hardening, post-LLM `seed_keywords` / `data_mode` injection
- `research/schemas.py` — `KeywordSeed`, `data_mode`
- `report/writer.py` — seed rendering
- `tests/test_seo_tier0.py`

### SEO Tier 1 — Not started

Paid/measured keyword + SERP signals (candidate: DataForSEO), spend-capped per run, still label non-measured fields as inferred.

---

## Recommended Implementation Order (remaining only)

Completed through Phase 15 + Phase 21 + SEO Tier 0 + current search stack. Remaining priority:

1. **SEO Tier 1 — Measured keyword/SERP data**
   - Biggest remaining quality gap in SEO after Tier 0 seeds.

2. **Phase 18 — Cost Controls**
   - Important before heavy usage, batch runs, or scheduled monitoring (LLM + Firecrawl/SerpAPI).

3. **Phase 17 — Monitoring and Scheduled Re-runs**
   - High agency workflow value once scores, lists, and evidence exist.

4. **Phase 19 — Better Local Mode**
   - Clean local-only / Ollama posture.

5. **Phase 16 — Local-First Auth and Report Ownership**
   - Only when multi-user or shared deployment is real.

6. **Phase 20 — CRM and Export Integrations**
   - Beyond existing Markdown/HTML/PDF exports; CRM/Airtable-style sinks.

---

## Phase Tracker

| Phase | Feature | Status | Depends On | Evidence |
|---|---|---|---|---|
| 0–8 | MVP core | COMPLETE | — | `docs/plan-v2.md`, PRs #1–#9 |
| 9 | Post-MVP platform enhancements | COMPLETE | MVP | `docs/enhancements.md`, PRs #10–#21 |
| 10 | Evidence and Citations Viewer | COMPLETE | Structured scraper | PR #22 |
| 11 | Competitor Comparison Matrix | COMPLETE | Competitor module | PR #23 |
| 12 | Outreach Pack Generator | COMPLETE | SWOT + modules | PRs #24–#30 |
| 13 | Prospect Scoring | COMPLETE | Module outputs | PRs #31–#32 |
| 14 | Report Dashboard Filters | COMPLETE | API DB; scoring | PRs #33–#34 |
| 15 | Saved Prospect Lists | COMPLETE | API DB; dashboard | PRs #35–#38 |
| 16 | Local-First Auth and Report Ownership | Not started | API DB | — |
| 17 | Monitoring and Scheduled Re-runs | Not started | API DB; evidence; scoring | — |
| 18 | Cost Controls | Not started | LLM router; search providers | — |
| 19 | Better Local Mode | Not started | LLM router; search helpers | — |
| 20 | CRM and Export Integrations | Not started | Lists; scoring (CSV/HTML/PDF already from 9F) | — |
| 21 | Visual Report Builder | COMPLETE | Report writer; schemas | PR #39 |
| SEO-0 | Measured keyword seeds / data_mode | COMPLETE | ScrapeResult | PR #41 |
| SEO-1 | Measured keyword/SERP API | Not started | SEO-0 | — |
| Search | Firecrawl + SerpAPI fallback | COMPLETE | Competitor discovery | through PR #40 |

---

## Open Questions

- Should SEO Tier 1 land before Phase 18, or cost caps first if spend is already a concern?
- Should local-only mode (19) move earlier for privacy-first demos?
- Should outreach generation use the same provider as analysis, or allow a separate cheaper/faster model?
- Should auth remain local-only permanently, or should cloud auth be an optional deployment profile later?
- If ReconIQ and Cascade merge later, which system owns identity, jobs, and report storage?

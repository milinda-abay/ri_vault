# QA Test Plan

Source: `PBI_Manual_QA_Test_Plan.md` at the `ri_pbi_production` workspace root — "Manual QA Test Plan — Cross-Report Look, Feel & Behaviour Consistency."

The plan exists in **two formats that must be kept in sync**: the `.md` is the source of truth, and `PBI_Manual_QA_Test_Plan.xlsx` is the tester-facing workbook (Pass/Fail/N-A dropdowns on the result columns, one sheet per part, plus `Appendix A - Defects` and `Appendix B - Decisions`). Edit the `.md` first, then regenerate the workbook's text from it programmatically rather than retyping cells. Both files live in the **root** repo, which is not a parent of the 7 sub-repos — see [[Overview|RI PBI Production]].

> [!important] `PBI_Manual_QA_Test_Plan.md` is **not** absorbed into this vault
> This note summarises the plan; it does not replace it, and the plan is not being stubbed or retired the way the repo documentation is.
>
> The reason is a **regeneration contract the vault cannot participate in**. The `.md` is the declared source of truth for the `.xlsx`, and the workbook is regenerated from it programmatically — parse the markdown tables keyed on check ID, write into column B of the grid sheets, preserving the sheets' data validations and column widths. That contract requires the `.md` to sit beside the `.xlsx` in the root repo, in the exact table shape the parser expects. Moving the checks into a vault note would break the parse and let the two formats drift, which is the one failure the contract exists to prevent.
>
> So: **edit the plan in the repo, then regenerate the workbook, then update this note.** This note is the map, not the territory — treat any check ID, defect status or count here as a pointer back to the `.md`.

> [!warning] Point-in-time snapshot
> Reviewed and verified against the current report definitions on **2026-08-26**. Defect statuses in the plan itself were last re-verified **2026-08-25**. Verify against current PBIR/TMDL before relying on any specific finding.

## Purpose / scope

A **manual** QA pass across all 7 reports in [[Overview|RI PBI Production]], checked **page by page** (18 pages) so drift on a single page isn't masked by another page of the same report passing. It's manual because — per [[Shared Conventions]] — the workspace has no build/lint/test tooling; reports are edited via Power BI Desktop/`pbi-cli` and there's nothing to run in CI.

Deliberately scoped to **look, feel, and behaviour** consistency, plus production-readiness gates. It is **not** the row-level-security audit — that's [[RLS Alignment Audit]]. The plan carries only a light RLS smoke-check plus a per-report permissions matrix so the two don't duplicate each other.

**Explicitly out of scope**: deep source-to-report data reconciliation (control totals, tolerances, key/null handling) and formal performance benchmarking — both owned by the data engineering team.

## Structure

Three parts, run in order: **Part 1** (Desktop, per page) → **Part 2** (Desktop, report-level) → **Part 3** (Service, after publishing).

Checks use a **topic-prefixed ID** that means the same thing throughout, so the tables can be sorted and filtered by it. An `-S` in the ID means the check can only be run in the Service.

| Prefix | Area | Prefix | Area |
|---|---|---|---|
| `BRD` | Branding & theme | `DATA` | Data & refresh |
| `NAV` | Navigation | `ACC` | Accessibility |
| `FLT` | Filtering | `PERF` | Performance |
| `LAY` | Layout & canvas | `REL` | Release gates & sign-off |
| `VIS` | Visuals & data presentation | `PAR` | Desktop/Service parity |
| `EXP` | Export | `SEC` | Security (smoke check + RLS matrix) |

Per-page tables carry one column per page (18); report-level tables carry one per report (7). Page codes are short forms like `AST-Sum` (Asset Summary ★) and `FIN-PL` (Finance P/L); ★ marks a report's landing page.

## Page inventory

Confirmed 2026-08-26 — 18 pages, matching the plan's legend exactly.

| Report | Pages |
|---|---|
| [[iLab Utilisation]] | `Summary` ★ · `Users` · `Services` · `Equipment` |
| [[Finance]] | `Summary` ★ · `Finance P/L` · `Recoveries, Commercial & CAPEX` |
| [[Asset]] | `Summary` ★ · `Asset Report` |
| [[Awards]] | `Associated Research Income` ★ · `Research Awards Supported` |
| [[Publication]] | `Associated Publications` ★ · `Publications from PURE` |
| [[Survey]] | `Summary` ★ · `User Feedback for Services` · `User Feedback for Equipment` |
| [[Risk]] | `Summary` ★ · `Risk Register` |

Finance's hidden "Duplicate of Finance P/L" page has been **deleted**, so these 18 are the complete inventory. No hidden pages exist in any report.

## Known defects

Appendix A of the source doc lists **20 defects**, each found by inspecting the report definition files. As at the 2026-08-25 re-verification, **17 are fixed and 3 remain open**. Testers are told to check the appendix first and reference the defect ID rather than investigating from scratch — a "Fixed" defect that still reproduces means an old build is being tested.

The three still open:

| ID | Reports | What | Check |
|---|---|---|---|
| D-004 | [[Asset]] | Custom theme is named `Custom`, not `Monash Analytics V1` like the other six | `BRD-03` |
| D-005 | [[iLab Utilisation]], [[Finance]], [[Publication]], [[Survey]] | Base theme versions stale against a `CY26SU05` target — iLab `CY24SU06`, Finance `CY26SU04`, Publication `CY21SU07`, Survey `CY26SU02` | `BRD-04` |
| D-016 | All 7 | Only 1 of 166 visuals has alt text (the one that does is in [[Awards]]). Documented exception this pass, not a release blocker | `ACC-03` |

Appendix A also carries four lower-severity observations without defect IDs, and Appendix B lists open decisions for the report owner (number-format standards, table sort defaults, alt-text remediation owner, Finance's hidden Value Type Indicator filter, raw column names in the model).

## Review findings not yet folded into the plan

A full review on **2026-08-26** verified the plan against all 7 report definitions. The defect statuses, theme versions, page inventory, filter-pane widths, footers, and role structures all checked out as stated. The items below are corrections and gaps found during that review that are **still outstanding** in the source doc:

| # | Finding | Affects |
|---|---|---|
| 1 | [[Survey]]'s landing-page logo *does* carry a page-navigation link (pointing at itself). The plan states landing-page logos carry no link — true for the other 6 | `NAV-04`, D-001 |
| 2 | "Named admin roles exist only in iLab" is wrong — [[Finance RLS|Finance]] has 4 `*-ADMIN` roles and [[Survey RLS|Survey]] 3. They're faculty-scoped, but as written testers will wrongly mark `SEC-08-FIN`/`SEC-08-SUR` as N/A. Only `DVCRE-ADMIN`/`PVCRI-ADMIN` in [[iLab Utilisation RLS|iLab Utilisation]] are genuinely unfiltered | `SEC-08` |
| 3 | `DATA-03` names only [[Publication]] and [[Risk]] as carrying hardcoded local paths. [[Survey]] has one too — see [[Shared Conventions]], which records it as dormant rather than broken | `DATA-03` |
| 4 | [[Awards]]' info button is wired `PageNavigation` with an **empty** target — a dead link, the same class as D-001 but never logged. ([[Risk]]'s two buttons are fine: `WebUrl` to a Monash intranet PDF) | `NAV-03` |
| 5 | `PAR-S02` asks testers to compare drillthrough. **No drillthrough pages, tooltip pages, or bookmarks exist anywhere in the estate** | `PAR-S02`, `SEC-01` |
| 6 | `REL-05` requires "named remediation owners", but Appendix B records the alt-text owner as unassigned, and `ACC-03` says it isn't a blocker. The gate can't be met as written | `REL-05` |
| 7 | Lock-state drift the plan doesn't check: `Platform Governance Area` is **locked** in [[Publication]] and [[Risk]], **unlocked** in [[iLab Utilisation]] and [[Finance]]. `FLT-03` covers only `Capability Type` | `FLT-03` |
| 8 | Within [[iLab Utilisation]], the page-level `Record Type` filter is **locked on Equipment, unlocked on Services** | `FLT-05` |
| 9 | [[Asset]] carries an orphaned `RegisteredResources/reportThemeSchema.json`, undeclared in `resourcePackages` — parallel to the [[Awards]] `CY24SU10` observation already listed | Appendix A |
| 10 | `FLT-06` tells testers to use "Reset to default", which is a Service toolbar feature, but the check sits in Part 1 (Desktop) | `FLT-06` |

Four minor issues **were** fixed in both formats on 2026-08-26: an "A the detailed" typo, a missing comma in D-006's page name, two sentence-case instances of "Value Type Indicator", and a new observation recording that Publication's footer is the only one ending in a full stop and using the plural "models".

> The lower-severity observations list exists only in the `.md` — it has never been carried into the workbook, whose `Appendix A - Defects` sheet holds only the 20-row defect table.

## How to run it

1. Open each of the 7 reports in Power BI Desktop, and later the published version in the Service.
2. Work Part 1 → Part 2 → Part 3, filling each cell with ✅ Pass / ❌ Fail / ➖ N/A, leaving it blank until tested.
3. Most checks now **state the expected value outright**, and many state what each report does today — testers compare against a stated fact rather than judging by eye. Where no baseline is agreed, the check says so and asks for an observation instead of a pass/fail.
4. Record every Fail as a defect with an ID and evidence link; record every N/A's reason.
5. Log the test-run record at the start: tester, date, repo commit or published version, environment, browser/device, refresh timestamp, RLS identity, agreed load-time threshold.
6. Use the `.xlsx` for actual execution — the `.md` tables are 18 columns wide and need an editor with horizontal scroll.

## See also

- [[Shared Conventions]] — why there's no automated build/lint/test tooling, and the hardcoded-path gotcha behind `DATA-03`
- [[Overview|RI PBI Production]] — workspace structure and the 7 repos behind the page codes
- [[RLS Alignment Audit]] — the full RLS audit this plan's `SEC` checks deliberately don't duplicate
- [[Asset]], [[Awards]], [[Finance]], [[iLab Utilisation]], [[Publication]], [[Risk]], [[Survey]] — repos named in the findings above
- **Derived layer** (`graphify/`, never hand-edited): [[PBI_Manual_QA_Test_Plan]], [[PBI_Manual_QA_Test_Plan.xlsx]], `_COMMUNITY_Manual QA Test Plans` *(no node since export `0c73b0cf`)*, [[Documentation Review and Update Design]], [[Documentation Review and Update Implementation Plan]], [[Breadth-First Documentation Review]], [[_COMMUNITY_Documentation Validation]]

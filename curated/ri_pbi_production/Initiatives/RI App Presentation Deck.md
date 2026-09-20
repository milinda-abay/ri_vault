# RI App Presentation Deck

A single self-contained HTML file, `RI_App_Presentation.html`, that lets anyone at a meeting click through an overview of the whole RI App — all 7 `ri_pbi_*` Power BI reports — without opening Power BI Desktop or any live report. Lives at the workspace root of [[Overview|RI PBI Production]].

## Purpose and audience

Built for presenting the RI reporting suite to an audience (e.g. governance/stakeholder meetings) where the presenter wants to walk through each report's scope and page structure without switching between 7 live `.pbip` files. Designed around **~5 minutes of presentable content per report, followed by Q&A** — so content is deliberately kept to tight bullets, not prose.

Because it's a static summary opened straight from a browser (`file://`, offline, no dependencies), it works on any presenting machine regardless of whether Power BI Desktop or a Databricks connection is available.

## Design decisions

Source: `ri_pbi_production/docs/superpowers/specs/2026-07-31-ri-app-presentation-deck-design.md` (status: Approved).

- **Single self-contained HTML file** — inline `<style>`/`<script>`, no CDN, no build step, no server, no persistence. Opens directly in any browser, works offline.
- **Hash-based client-side routing** — `#landing` plus one hash per report (`#ilab_utilisation`, `#finance`, `#asset`, `#awards`, `#publication`, `#survey`, `#risk`). A small inline script shows/hides `<section class="page">` blocks based on `location.hash`, defaulting to `landing`.
- **Landing page**: Monash-styled header bar (logo embedded as base64, `#006DAE` accent bar), a short intro paragraph, and a 7-card grid — one card per report, each linking to its section. Card order is fixed by the design (not alphabetical): **iLab Utilisation → Finance → Asset → Awards → Publication → Survey → Risk**.
- **Per-report page**, one per repo: a persistent "← Back to overview" link, a title + short bullet summary (sourced from that repo's `<repo>_documentation.md` §1 Overview and its `CLAUDE.md` framing), and a page-by-page breakdown — one card per report page, in the page's actual `pageOrder` sequence from `pages.json`, each with a short inferred (not invented) summary of what it likely shows.
- **Theme**: Monash PVCRI theme, sourced read-only from `ri_reporting_template/Monash PVCRI.json` (outside the workspace, not modified) — primary accent `#006DAE`, active accent `#0A5599`, text `#242424`/`#616161`, backgrounds `#FFFFFF`/`#F5F5F5`/`#E6E6E6`, border `#D1D1D1`, good/bad accents `#0CA139`/`#CD2FB0` (used sparingly), links `#0078d4`, font stack `'DIN','Segoe UI Semibold','Segoe UI',Arial,sans-serif`.
- **Responsive**: flexbox/grid, relative units, `max-width: 100%` on the logo — grid collapses to fewer columns on narrower viewports, aimed at reading clearly on a projector or shared screen.
- **Explicitly out of scope**: no changes to any `ri_pbi_*` repo's TMDL/DAX/PBIR, no live data connection or embedded Power BI visuals (static presentational summary only), no changes to the theme source file.

## Plan/approach

Source: `ri_pbi_production/docs/superpowers/plans/2026-07-31-ri-app-presentation-deck.md`, executed via `superpowers:subagent-driven-development`/`executing-plans`. Built as 4 sequential tasks, each ending in a manual browser check (no build/test tooling exists for this artifact):

1. **Skeleton** — theme CSS variables, routing script, header chrome, base64-embed the Monash logo (source PNG from `ri_pbi_asset`'s `StaticResources`), empty `#landing` stub.
2. **Landing page content** — intro paragraph + the 7-card grid in the confirmed order.
3. **Report sections, batch 1** — `ilab_utilisation`, `finance`, `asset`, `awards`.
4. **Report sections, batch 2** — `publication`, `survey`, `risk` + a full manual verification pass (click through all 8 sections and back-links, check console errors, check both wide/projector and narrow/phone viewport widths).

Page-list content (which pages each report has, in order) was pre-gathered from each repo's `pages.json`/`page.json` before implementation started, to avoid the builder re-deriving it per task. Per-report summary bullets were written from each repo's `<repo>_documentation.md` and `CLAUDE.md` at implementation time rather than duplicated into the spec, to avoid drift between the spec and the source docs.

## Status/outcome

Implemented and present in the repo: `RI_App_Presentation.html` exists at the workspace root (44.5 KB). Git history at the workspace root shows the plan's 4 tasks landed as 4 separate commits, plus one follow-up fix commit (`Fix: Finance page-card name and route() fallback guard`) addressing a post-implementation bug — a small correction to the Finance page-card label and a defensive guard on the `route()` function's hash-fallback logic.

Note: the design spec and plan both state the workspace root "is not a git repository" and that there is nothing to commit — this was true when they were written (2026-07-31). It's since become a small git repo (see [[Overview|RI PBI Production]]) specifically to version this file and other root-level artifacts, which is why commits now exist for it. Both documents were annotated with a dated note to that effect on 2026-09-11.

> [!warning] The deck's page lists are stale (as at 2026-09-11)
> Two reports have changed their pages since the deck was built, and `RI_App_Presentation.html` has **not** been updated for either:
>
> | Report | Deck shows | Report now has |
> |---|---|---|
> | [[iLab Utilisation]] | a `Home Page` plus the other pages in their 2026-07-31 order | `Summary` · `Users` · `Services` · `Equipment` — `Home Page` removed, order changed |
> | [[Finance]] | the third page under its 2026-07-31 title | third page now titled `Recoveries, Commercial & CAPEX` |
>
> The current page inventory for all seven reports is the page legend in `PBI_Manual_QA_Test_Plan.md`, reproduced in [[QA Test Plan]]. The page lists embedded in the plan's Tasks 3–4 are stale in the same way. Anyone presenting from the deck should check those two reports' pages first.

## See also

- [[Overview|RI PBI Production]] — workspace structure; the root repo that now hosts this file
- [[Shared Conventions]] — PBIP layout and conventions each repo's summary content draws on
- [[iLab Utilisation]], [[Finance]], [[Asset]], [[Awards]], [[Publication]], [[Survey]], [[Risk]] — the 7 repos summarized by this deck, in landing-page card order
- **Derived layer** (`graphify/`, never hand-edited): [[RI App Presentation Deck Design]], [[RI App Presentation Deck Implementation Plan]], [[RI App Presentation Landing Page]]

# Publication Measures

All 21 report-wide DAX measures in [[Publication]] live in `key_measures`, plus 4 calculation items in `Time intelligence`. **None of them is hidden** — every measure and calculation item is visible in the Fields pane.

`key_measures` holds no data of its own. Its M partition decompresses a tiny base64/Deflate placeholder table and immediately drops the only column — Power BI Desktop's standard empty-measures-table pattern, per the centralised-measures convention in [[Shared Conventions]].

> [!note] Reconciled against [[ri_pbi_publication semantic model]] on 2026-09-19 (`ri_pbi_publication` @ `63ae148a`)
> Every DAX block below appears verbatim in the export, and the inventory matches: 21 measures in `key_measures` plus 4 calculation items. The export doesn't carry `isHidden` flags, so the visibility markers still rest on the 2026-09-01 TMDL read.

## What to know before using them

**The suffix tells you which fact you are counting.** `(app)`, `(pure)` and `(ilab)` are not decoration:

| Suffix | Fact | Meaning |
|---|---|---|
| `(app)` | `fact_research_output` | PURE research outputs by researcher |
| `(pure)` | `fact_pure` | PURE publication ↔ equipment/facility links |
| `(ilab)` | `fact_ilab_charges_award_researcher` | iLab facility charges |

Because the three facts sit at different grains with no common RI-platform path ([[Publication Data Model]]), `unique_publications (app)` and `unique_publications (pure)` are counting different things and will not agree. **Do not read a bare-sounding measure name as fact-agnostic** — `peer_reviewed_publications`, `researcher_publication` and `MNHS PUBLICATIONS` all carry a fact choice inside them without saying so in the name.

**`researcher_publication` is a relationship substitute, not a measure like the others.** `fact_research_output` has no join to `dim_ri_master_list`, so this measure reaches across to the iLab fact by hand: `CONTAINS` matches researcher-and-year pairs between two otherwise unrelated facts. It is the model's answer to a structural gap, and `Q1 %` and `MNHS Q1 %` both build on it — so that workaround propagates into anything downstream of them.

**Three measures have names that do not describe what the DAX computes.** These are recorded as-is; correcting them is separate work.

- `'% Publications Linked to RI'` filters PURE's generic `valid` flag. Nothing in it touches `dim_ri_master_list` or any RI-platform attribute, so despite the name it says nothing about RI linkage.
- `'MNHS Q1 %'` divides a numerator that is *not* MNHS-filtered (`researcher_publication`, the general RI-facility-user Q1 count) by an MNHS-specific denominator. Unless it is only ever placed in a visual where an MNHS filter is already applied, it does not compute MNHS's Q1 share in isolation.
- `'Q1 %'` computes a broader figure than its leftover variable suggests — see its entry below.

**Time intelligence only half-reaches PURE data.** `'Publications YoY %'` and all four `Time intelligence` calculation items key off `Calendar[cal_date]`, which is related **only** to `fact_ilab_charges_award_researcher`. Applied to a `(pure)` or `(app)` measure, they reach the data indirectly through the year-grain `output_year → cal_year` relationship, never through `cal_date`. Validate the behaviour before trusting any time comparison on a PURE-based measure.

## Measure inventory

All 21 measures, in TMDL source order. Multi-line definitions are given in full below the table.

| Measure | Built on | Definition |
|---|---|---|
| `'unique_pi (ilab)'` | iLab fact | `DISTINCTCOUNT(fact_ilab_charges_award_researcher[researcher_id])` — distinct researchers (PIs) appearing in iLab charges. |
| `'unique_awards (ilab)'` | iLab fact | `DISTINCTCOUNT(fact_ilab_charges_award_researcher[award_id])` — distinct awards billed against iLab usage. |
| `'unique_publications (app)'` | `fact_research_output` | `DISTINCTCOUNT(fact_research_output[output_id])` — the base figure most rate measures divide into. |
| `peer_reviewed_publications` | `fact_research_output` | `CALCULATE([unique_publications (app)], dim_research_output[PEER_REVIEWED_INDICATOR] = "Y")`. Feeds `'Peer-Reviewed Rate'`. |
| `publication_external_collaboration` | `fact_research_output` | `CALCULATE([unique_publications (app)], dim_research_output[EXTERNAL_COLLABORATION_INDICATOR] = "External Co-Authorship")`. Feeds `external_collaboration_rate`. |
| `external_collaboration_rate` | cross-fact | Share of publications with external collaboration, **restricted to researchers who also appear in the iLab charges fact** — see below. |
| `'validated_publication (pure)'` | `fact_pure` | `CALCULATE([unique_publications (pure)], fact_pure[valid] = "VALID")`. Depends on a measure defined later in the same table; DAX ordering does not matter for evaluation, only for TMDL layout. |
| `'% Publications Linked to RI'` | `fact_pure` | `DIVIDE([validated_publication (pure)], DISTINCTCOUNT(fact_pure[output_id]))` — the validated share of `fact_pure` rows. **Name does not match the logic** (see above). |
| `researcher_publication` | cross-fact | The `CONTAINS`-based workaround for the missing `fact_research_output → dim_ri_master_list` relationship — see below. |
| `'unique_publications_q1 (app)'` | `fact_research_output` | `CALCULATE([unique_publications (app)], fact_research_output[quality_outlet_jcr_q1] in {"QUALITY"})`. |
| `'Q1 %'` | cross-fact | `researcher_publication` over all in-context Q1 publications — carries a dead variable and an author's own `// Double check this` comment; see below. |
| `'unique_publications (pure)'` | `fact_pure` | `DISTINCTCOUNT(fact_pure[output_id])` — the PURE-fact equivalent of `'unique_publications (app)'`. |
| `'unique_publications_q1 (pure)'` | `fact_pure` | `CALCULATE([unique_publications (pure)], fact_pure[quality_outlet_jcr_q1] in {"QUALITY"})`. |
| `'Publications per RI Platform'` | `fact_pure` | `DIVIDE([validated_publication (pure)], DISTINCTCOUNT(dim_ri_master_list[CAPABILITY_CODE]))` — validated PURE publications per distinct RI capability in scope. Its doc comment states it "replaces the previously broken measure"; the predecessor is not preserved in TMDL. |
| `'Publications YoY %'` | `fact_pure` | Year-over-year change in PURE publications via `DATEADD` on `Calendar[cal_date]` — see below, and the time-intelligence caveat above. |
| `'Peer-Reviewed Rate'` | `fact_research_output` | `DIVIDE([peer_reviewed_publications], [unique_publications (app)])` — share of publications that are peer-reviewed. |
| `'International Collaboration Rate'` | `fact_research_output` | Share of publications with international external collaboration — see below. Parallel in structure to `'Peer-Reviewed Rate'`. |
| `'validated_publications_q1 (pure)'` | `fact_pure` | `CALCULATE([validated_publication (pure)], fact_pure[quality_outlet_jcr_q1] in {"QUALITY"})` — the validated-and-Q1 intersection. |
| `'Associated publication'` | cross-fact | Row-level flag returning `"Associated"` when the selected `fact_research_output[output_id]` also appears in `fact_pure` — see below. |
| `'MNHS PUBLICATIONS'` | `fact_research_output` | `CALCULATE([unique_publications (app)], fact_research_output[quality_outlet_jcr_q1] in {"QUALITY"}, dim_research_organisation[FACULTY_CODE] in {"MNHS"})` — Q1 count hardcoded to MNHS. A one-off for a specific faculty request: no equivalent exists for Science, Pharmacy or Engineering despite `FACULTY_CODE` supporting them. |
| `'MNHS Q1 %'` | cross-fact | `DIVIDE(key_measures[researcher_publication], [MNHS PUBLICATIONS])`. **Numerator is not MNHS-filtered** (see above). |

### external_collaboration_rate

```dax
CALCULATE(
    DIVIDE([publication_external_collaboration], [unique_publications (app)]),
    dim_researcher[RESEARCHER_ID] in VALUES(fact_ilab_charges_award_researcher[researcher_id]))
```

The share of a researcher's publications involving external collaboration — but scoped to researchers who have *used an RI facility*, not to all researchers in `dim_research_output`. That restriction is carried by `IN VALUES(...)` rather than a model relationship, because the two facts are linked only indirectly through the shared `dim_researcher` dimension.

### researcher_publication

```dax
 VAR reduce_table = CALCULATETABLE(
            fact_research_output,
            dim_researcher[RESEARCHER_ID] in VALUES(fact_ilab_charges_award_researcher[researcher_id]))

VAR result = 
 CALCULATE(
    [unique_publications_q1 (app)],
    FILTER(
        reduce_table,
        CONTAINS(
            fact_ilab_charges_award_researcher,
            fact_ilab_charges_award_researcher[researcher_id], fact_research_output[researcher_id],
            fact_ilab_charges_award_researcher[completion_year], fact_research_output[output_year]
        )
    )
)

RETURN
result
```

Its TMDL doc comment reads: *"Count of unique output_ids from fact_research_output, filtered to rows where the researcher_id and output_year match a researcher_id and completion_year pair in fact_ilab_charges_award_researcher."* This is the manual stand-in for the relationship the model does not have — it cross-matches researcher/year pairs between two unrelated facts, then counts Q1-quality publications among the matches. Feeds `'Q1 %'` and, in a probably unintended way, `'MNHS Q1 %'`.

### 'Q1 %'

```dax
VAR monash_publication = CALCULATE([unique_publications_q1 (app)], dim_research_output[OUTPUT_YEAR] in VALUES(fact_ilab_charges_award_researcher[completion_year])) // Double check this 

VAR percentage = DIVIDE([researcher_publication], [unique_publications_q1 (app)])

RETURN 
percentage
```

As implemented, this divides `researcher_publication` by **all** Q1 publications in `fact_research_output` within the current filter context. The `monash_publication` variable still computes a year-restricted denominator from `fact_ilab_charges_award_researcher[completion_year]`, but it is no longer used in the `DIVIDE` — so the measure expresses a broader "RI-facility-user Q1 share of all in-context Q1 publications" than the leftover variable name suggests. The author's own trailing comment on that line, `// Double check this`, is in the TMDL and has not been resolved.

### 'Publications YoY %'

```dax
VAR curr = [unique_publications (pure)]
VAR prev = CALCULATE ( [unique_publications (pure)], DATEADD ( 'Calendar'[cal_date], -1, YEAR ) )
RETURN DIVIDE ( curr - prev, prev )
```

Doc comment: *"Year-over-year percentage change in PURE publications. Compares the current period to the same period one year prior using the Calendar date."* A standard `DATEADD` pattern — but it depends on `Calendar[cal_date]`, which is related only to `fact_ilab_charges_award_researcher`, not to `fact_pure`. It therefore works only insofar as `fact_pure` is filtered indirectly through the `output_year → cal_year` relationship.

### 'International Collaboration Rate'

```dax
DIVIDE (
    CALCULATE ( [unique_publications (app)], dim_research_output[EXTERNAL_COLLABORATION_INTERNATIONAL_INDICATOR] = "Y" ),
    [unique_publications (app)]
)
```

Doc comment: *"Share of publications with international external collaboration (EXTERNAL_COLLABORATION_INTERNATIONAL_INDICATOR = Y)."*

### 'Associated publication'

```dax
VAR test = IF ( SELECTEDVALUE(fact_research_output[output_id]) IN VALUES(fact_pure[output_id]), "Associated", BLANK())

RETURN
test
```

A row-level flag intended for a table or matrix visual bound to `fact_research_output`: returns `"Associated"` when the selected output ID also appears among `fact_pure`'s output IDs, else blank. Since the two facts share no relationship, this is a set-membership check via `VALUES()`/`IN`, not a filter-propagated calculation — it only behaves sensibly where a single `output_id` is in context, hence `SELECTEDVALUE`.

## Time intelligence (calculation group)

`Time intelligence` is a calculation group, not a set of measures. Its items apply to whichever measure is currently selected in a visual, via `SELECTEDMEASURE()`. Display order is controlled by the `Ordinal` column — the only hidden column in the entire model.

All four items reference `'CALENDAR'[cal_date]` in uppercase; TMDL and DAX table names are case-insensitive, so this resolves to `Calendar` fine.

### Current

```dax
SELECTEDMEASURE()
```

Pass-through: returns the selected measure unmodified.

### YTD

```dax
VAR
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
max_day = {max('CALENDAR'[cal_date])}

VAR
fiscal_YTD = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(last_date)
)

RETURN
fiscal_YTD
```

Year-to-date for the selected measure, using `DATESYTD` anchored on the last non-blank date. The `max_day` variable is computed but never referenced in the `RETURN` — dead code inside the calculation item.

### 'PY YTD'

```dax
VAR
last_year_date =  DATEADD(LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE()),-1,YEAR)

VAR
last_ytd = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(last_year_date)
)

RETURN
last_ytd
```

The same YTD logic shifted back one year, for prior-year comparison.

### 'YTD (%)'

```dax
VAR
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
last_year_date =  DATEADD(LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE()),-1,YEAR)

VAR
fiscal_YTD = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(last_date)
)

VAR
last_ytd = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(last_year_date)
)

RETURN
DIVIDE((fiscal_YTD-last_ytd), last_ytd)
```

Percentage change between current YTD and prior-year YTD, carrying `formatStringDefinition = "0.00%"`.

## See also

- [[Publication]] — the repo entry note
- [[Publication Data Model]] — the tables and relationships these measures traverse
- [[Publication Gotchas]] — the dead code and open naming questions listed above, alongside the rest
- [[Shared Conventions]] — the centralised-measures convention
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_PURE Publication Records]], [[KeyMeasures]], [[fact_pure_1]], [[fact_research_output_1]], [[fact_ilab_charges_award_researcher_1]], [[dim_research_output]], [[dim_researcher_1]], [[Calendar_2]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[dim_ri_master_list_6]], [[dim_ri_master_list_2]]

# Survey Measures

**21 measures** in [[Survey]] — 20 in `Key measures`, plus one stray on `DIM_FACILITY`. There is no calculation group in this repo, and automatic time intelligence is disabled (`__PBI_TimeIntelligenceEnabled = 0`), so there is no date-comparison layer at all.

Full definitions are transferred below in TMDL declaration order.

> [!warning] "Hidden" below is the documentation's reading, not a TMDL flag (checked 2026-09-01)
> The transferred entries mark 18 of these measures hidden. **No measure in this model carries an `isHidden` flag in TMDL** — 17 in `Key measures` and 1 on `DIM_FACILITY` carry a `changedProperty = IsHidden` marker, which records that the property was changed at some point rather than asserting its current value. Full detail in [[Survey]]. Treat the visible/hidden split below as unverified against the live model.

> [!note] Reconciled against [[ri_pbi_survey semantic model]] on 2026-09-19 (`ri_pbi_survey` @ `403de545`)
> Every DAX block below appears verbatim in the export, and the inventory matches: 20 measures in `Key measures` and 1 on `DIM_FACILITY`, with no calculation group. The export doesn't carry `isHidden` flags, so the visibility markers still rest on the 2026-09-01 TMDL read.

## What to know before using them

**Only three measures reach the report**, and everything else is scaffolding beneath them: `Average Equipment Rating`, `Average Service Rating`, `Average Performance Rating`.

### None of those three averages a rating

This is the most important thing on this page. All three have the same shape — `AVERAGEX` over the distinct years in context — and all three average a **response count**, not a rating:

| Measure | Averages | Which is |
|---|---|---|
| `Average Equipment Rating` | `[Equipment]` | count of responses where `C_SOE` is `"EQUIPMENT"` or `"SERVICE,EQUIPMENT"` |
| `Average Service Rating` | `[Service]` | count of responses where `C_SOE` is `"SERVICE"` or `"SERVICE,EQUIPMENT"` |
| `Average Performance Rating` | `[Responses]` | count of all distinct responses |

Not one of them touches a rating column or a rating dimension. `Average Performance Rating` in particular touches neither `C_PERFORMANCE_SATISFY_RATING` nor `DIM_C_PERFORMANCE_SATISFY` — the source documentation flags that one, but the same mismatch runs through all three.

What they actually compute is **average responses per year**, segmented by what the respondent used. That may well be the intent — a volume trend smoothed across years — but the names say otherwise, and these are the three figures the report puts in front of readers. **Confirm with the model owner before quoting any of them as a satisfaction score.** Recorded, not changed.

They are also the only measures that read `Calendar` directly, through `VALUES('Calendar'[cal_year])` — notable given every `Calendar` column is reported hidden and visuals otherwise filter on `FACT_SURVEY[YEAR]`.

### `[Service]` and `[Equipment]` are built two different ways

Same intent, two mechanisms: `[Service]` wraps `CALCULATE([Responses], _service_selections)`, while `[Equipment]` uses `COUNTROWS(CALCULATETABLE(SUMMARIZE(...)))`. Both count distinct responses by `C_SOE`. `[Service]` additionally carries a commented-out `_temp` alternative using differently-cased literals (`"Services"`, `"Service,Instrument"`) that no longer match the data.

Note that `"SERVICE,EQUIPMENT"` responses count toward **both**, so the two do not partition the response set and will not sum to `[Responses]`.

### The percentage measures are not parallel

`'Service (%)'` and `'Equipment (%)'` look like siblings and are not:

- `'Service (%)'` frees its denominator of rating-scale filters with `REMOVEFILTERS` on `DIM_S_SL_SERVICE_SATISFACTION[S_LS]`, `DIM_SERVICE_COMPLETION[S_COMPLETION_SCHEDULE_RATING]` and `FACT_SURVEY[C_SOE]`, so a rating slicer cannot distort the response-rate denominator.
- **`'Equipment (%)'` does not apply the equivalent treatment.** With a rating-scale slicer active, the two measures respond differently.

`'Service (%)'` also computes a `denominator_responses` variable it never references — dead code from an earlier version, and easy to mistake for the live denominator when reading.

### Dead and broken measures

- **`'Comments Selected facility'`** returns `BLANK()`. Its real body is commented out and references a `facility_code_lvl1` column that no longer exists.
- **`'Selected service communication'`** reads `DIM_SERVICE_COMMUNICATION`, which has no relationship to anything — so it sits outside the filter graph entirely. Neither it nor its table appears in any visual.
- **`count_row`** is a plain `COUNTROWS(FACT_SURVEY)` referenced by nothing. A leftover sanity check.
- **`DIM_FACILITY[Measure]`** reads `SELECTEDVALUE(DIM_FACILITY[survey_facility_id])` — **a column that does not exist** on that table (the real one is `SURVEY_CAPABILITY_ID`). Broken as written, and attached to a dimension rather than `Key measures`, against convention.

That is four of 21 measures dead or broken. See [[Survey]].

### `'Selected Capability'` depends on the bidirectional relationship

It reads a facility name back out with `SELECTEDVALUE(DIM_FACILITY[SURVEY_CAPABILITY_ID])` from `FACT_SURVEY`-side filters. That only works because `FACT_SURVEY` ↔ `DIM_FACILITY` is bidirectional — the one such relationship in the model. See [[Survey Data Model]].

## Measures

### Responses — *hidden (building-block measure)*

```dax
VAR _responses =
    DISTINCTCOUNT ( FACT_SURVEY[RESPONSEID] )
VAR result =
    IF ( ISBLANK ( _responses ), 0, _responses )
RETURN
    result
```

Counts distinct survey responses in the current filter context (defaulting to 0 rather than blank). This is the base "how many people responded" figure that most other measures — `Service`, `'Response (%)'`, `'Completed survey'`, `'Completed (%)'` — build on.

### Service — *hidden (building-block measure; feeds visible `Average Service Rating`)*

```dax
VAR _service_selections =
    CALCULATETABLE (
        SUMMARIZE ( FACT_SURVEY, FACT_SURVEY[RESPONSEID], FACT_SURVEY[C_SOE] ),
        FACT_SURVEY[C_SOE] IN { "SERVICE", "SERVICE,EQUIPMENT" }
    )
VAR _service_responses =
    CALCULATE ( [Responses], _service_selections )
// VAR _temp =
//     COUNTROWS (
//         CALCULATETABLE (
//             SUMMARIZE ( FACT_SURVEY, FACT_SURVEY[ResponseId], FACT_SURVEY[C_SOE] ),
//             FACT_SURVEY[C_SOE] IN { "Services", "Service,Instrument" }
//         )
//     )
RETURN
    _service_responses
```

Counts distinct responses where `C_SOE` indicates the respondent used a service (`"SERVICE"` or `"SERVICE,EQUIPMENT"`). The commented-out `_temp` variable is a dead alternative version using different (now-incorrect-cased) literal values — leftover from earlier development, unused. Feeds `'Service (%)'` and the visible `Average Service Rating`.

### count_row — *hidden (appears unused elsewhere)*

```dax
COUNTROWS ( FACT_SURVEY )
```

Plain row count of `FACT_SURVEY`. Not referenced by any other measure in `Key measures` — likely a leftover debug/sanity-check measure.

### Equipment — *hidden (building-block measure; feeds visible `Average Equipment Rating`)*

```dax
COUNTROWS (
    CALCULATETABLE (
        SUMMARIZE ( FACT_SURVEY, FACT_SURVEY[RESPONSEID], FACT_SURVEY[C_SOE] ),
        FACT_SURVEY[C_SOE] IN { "EQUIPMENT","SERVICE,EQUIPMENT" }
    )
)
```

Counts distinct responses where `C_SOE` indicates the respondent used equipment (`"EQUIPMENT"` or `"SERVICE,EQUIPMENT"`). Feeds `'Equipment (%)'` and the visible `Average Equipment Rating`.

### Response (%) — *hidden*

```dax
VAR current_year =
    SELECTEDVALUE ( FACT_SURVEY[YEAR] )
VAR numerator = [Responses]
VAR denominator_year =
    CALCULATE (
        [Responses],
        ALLSELECTED ( FACT_SURVEY ),
        FACT_SURVEY[YEAR] = current_year
    )
VAR denominator_all =
    CALCULATE ( [Responses], ALLSELECTED ( FACT_SURVEY ) )
VAR denominator =
    IF ( ISBLANK ( current_year ), denominator_all, denominator_year )
VAR result =
    DIVIDE ( numerator, denominator )
RETURN
    result
```

Shows the selected slice of `[Responses]` as a percentage of all responses in the selected year (or the grand total if no single year is selected), ignoring finer filters within the visual (`ALLSELECTED`). Same "percentage of selected total" pattern as `ri_pbi_asset`'s `Proportion of Total Cost`.

### Service (%) — *hidden*

```dax
VAR current_year =
    SELECTEDVALUE ( FACT_SURVEY[YEAR] )


VAR denominator_responses = CALCULATE('Key measures'[Responses], REMOVEFILTERS(DIM_S_SL_SERVICE_SATISFACTION[S_LS]), REMOVEFILTERS(DIM_SERVICE_COMPLETION[S_COMPLETION_SCHEDULE_RATING]))
VAR denominator_table =
    CALCULATETABLE (
        SUMMARIZE ( ALLSELECTED ( FACT_SURVEY ), FACT_SURVEY[RESPONSEID], FACT_SURVEY[C_SOE] ),
       REMOVEFILTERS(FACT_SURVEY[C_SOE])
    )

VAR numerator = [Service]
VAR denominator_year =
    CALCULATE (
        [Responses],
        denominator_table,
        FACT_SURVEY[YEAR] = current_year
    )
VAR denominator_all =
    CALCULATE ( [Responses], denominator_table )
VAR denominator =
    IF ( ISBLANK ( current_year ), denominator_all, denominator_year )
VAR result =
    DIVIDE ( numerator, denominator )
RETURN
    result
```

Shows `[Service]` (distinct service-using responses) as a percentage of all responses for the selected year/total, with the denominator explicitly freed of any `S_LS`/`S_COMPLETION_SCHEDULE_RATING` rating filters and of the `C_SOE` filter itself (`REMOVEFILTERS`), so a rating-scale slicer selection on the service-satisfaction dimensions doesn't distort the response-rate denominator. `denominator_responses` is computed but never used in the `RETURN` — dead variable, likely a leftover from an earlier version of the formula.

### Equipment (%) — *hidden*

```dax
VAR current_year =
    SELECTEDVALUE ( FACT_SURVEY[YEAR] )
VAR numerator = [Equipment]
VAR denominator_year =
    CALCULATE (
        [Responses],
        ALLSELECTED ( FACT_SURVEY ),
        FACT_SURVEY[YEAR] = current_year
    )
VAR denominator_all =
    CALCULATE ( [Responses], ALLSELECTED ( FACT_SURVEY ) )
VAR denominator =
    IF ( ISBLANK ( current_year ), denominator_all, denominator_year )
VAR result =
    DIVIDE ( numerator, denominator )
RETURN
    result
```

Same pattern as `'Response (%)'` but for `[Equipment]` — the percentage of responses in the selected year/total that used equipment. Note this one does **not** apply the same `REMOVEFILTERS` treatment that `'Service (%)'` does, an inconsistency between the two otherwise-parallel measures.

### Average completion Time — *hidden*

```dax
CALCULATE (
    AVERAGE ( FACT_SURVEY[TOTAL_MINUTES] ),
    FACT_SURVEY[TOTAL_MINUTES] < 60
)
```

Average survey completion time in minutes, excluding responses that took an hour or more (likely abandoned sessions left open rather than genuine completion times).

### Comments Selected facility — *hidden (dead — always returns BLANK)*

```dax
BLANK()
// CONCATENATE (
//     "Comments for ",
//     SELECTEDVALUE (
//         FACT_SURVEY[facility_code_lvl1],
//         "more than one facility selected."
//     )
// )
```

The live expression is simply `BLANK()` — the original logic (a dynamic "Comments for X" title referencing a `facility_code_lvl1` column that no longer exists) is commented out. This measure is vestigial and always evaluates to blank regardless of filter context.

### Selected Capability — *hidden*

```dax
SELECTEDVALUE (
    DIM_FACILITY[SURVEY_CAPABILITY_ID],
    "More than one facility selected."
)
```

Returns the single selected facility code if exactly one is in context (via the bidirectional `FACT_SURVEY`↔`DIM_FACILITY` relationship, this also responds to fact-side filters), otherwise a fallback message — typical building block for a dynamic report title/subtitle.

### Selected service communication — *hidden (disconnected — see [[Survey Data Model]])*

```dax
SELECTEDVALUE ( DIM_SERVICE_COMMUNICATION[SORT_ORDER] )
```

Reads back the selected `SORT_ORDER` from `DIM_SERVICE_COMMUNICATION`, but since that table has no relationship to `FACT_SURVEY` or any other table, this measure is functionally disconnected from the rest of the model's filter context. Not used in any report visual.

### Responses (all) — *hidden*

```dax
CALCULATE ( [Responses], REMOVEFILTERS ( FACT_SURVEY[FACILITY_ID] ) )
```

`[Responses]` with any facility filter removed — total responses across all facilities, ignoring the currently selected facility/facilities. Feeds `'Response % (all)'`.

### Response % (all) — *hidden*

```dax
VAR current_year =
    SELECTEDVALUE ( FACT_SURVEY[YEAR] )
VAR numerator = [Responses (all)]
VAR denominator_year =
    CALCULATE (
        [Responses (all)],
        ALLSELECTED ( FACT_SURVEY ),
        FACT_SURVEY[YEAR] = current_year,
        REMOVEFILTERS ( FACT_SURVEY[FACILITY_ID] )
    )
VAR denominator_all =
    CALCULATE (
        [Responses (all)],
        ALLSELECTED ( FACT_SURVEY ),
        REMOVEFILTERS ( FACT_SURVEY[FACILITY_ID] )
    )
VAR denominator =
    IF ( ISBLANK ( current_year ), denominator_all, denominator_year )
VAR result =
    DIVIDE ( numerator, denominator )
RETURN
    result
```

Same "percentage of selected year/total" pattern as `'Response (%)'`, but computed with facility filters removed throughout — a facility-agnostic response-rate percentage, useful for comparing a facility's response volume against the whole-of-suite total.

### Completed survey — *hidden*

```dax
CALCULATE ( [Responses], FACT_SURVEY[FINISHED] = TRUE() )
```

Counts responses where `FINISHED = TRUE`, i.e. respondents who completed the entire survey rather than abandoning partway through. Feeds `'Completed (%)'`.

### Completed target — *hidden*

```dax
DIVIDE ( [Responses], 4 / 3 )
```

`[Responses]` divided by 4/3 (≈1.333), i.e. `[Responses] × 0.75` — likely a target-line reference value for a KPI/gauge visual (e.g. "aim for at least 75% of last period's response count"), though the specific business rationale for the 4/3 divisor isn't stated anywhere in the model — purpose of the exact ratio unclear, review with model owner.

### visible years — *hidden*

```dax
VAR _years =
    CONCATENATEX ( VALUES ( 'Calendar'[cal_year] ), 'Calendar'[cal_year], "," )

RETURN
    _years
```

Concatenates every distinct `Calendar[cal_year]` currently in context into a comma-separated string (e.g. "2022,2023,2024") — typical pattern for a dynamic report title/subtitle showing which years are represented in the current view.

### Completed (%) — *hidden*

```dax


VAR
numerator = [Completed survey]

VAR
denominator = [Responses]

VAR
result = DIVIDE(numerator,denominator)

RETURN
result
```

Completion rate: `[Completed survey]` (finished responses) divided by `[Responses]` (all responses) in the current filter context.

### Average Equipment Rating — *visible*

```dax

AVERAGEX(
    VALUES('Calendar'[cal_year]), 
    [Equipment]
)
```

Averages `[Equipment]` (the equipment-usage response count) across each distinct year in context — an average-per-year figure rather than a straight total, smoothing out year-to-year volume differences. Depends on `Calendar[cal_year]`, which is otherwise hidden in the Fields pane (see [[Survey Data Model]]) — this measure is one of the few things that actually reads `Calendar` directly.

### Average Service Rating — *visible*

```dax

AVERAGEX(
    VALUES('Calendar'[cal_year]), 
    [Service]
)
```

Same per-year averaging pattern as `Average Equipment Rating`, applied to `[Service]` (the service-usage response count).

### Average Performance Rating — *visible*

```dax

AVERAGEX(
    VALUES('Calendar'[cal_year]), 
    [Responses]
)
```

Same per-year averaging pattern again, but applied to `[Responses]` (total response count) rather than anything performance-specific. **Caveat**: despite its name, this measure does not touch `C_PERFORMANCE_SATISFY_RATING`/`DIM_C_PERFORMANCE_SATISFY` at all — it's a per-year average of total response volume, not a performance-satisfaction score. The name appears to be a mismatch with the underlying logic; worth confirming with the model owner whether this is intentional (e.g. "Performance" here means "response performance/volume") or whether it should be averaging a performance-rating measure instead.

## See also

- [[Survey]] — the repo entry note
- [[Survey Data Model]] — the tables and relationships these measures read
- [[Survey RLS]] — the role roster on `DIM_FACILITY`
- [[Shared Conventions]] — why measures are centralised in one table
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Selected Survey Facility]], [[FACT_SURVEY]], [[DIM_FACILITY]], [[DIM_C_PERFORMANCE_SATISFY]], [[Calendar_3]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[DIM_FACILITY_2]]

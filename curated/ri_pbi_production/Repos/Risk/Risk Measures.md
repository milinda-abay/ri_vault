# Risk Measures

**19 measures** in [[Risk]] — 18 in `KeyMeasures`, one on `dim_likelihood_impact` — plus **4 calculation items** in `Time intelligence`. Sixteen measures are visible; three are hidden.

Full definitions are transferred below in source order, followed by the calculation group.

> [!note] Reconciled against [[ri_pbi_risk semantic model]] on 2026-09-19 (`ri_pbi_risk` @ `75df1b25`)
> Every DAX block below appears verbatim in the export, and the inventory matches: 18 measures in `KeyMeasures`, 1 on `dim_likelihood_impact`, plus 4 calculation items. `USERELATIONSHIP` appears only in `Inherent Risk` and `Post Mitigation Active Risks`, as described. The export doesn't carry `isHidden` flags, so the visibility markers still rest on the 2026-09-01 TMDL read.

## What to know before using them

**`Total Risks` is the root of nearly everything.** It is `DISTINCTCOUNT(fact_risk_register[RECORD_ID])`, and `Active Risks`, `Archived Risks`, `Eliminated Risks`, `High`/`Medium`/`Low`/`Extreme Risks` all re-filter it with `CALCULATE`. Change it and everything moves.

Note the fact is **one row per risk record *version***, so the `DISTINCTCOUNT` on `RECORD_ID` — rather than `COUNTROWS` — is what collapses versions down to risks. A new count measure must do the same or it will count history.

**"Active" means `RISK_STATUS = "Monitor"`.** That string is the model's convention for a risk still being tracked, hardcoded into `Active Risks` and `Post Mitigation Active Risks`. It is not derived from `dim_risk_status`, so a status rename upstream breaks both silently.

### Two measures flip relationships, and they flip different ones

This is where the model's inherent-versus-residual wrinkle ([[Risk Data Model]]) surfaces in DAX. Both measures use `USERELATIONSHIP`, on different dimensions and in opposite directions:

| Measure | Activates | Effect |
|---|---|---|
| `Inherent Risk` | `dim_risk_rating[Risk rating]` ↔ `INHERENT_RISK_RATING` | Counts active risks by their **pre**-mitigation rating instead of the default residual one |
| `Post Mitigation Active Risks` | `dim_likelihood[Likelihood]` ↔ `LIKELIHOOD_AFTER_MITIGATION` **and** `dim_impact[Impact]` ↔ `IMPACT_AFTER_MITIGATION` | Makes likelihood and impact slicers filter by **post**-mitigation values instead of the default pre-mitigation ones |

They pull in opposite directions because the defaults do. `dim_risk_rating` defaults to residual, so `Inherent Risk` reaches back to inherent; `dim_impact` and `dim_likelihood` default to inherent, so `Post Mitigation Active Risks` reaches forward to post-mitigation.

**Anything new that mixes rating with likelihood or impact needs both fixes, or neither.** A measure that activates one and not the other silently compares a residual rating against a pre-mitigation likelihood.

### `Risk Rating Reduction` only works per-rating

It compares residual against inherent counts across the three worst tiers — `Extreme`, `High`, `Medium` — and negates the result so a genuine reduction reads positive.

Its final `IF` blanks the whole measure unless **exactly one** `dim_risk_rating[Risk rating]` value is in context, because `SELECTEDVALUE` returns blank on zero or multiple values. **It is meaningless at a grand total and will show empty there by design** — not a bug, and not something to "fix" by removing the guard.

### `colour_value` is not really a measure about risk

`SUM(dim_likelihood_impact[colour_code])` over the 25-row bridge table, driving conditional-format colour on the risk-matrix heatmap. Because `dim_likelihood_impact` has no path to the fact ([[Risk Data Model]]), **this measure does not respond to any filter on the register** — it colours the scale, not the data.

It is also the model's only measure defined outside `KeyMeasures`, against the suite-wide convention. See [[Risk]].

### The calculation group anchors on data, not today

`Current`, `YTD`, `PY YTD` and `YTD (%)` all anchor on `LASTNONBLANK('Calendar'[cal_date], ...)` — the latest date in context that has data — rather than `TODAY()`, over an Australian July-start fiscal year. So "year to date" tracks the register's latest activity, not the wall clock, and a stale refresh silently shifts the window rather than showing a gap.

`YTD` also computes a `max_day` variable it never references — the same dead leftover [[Publication]] and [[Awards]] carry in their own `YTD` items.

## Measures

### Total Risks — *visible*

```dax
DISTINCTCOUNT ( fact_risk_register[RECORD_ID] )
```

Total number of unique risk records in the current filter context. Per its doc comment: *"Total number of unique risks in the register."* This is the base count every other risk-count measure (`Active Risks`, `High Risks`, etc.) builds on via `CALCULATE`.

### Active Risks — *visible*

```dax
CALCULATE ( [Total Risks], fact_risk_register[RISK_STATUS] = "Monitor" )
```

Per its doc comment: *"Number of risks with status Monitor (active risk)."* Re-filters `Total Risks` to rows where `RISK_STATUS = "Monitor"` — the convention this model uses for "still active/being tracked."

### Archived Risks — *hidden*

```dax
CALCULATE ( [Total Risks], fact_risk_register[ISINARCHIVEDSTATUS] = "True" )
```

Per its doc comment: *"Number of risks that have been archived."* Filters `Total Risks` to `ISINARCHIVEDSTATUS = "True"` (note: this column is typed as `string`, not `boolean`, so the comparison is a text match). No reason for hiding is stated in the source; likely not currently bound to a visual (consistent with the pattern of hidden-but-functional measures seen elsewhere in the RI suite).

### Eliminated Risks — *hidden*

```dax
CALCULATE ( [Total Risks], fact_risk_register[RISK_STATUS] = "Eliminated" )
```

Per its doc comment: *"Number of risks that have been eliminated."* Filters `Total Risks` to `RISK_STATUS = "Eliminated"`. No reason for hiding stated in source.

### High Risks — *visible*

```dax
CALCULATE ( [Total Risks], fact_risk_register[RESIDUAL_RISK_RATING] = "High" )
```

Per its doc comment: *"Number of risks rated High after mitigation."* Uses the **active** `RESIDUAL_RISK_RATING` field (post-mitigation), so this reflects current, residual exposure — not the raw/inherent rating.

### Medium Risks — *visible*

```dax
CALCULATE ( [Total Risks], fact_risk_register[RESIDUAL_RISK_RATING] = "Medium" )
```

Per its doc comment: *"Number of risks rated Medium after mitigation."* Same pattern as `High Risks`.

### Low Risks — *visible*

```dax
CALCULATE ( [Total Risks], fact_risk_register[RESIDUAL_RISK_RATING] = "Low" )
```

Per its doc comment: *"Number of risks rated Low after mitigation."* Same pattern as `High Risks`. Note there is no equivalent visible measure for the `"Extreme"` or `"Unknown"` rating values from `dim_risk_rating` alongside this trio — `Extreme Risks` exists separately, further down, and no `Unknown Risks` measure exists at all.

### % High Residual Risk — *hidden*

```dax
DIVIDE ( [High Risks], [Total Risks], 0 )
```

Per its doc comment: *"Percentage of risks rated High after mitigation."* `High Risks` as a share of `Total Risks`, with a `0` fallback via `DIVIDE` to avoid divide-by-zero blanks. No reason for hiding stated in source.

### Avg Inherent Risk Score — *visible*

```dax
AVERAGE ( fact_risk_register[RISK_SCORE] )
```

Per its doc comment: *"Average inherent (pre-mitigation) risk score."* Straight average of the pre-mitigation `RISK_SCORE` column across the filter context.

### Avg Residual Risk Score — *visible*

```dax
AVERAGE ( fact_risk_register[RESIDUAL_RISK_SCORE] )
```

Per its doc comment: *"Average residual (post-mitigation) risk score."* Straight average of the post-mitigation `RESIDUAL_RISK_SCORE` column.

### Avg Risk Reduction — *visible*

```dax
[Avg Inherent Risk Score] - [Avg Residual Risk Score]
```

Per its doc comment: *"Average reduction in risk score achieved through controls."* Simple difference between the two average-score measures above — shows how much, on average, controls/mitigation are reducing risk scores.

### % Risk Reduction — *visible*

```dax
DIVIDE ( [Avg Risk Reduction], [Avg Inherent Risk Score], 0 )
```

Per its doc comment: *"Percentage reduction in risk score via controls."* Expresses `Avg Risk Reduction` as a percentage of the starting (inherent) score, with a `0` fallback.

### Extreme Risks — *visible*

```dax
CALCULATE (
    [Total Risks],
    fact_risk_register[RESIDUAL_RISK_RATING] = "Extreme"
)
```

No doc comment. Filters `Total Risks` to `RESIDUAL_RISK_RATING = "Extreme"` — the top rating tier from `dim_risk_rating`, not covered by the `High`/`Medium`/`Low` trio above.

### Inherent Risk — *visible*

```dax
CALCULATE (
    [Active Risks],
    USERELATIONSHIP ( dim_risk_rating[Risk rating], fact_risk_register[INHERENT_RISK_RATING] )
)
```

No doc comment. Recomputes `Active Risks` but swaps the active `dim_risk_rating` relationship for the (normally inactive) `INHERENT_RISK_RATING` one via `USERELATIONSHIP` — i.e. this measure answers "how many active risks would there be if we rated everything by its pre-mitigation (inherent) rating instead of its current residual rating," filtered by whatever `dim_risk_rating[Risk rating]` value is currently selected in the visual (since the relationship, once activated, still respects the filter context on that column).

### Risk Rating Reduction — *visible*

```dax
VAR numerator =
    CALCULATE (
        [Total Risks] - [Inherent Risk],
        KEEPFILTERS ( dim_risk_rating[Risk rating] IN { "Extreme", "High", "Medium" } )
    )
VAR denominator =
    CALCULATE (
        [Inherent Risk],
        KEEPFILTERS ( dim_risk_rating[Risk rating] IN { "Extreme", "High", "Medium" } )
    )
VAR result =
    - DIVIDE ( numerator, denominator )
RETURN
    IF (
        ISBLANK ( SELECTEDVALUE ( dim_risk_rating[Risk rating] ) ),
        BLANK (),
        result
    )
```

No doc comment. Compares residual (`Total Risks`, filtered by the active `RESIDUAL_RISK_RATING` relationship) against inherent (`[Inherent Risk]`, via the `USERELATIONSHIP`-activated relationship) counts, restricted to the three worst rating tiers (`Extreme`/`High`/`Medium`). `numerator` is the change in count (residual − inherent) for those tiers; `denominator` is the inherent count for those tiers; the result is negated so a *reduction* in high-severity risk counts (residual < inherent) reads as a positive percentage. The final `IF` blanks the result unless exactly one `Risk rating` value is selected (`SELECTEDVALUE` returns blank when zero or multiple values are in context), so this measure is only meaningful per-rating, not at a grand-total level.

### Residual risk score — *visible*

```dax
SELECTEDVALUE ( fact_risk_register[RESIDUAL_RISK_SCORE] )
```

No doc comment. Returns the single `RESIDUAL_RISK_SCORE` value when the filter context narrows to exactly one risk record (e.g. a detail card/tooltip on a risk-by-risk table); otherwise blank. Not an aggregate — a row-level lookup measure.

### Risk titles — *visible*

```dax
CALCULATE(
    CONCATENATEX(VALUES(fact_risk_register[RISK_TITLE]), fact_risk_register[RISK_TITLE],UNICHAR(10) & "-" & UNICHAR(10)))
```

No doc comment. Concatenates every distinct `RISK_TITLE` in the current filter context into a single string, each on its own line prefixed with `-` (using `UNICHAR(10)` for the newline) — likely feeds a tooltip or text-box listing all risk titles behind a given slice (e.g. all risks for a selected capability).

### Post Mitigation Active Risks — *visible*

```dax
CALCULATE ( [Total Risks], fact_risk_register[RISK_STATUS] = "Monitor" ,
USERELATIONSHIP(dim_likelihood[Likelihood], fact_risk_register[LIKELIHOOD_AFTER_MITIGATION]),
USERELATIONSHIP(dim_impact[Impact], fact_risk_register[IMPACT_AFTER_MITIGATION]))
```

No doc comment. Same "Monitor"-status filter as `Active Risks`, but activates the two inactive post-mitigation relationships (`LIKELIHOOD_AFTER_MITIGATION` → `dim_likelihood`, `IMPACT_AFTER_MITIGATION` → `dim_impact`) via `USERELATIONSHIP`, so that any slicer on `dim_likelihood[Likelihood]` or `dim_impact[Impact]` filters by the *post-mitigation* values rather than the default (pre-mitigation) ones. This is the counterpart to `Inherent Risk`'s pattern, but for the likelihood/impact dimensions instead of the rating dimension.

### colour_value — *visible* (on `dim_likelihood_impact`, not `KeyMeasures`)

```dax
SUM(dim_likelihood_impact[colour_code])
```

No doc comment. A simple `SUM` wrapper around `dim_likelihood_impact[colour_code]`, most likely used to drive conditional-formatting colour on a risk-matrix heatmap visual built from `dim_likelihood_impact`. This measure breaks the "measures live in `KeyMeasures`" convention followed everywhere else in this model and across the RI suite — see [[Risk]].

### Time intelligence (calculation group)

`Time intelligence` is a **calculation group**, not a plain measure table — its calculation items apply to whichever measure is currently selected (`SELECTEDMEASURE()`) rather than defining a new named measure. It has four calculation items:

#### Current

```dax
SELECTEDMEASURE()
```

Passes the selected measure through unchanged — the "no time intelligence applied" baseline option in the period slicer.

#### YTD

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

Computes the selected measure's year-to-date total, using `LASTNONBLANK` to anchor "today" at the last date in the current filter context for which the selected measure has a non-blank value (so it doesn't just default to `TODAY()` or the max date in the whole `Calendar` table), then applies `DATESYTD` from that anchor date. Note `max_day` is computed but never used in the `RETURN` — dead code within this calculation item.

#### PY YTD

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

Same YTD logic as above, but anchored one year earlier (`DATEADD(..., -1, YEAR)`) — the prior-year year-to-date comparison figure.

#### YTD (%)

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
formatStringDefinition: `"0.00%"`

Combines the current-year and prior-year YTD calculations from the two items above into a single year-over-year percentage-change figure. Has its own explicit format string (`0.00%`) at the calculation-item level, distinct from whatever format string the underlying selected measure carries.

## See also

- [[Risk]] — the repo entry note
- [[Risk Data Model]] — the tables and relationships these measures read, including the pre- and post-mitigation relationship pairs
- [[Shared Conventions]] — why measures are centralised in one table
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Risk Rating Dimension]], [[fact_risk_register]], [[dim_risk_rating]], [[dim_impact]], [[dim_likelihood]], [[USERELATIONSHIP]]

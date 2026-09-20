# Awards Measures

**11 measures** in [[Awards]], all in `KeyMeasures`, plus **4 calculation items** in `Time intelligence`. **Nothing is hidden** — every measure and calculation item is visible in the Fields pane.

Full definitions are transferred below in source order, followed by the calculation group.

> [!note] Reconciled against [[ri_pbi_awards semantic model]] on 2026-09-19 (`ri_pbi_awards` @ `bea86c95`)
> Every DAX block below appears verbatim in the export, and the inventory matches: 11 measures in `KeyMeasures` plus 4 calculation items. As stated below, no measure uses `USERELATIONSHIP`. The export doesn't carry `isHidden` flags, so the visibility markers still rest on the 2026-09-01 TMDL read.

## What to know before using them

**Half of these measures exist to work around the relationship graph.** `dim_ri_master_list` reaches only `fact_ilab`, and the one relationship linking `fact_ilab` to `fact_research_income` is inactive ([[Awards Data Model]]). So every measure that crosses facts does it by hand, with `VALUES()`/`IN` or `CONTAINS`, rather than by filter propagation:

| Measure | Crosses | Mechanism |
|---|---|---|
| `total_awarded_amount` | funding ↔ iLab | `dim_awards[AWARD_ID] IN VALUES(fact_ilab[award_id])` |
| `research_group_income` | income ↔ iLab | `CONTAINS` on researcher **and** year |
| `monash_income` | income, researcher-cleared | `ALL(dim_researcher[RESEARCHER_ID])` plus a year match |

These are not stylistic choices. Copying one of them into a new measure carries the workaround with it; writing a new cross-fact measure without one will silently return unfiltered totals.

**`research_group_income` is the measure the report exists for.** It answers "how much research income is attributable to researchers who use RI platforms?" — reducing `fact_research_income` to researchers who appear in `fact_ilab`, then requiring a matching iLab row for the **same researcher and the same year**. Note the year match pairs `fact_ilab[completion_year]` against `fact_research_income[FINANCIAL_YEAR]`: a calendar year against a financial year. Worth confirming that alignment with the model owner.

Rather than activate the inactive `payment_information_cleaned → FUND_CENTRE_FUND` relationship with `USERELATIONSHIP`, this measure re-derives the match directly. **Nothing in the model activates that relationship.**

**Two measures are identical.** `Proportion of Research Income from Platform Users (%)` and `Research Income from Platform Users (%)` are both `DIVIDE([research_group_income], [research_income])`, differing only in TMDL formatting. Almost certainly a leftover from a rename. Which one visuals are bound to is unconfirmed — check before deleting either. Recorded in [[Awards Gotchas]].

**De-duplication is deliberate and inconsistent.** `research_income` and `monash_income` both `SUMMARIZE` on `RESEARCH_INCOME_ID` before summing, guarding against fan-out; `actual_amount` is a plain `SUM` over the same column. `monash_income` additionally clears the researcher filter with `ALL`, `research_income` does not. They are not interchangeable denominators.

**`Awards` and `Awards (D)` count different things.** `Awards` is `DISTINCTCOUNT(fact_ilab[AWARD_ID])` — awards that have iLab activity, not awards overall. Note also that it reads `AWARD_ID` in uppercase, which Power BI resolves to the table's lowercase `award_id` column.

**Time comparisons run through a calculation group**, not per-measure DAX. Automatic time intelligence is disabled at the model level (`__PBI_TimeIntelligenceEnabled = 0`), and the four `Time intelligence` items — `Current`, `YTD`, `PY YTD`, `YTD (%)` — supply all of it.

## Measures

### Platforms — *visible*

```dax
DISTINCTCOUNT ( fact_research_award_funding[EQUIPMENT_ID] )
```

Counts the distinct pieces of equipment/platforms referenced across award-funding lines in the current filter context — a headcount of platforms involved in awarded funding.

### Awards — *visible*

```dax
DISTINCTCOUNT ( fact_ilab[AWARD_ID] )
```

Counts the distinct awards represented in `fact_ilab` — i.e. how many awards have associated iLab charges/bookings in the current filter context. Note this reads `fact_ilab[AWARD_ID]`, the uppercase alias Power BI resolves to the table's `award_id` column.

### total_awarded_amount — *visible*

```dax
VAR award_table =
    CALCULATETABLE (
        SUMMARIZE (
            fact_research_award_funding,
            dim_awards[AWARD_ID],
            fact_research_award_funding[AWARD_FUNDING_ID],
            fact_research_award_funding[AWARDED_AMOUNT_IN_AUD]
        ),
        dim_awards[AWARD_ID] IN VALUES ( fact_ilab[award_id] )
    )
VAR result =
    SUMX ( award_table, fact_research_award_funding[AWARDED_AMOUNT_IN_AUD] )
RETURN
    result
```

Sums `AWARDED_AMOUNT_IN_AUD` across award-funding lines, but restricted to only those awards that also appear in `fact_ilab` (i.e. awards with associated iLab activity), via an explicit `dim_awards[AWARD_ID] IN VALUES(fact_ilab[award_id])` filter rather than relying on the model relationships. This pattern works around the fact that `fact_ilab` and `fact_research_award_funding` are not directly related — both connect through `dim_awards`, so the explicit `VALUES()`/`IN` filter is needed to intersect the two fact tables' award sets.

### Awards (D) — *visible*

```dax
VAR award_table =
    CALCULATETABLE (
        SUMMARIZE (
            fact_research_award_funding,
            dim_awards[AWARD_ID],
            fact_research_award_funding[AWARD_FUNDING_ID]
        ),
        dim_awards[AWARD_ID] IN VALUES ( fact_ilab[award_id] )
    )
VAR result =
    COUNTROWS ( award_table )
RETURN
    result
```

Counts distinct award-funding lines (`AWARD_ID`/`AWARD_FUNDING_ID` pairs) restricted to awards that also have iLab activity — the "count" counterpart to `total_awarded_amount`'s "sum". The `(D)` suffix suggests "distinct" count of award-funding lines, as opposed to `Awards`, which counts distinct `AWARD_ID`s directly from `fact_ilab`.

### pro_rata_amount — *visible*

```dax
SUM ( fact_research_income[PRO_RATA_AMOUNT] )
```

Sums each researcher's pro-rata share of research income postings in the current filter context. Used as a building block by `research_group_income`.

### research_group_income — *visible*

```dax
VAR reduce_table =
    CALCULATETABLE (
        fact_research_income,
        dim_researcher[RESEARCHER_ID] IN VALUES ( fact_ilab[researcher_id] )
    )

VAR income =
    CALCULATE (
        [pro_rata_amount],
        FILTER (
            reduce_table,
            CONTAINS (
                fact_ilab,
                fact_ilab[researcher_id], fact_research_income[researcher_id],
                fact_ilab[completion_year], fact_research_income[FINANCIAL_YEAR]
            )
        )
    )
RETURN 
    income
```

Answers "how much research income is attributable to researchers who use RI platforms (iLab)?" It first reduces `fact_research_income` to rows whose `RESEARCHER_ID` appears in `fact_ilab[researcher_id]`, then further restricts to rows where a matching `fact_ilab` row exists with the **same** researcher **and** the same year (`fact_ilab[completion_year] = fact_research_income[FINANCIAL_YEAR]`), via `CONTAINS`. This `CONTAINS`-based row-matching is a manual workaround for the fact that the only relationship between `fact_ilab` and `fact_research_income` (`payment_information_cleaned` → `FUND_CENTRE_FUND`) is **inactive**; rather than activating it with `USERELATIONSHIP`, this measure re-derives the researcher/year match directly. Feeds into `Proportion of Research Income from Platform Users (%)` and `Research Income from Platform Users (%)`.

### actual_amount — *visible*

```dax
SUM ( fact_research_income[ACTUAL_AMOUNT] )
```

Sums actual (as opposed to committed or pro-rata) income postings in the current filter context.

### monash_income — *visible*

```dax
VAR lookup = 
    CALCULATETABLE(SUMMARIZE(fact_research_income,fact_research_income[RESEARCH_INCOME_ID],fact_research_income[ACTUAL_AMOUNT]),
    ALL(dim_researcher[RESEARCHER_ID]),
    'Calendar'[cal_year] in VALUES(fact_research_income[FINANCIAL_YEAR]))


VAR monash_income = 
    SUMX(lookup,[actual_amount])



RETURN
monash_income
```

Computes total actual income for the selected year(s) while explicitly clearing any researcher-level filter (`ALL(dim_researcher[RESEARCHER_ID])`) — i.e. the University-wide income total, unaffected by a researcher slicer, for the years currently in context. Not referenced by any other measure in this table — the "proportion" measures use `research_income` (below) as their denominator instead, not `monash_income`; it appears to be either an unused alternative denominator or a measure intended for a visual not captured in this documentation pass.

### Proportion of Research Income from Platform Users (%) — *visible*

```dax
DIVIDE ( [research_group_income], [research_income] ) 
```

Expresses `research_group_income` (income attributable to iLab/platform-using researchers) as a percentage of `research_income` (total income in context). **Caveat:** this measure and `Research Income from Platform Users (%)` below use the identical `DIVIDE([research_group_income],[research_income])` formula — apparent duplicate measures, likely from a prior rename, worth confirming with the model owner which one is bound to visuals.

### research_income — *visible*

```dax
VAR lookup = 
    SUMMARIZE(fact_research_income,fact_research_income[RESEARCH_INCOME_ID],fact_research_income[ACTUAL_AMOUNT])
VAR iterate_table = SUMX(
lookup,
    [actual_amount]
)



RETURN
iterate_table
```

Sums `ACTUAL_AMOUNT` after de-duplicating on `RESEARCH_INCOME_ID` via `SUMMARIZE`, in the current filter context (unlike `monash_income`, it does not clear the researcher filter). Used as the denominator for both "proportion of platform-user income" measures.

### Research Income from Platform Users (%) — *visible*

```dax
DIVIDE([research_group_income],[research_income])
```

Same formula as `Proportion of Research Income from Platform Users (%)` above (single-line form vs. the fenced-code-block form) — see the caveat noted there.

### Time intelligence calculation group

Documented separately as it is a calculation group (`Time intelligence` table), not a `KeyMeasures` measure — its items apply to whichever measure is selected in a visual via `SELECTEDMEASURE()`.

#### Current

```dax
SELECTEDMEASURE()
```

Passthrough item — returns the selected measure unmodified. The baseline against which the other calculation items compare.

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

Calculates the selected measure's year-to-date total, using the last date with non-blank data (`LASTNONBLANK`) as the YTD cutoff rather than today's date or the visual's max date — so YTD stays meaningful even when the current period's data is incomplete or not yet loaded. **Note:** `max_day` is computed but never used in the `RETURN` — dead variable left over from a prior version of the logic.

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

Same YTD logic as above but shifted back one year (`DATEADD(..., -1, YEAR)`) — the prior-year YTD comparison figure.

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

Combines the `YTD` and `PY YTD` logic to compute year-over-year YTD growth as a percentage: `(this year's YTD − last year's YTD) / last year's YTD`. Formatted as a percentage (`formatStringDefinition = "0.00%"` on the calculation group).

## See also

- [[Awards]] — the repo entry note
- [[Awards Data Model]] — the tables and relationships these measures read
- [[Awards Gotchas]] — including the measures flagged as unreliable
- [[Shared Conventions]] — why measures are centralised in one table
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Research Awards Funding]], [[fact_research_award_funding]], [[fact_research_income]], [[fact_ilab_1]], [[dim_awards]]
- **Derived layer — more nodes** (`graphify/`, never hand-edited): [[Awards dim_ri_master_list]]

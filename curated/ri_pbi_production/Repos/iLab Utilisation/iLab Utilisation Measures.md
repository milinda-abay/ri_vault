# iLab Utilisation Measures

**29 measures** in [[iLab Utilisation]] — 28 in `Key Measures`, one on `dim_ilab_lab` — plus **8 calculation items** in `Time Intelligence`. **Nothing is hidden**: every measure and calculation item is visible in the Fields pane.

Full definitions are transferred below in source order: the `Key Measures` measures, then the one defined on `dim_ilab_lab`, then the calculation group.

> [!note] Reconciled against [[ri_pbi_ilab_utilisation semantic model]] on 2026-09-19 (`ri_pbi_ilab_utilisation` @ `f8c4a836`)
> Every DAX block below appears verbatim in the export, and the inventory matches: 28 measures in `Key Measures`, 1 on `dim_ilab_lab`, plus 8 calculation items. The export doesn't carry `isHidden` flags, so the visibility markers still rest on the 2026-09-01 TMDL read.

## What to know before using them

**Time intelligence is entirely manual here.** Model-level automatic time intelligence is switched off (`__PBI_TimeIntelligenceEnabled = 0`), and the `Time Intelligence` calculation group replaces it with eight items — `Total`, `CY`, `PY`, `YoY (%)`, `CML.`, `YTD`, `PY YTD`, `YTD(%)`. That is twice as many as [[Publication]] carries, and they are the only date-comparison logic in the model. All of them key off `LASTNONBLANK('CALENDAR'[cal_date], SELECTEDMEASURE())` — the latest date in context that actually has data — and `YEAR(TODAY())`, so their behaviour shifts with the data and with the calendar year, not with a fixed anchor.

Unlike [[Publication]], there is no split-fact caveat to worry about: `calendar` relates directly to the single `fact_ilab` at day grain, so time intelligence reaches everything.

**`Charges ($)` deliberately avoids a plain `SUM`.** It summarises over `charge_id` + `total_price` first and then `SUMX`es, so that a downstream relationship fanning out rows per charge cannot double-count revenue. Copy that shape rather than `SUM(fact_ilab[total_price])` if you add a revenue variant.

**`Equipment usage (%)` rests on a hardcoded capacity assumption.** It divides actual `Equipment Hours` by `[Equipment (D)] × 500 × <distinct quarters in context>` — a flat **500 hours per equipment item per quarter**, not driven by any per-equipment capacity data. It is a rough proxy. **Do not use it for capacity planning without validating that figure with the business owner.**

**Institution-type breakdowns split across two column families.** `Monash Researchers (D)`, `Ind/Govt Researchers (D)`, `Ext Res/Acad Researchers (D)`, `Ind/Govt Institute (D)` and `External Organisations (D)` filter `dim_ilab_lab`'s *grouped* institution-type columns (`institution_type_lvl_1`, `institution_type_LVL_3`), while `Industry Partners (D)` filters the *raw* `institution_type`. Check which family a measure uses before assuming two of these are comparable.

**One measure is in the wrong place.** `Industry Partners (D)` is defined on `dim_ilab_lab`, not in `Key Measures`, breaking this repo's own centralisation convention. Recorded in [[iLab Utilisation Gotchas]]; not moved.

**Two definitions carry disabled logic.** `Researchers (D)` and the `CY` calculation item both keep commented-out alternatives inline. `filter_assest` computes a `_visible_names` variable it never uses. Read past these rather than assuming they are live.

## Measures

### Charges ($) — *visible*

```dax
VAR _table =
    SUMMARIZE ( 'fact_ilab', fact_ilab[charge_id], fact_ilab[total_price] )
RETURN
    SUMX ( _table, fact_ilab[total_price] )
```

Total dollar value charged in the current filter context — the headline revenue figure. Uses `SUMMARIZE` over `charge_id` + `total_price` rather than a plain `SUM` to dedupe if a downstream relationship ever fans out rows per charge, then sums with `SUMX`.

### Researchers (D) — *visible*

```dax

DISTINCTCOUNT ( fact_ilab[user_login_email] )
//VALUES(  ilab[user_login_email] )
// COUNTROWS(VALUES(  ilab[user_login_email] ))
```

Distinct count of researchers (by login email) who submitted requests in the current filter context. Two commented-out alternative implementations (`VALUES`/`COUNTROWS(VALUES(...))`, referencing a table alias `ilab` that no longer exists) are left in place as dead code.

### Labs (D) — *visible*

```dax

COUNTROWS ( VALUES ( fact_ilab[customer_lab] ) )
```

Distinct count of labs that used the platform(s) in the current filter context. Offered as one of the two toggle options in the `Parameter` field-parameter table.

### Equipment Hours — *visible*

```dax

VAR __table =
    CALCULATETABLE (
        SUMMARIZE ( 'fact_ilab', fact_ilab[charge_id], fact_ilab[quantity] ),
        dim_ilab_services[type] IN { "EQUIPMENT" }
    )
VAR __result =
    SUMX ( __table, fact_ilab[quantity] )
RETURN
    __result
```

Total quantity (hours/units) of equipment-type usage, filtered via the fact→`dim_ilab_services` relationship to rows where `type = "EQUIPMENT"`. Feeds `Equipment usage (%)`.

### Asset (D) — *visible*

```dax
DISTINCTCOUNT ( fact_ilab[asset_id] )
```

Distinct count of assets (equipment/service items) used in the current filter context — the base measure `Equipment (D)` and `Services (D)` both re-filter.

### Equipment (D) — *visible*

```dax

CALCULATE ( [Asset (D)], dim_ilab_services[type] = "EQUIPMENT" )
```

Distinct equipment-type assets only. Used in the denominator of `Equipment usage (%)`.

### Services (D) — *visible*

```dax

CALCULATE ( [Asset (D)], dim_ilab_services[type] = "SERVICE" )
```

Distinct service-type assets only.

### Platforms (D) — *visible*

```dax

COUNTROWS ( VALUES ( fact_ilab[core_name] ) )
```

Distinct count of iLab core facilities/platforms represented in the current filter context.

### Services (N) — *visible*

```dax

VAR _table =
    CALCULATETABLE (
        VALUES ( fact_ilab[charge_id] ),
        dim_ilab_services[type] IN { "SERVICE" }
    )
RETURN
    COUNTROWS ( _table )
```

Count of service-type charges (transactions) — the "count of records" counterpart to `Services (D)`'s distinct-asset count.

### selected period — *visible*

```dax

SELECTEDVALUE ( 'calendar'[cal_year], -1 )
```

Returns the single selected `calendar[cal_year]` value, or `-1` if none/multiple years are selected. Note the DAX in this measure references `'calendar'` (lowercase) while several other measures in this table reference `'CALENDAR'` (uppercase) for the same table — a harmless naming inconsistency since DAX table names are case-insensitive. Feeds the `Chart title` measure.

### Equipment (N) — *visible*

```dax

VAR _table =
    CALCULATETABLE (
        VALUES ( fact_ilab[charge_id] ),
        dim_ilab_services[type] IN { "EQUIPMENT" }
    )
RETURN
    COUNTROWS ( _table )
```

Count of equipment-type charges/transactions.

### Platform capability & support — *visible*

```dax

BLANK ()
```

Always returns blank. A dummy measure in the `_Formatting` display folder, used purely as a section-header/label placeholder in the report rather than an actual data point.

### Platform usage — *visible*

```dax

BLANK ()
```

Same pattern as `Platform capability & support` — a dummy header/label measure.

### Chart title — *visible*

```dax

CONCATENATE (
    "Charge ($) by platform for ",
    CONVERT ( [selected period], STRING )
)
```

Builds a dynamic title string combining static text with the currently selected calendar year, for a title/card visual bound to this measure.

### Last completion date — *visible*

```dax

FORMAT (
    MAXX ( ALL ( fact_ilab[completion_date] ), fact_ilab[completion_date] ),
    "dd-mmm-yy"
)
```

Latest `completion_date` across the whole fact table, ignoring all filters (`ALL`), formatted as text — likely a "data as of" footer/caption.

### Researcher(s) — *visible*

```dax

VALUES ( fact_ilab[user_login_email] )
```

Returns the table of distinct researcher emails in context. A table-valued measure rather than a scalar — only behaves sensibly in visual contexts expecting a single value or a list (e.g. a tooltip or a filtered single-row card); would behave unexpectedly if dropped into a plain card visual with multiple values in context.

### Services (G) — *visible*

```dax

VAR __valid_years =
    VALUES ( 'calendar'[cal_year] )
VAR __growth_table =
    CALCULATETABLE (
        ADDCOLUMNS (
            VALUES ( fact_ilab[asset_id] ),
            "year", CALCULATE ( MIN ( fact_ilab[completion_year] ) )
        ),
        ALL ( 'calendar' ),
        dim_ilab_services[type] IN { "SERVICE" }
    )
VAR current_growth_in_period =
    FILTER ( __growth_table, [year] IN __valid_years )
VAR result =
    COUNTROWS ( current_growth_in_period )
RETURN
    result
```

A "growth" measure: for each distinct service-type `asset_id`, finds its earliest (`MIN`) `completion_year` with the calendar filter cleared (`ALL('calendar')`), then counts how many of those first-appearance years fall within the years currently visible in the filter context (`__valid_years`). Effectively counts newly onboarded service-type assets within the selected period(s).

### Field name — *visible*

```dax

VALUES ( Parameter[Parameter] )
```

Returns the currently selected label from the `Parameter` field-parameter table, used to dynamically label an axis/title in a visual driven by that parameter.

### selected_services — *visible*

```dax

SELECTEDVALUE ( dim_ilab_services[serviceorequipmentid] )
```

Returns the single selected service/equipment ID (e.g. from a slicer). Helper for `filter_assest`.

### Equipment usage (%) — *visible*

```dax

VAR __visible_quaters =
    DISTINCTCOUNT ( 'calendar'[Quarter] )
VAR __number_of_equipment = [Equipment (D)]
VAR __total_equipment_hours = __number_of_equipment * 500 * __visible_quaters
VAR result =
    DIVIDE ( [Equipment Hours], __total_equipment_hours )
RETURN
    result
```

Utilisation rate: actual `Equipment Hours` divided by an assumed theoretical capacity of 500 hours per equipment item per quarter, scaled by the number of distinct quarters visible in the current filter context. **Caveat:** the 500-hours/quarter capacity figure is hardcoded and not driven by any per-equipment capacity data — a rough proxy that should be validated with the business owner. (Note the variable name typo `__visible_quaters`, cosmetic only.)

### Service (Avg. TAT) — *visible*

```dax

VAR __service_table =
    CALCULATETABLE (
        SUMMARIZE (
            fact_ilab,
            fact_ilab[charge_id],
            dim_ilab_services[serviceorequipmentid],
            fact_ilab[asset_tat]
        ),
        dim_ilab_services[type] IN { "SERVICE" }
    )
VAR __result =
    AVERAGEX ( __service_table, fact_ilab[asset_tat] )
RETURN
    __result
```

Average turnaround time (days between `purchase_date` and `completion_date`, pre-computed as `asset_tat`) for service-type charges only — a service-delivery performance metric.

### filter_assest — *visible*

```dax

VAR _visible_assest =
    CALCULATETABLE (
        SUMMARIZE (
            dim_ilab_services,
            dim_ilab_services[serviceorequipmentid],
            dim_ilab_services[serviceorequipmentname]
        ),
        dim_ilab_services[serviceorequipmentid] IN VALUES ( fact_ilab[asset_id] )
    )
VAR __ids =
    INTERSECT (
        VALUES ( dim_ilab_services[serviceorequipmentid] ),
        VALUES ( fact_ilab[asset_id] )
    )
VAR _visible_names =
    TREATAS (
        SELECTCOLUMNS (
            _visible_assest,
            "serviceorequipmentname", dim_ilab_services[serviceorequipmentname]
        ),
        dim_ilab_services[serviceorequipmentname]
    )
VAR _result =
    IF (
        SELECTEDVALUE ( dim_ilab_services[serviceorequipmentid] ) IN __ids,
        "show"
    )
RETURN
    _result
```

Visibility helper: returns the literal string `"show"` when the currently-selected `dim_ilab_services[serviceorequipmentid]` (e.g. a slicer row) also appears among the `asset_id` values actually present in `fact_ilab` under the current filter context, otherwise `BLANK()`. Intended to be used as a visual-level filter condition to hide slicer/list entries for services or equipment with no usage in the selected period. **Caveat:** the `_visible_names` variable is computed but never referenced in `_result` — dead code within the measure.

### Monash Researchers (D) — *visible*

```dax

CALCULATE (
    [Researchers (D)],
    'dim_ilab_lab'[institution_type_lvl_1] = "INTERNAL"
)
```

Distinct researchers whose lab is classified `INTERNAL` (Monash University-affiliated) via `dim_ilab_lab[institution_type_lvl_1]`.

### Ind/Govt Researchers (D) — *visible*

```dax

CALCULATE (
    [Researchers (D)],
    'dim_ilab_lab'[institution_type_LVL_3] = "INDUSTRY/GOVERNMENT"
)
```

Distinct researchers from industry- or government-affiliated labs.

### Ext Res/Acad Researchers (D) — *visible*

```dax

CALCULATE (
    [Researchers (D)],
    'dim_ilab_lab'[institution_type_LVL_3] = "EXTERNAL RESEARCH INSTITUTES"
)
```

Distinct researchers from external research institutes/universities (non-Monash academic/research institutions).

### Ind/Govt Institute (D) — *visible*

```dax

CALCULATE (
    [External Organisations (D)],
    'dim_ilab_lab'[institution_type_LVL_3] = "INDUSTRY/GOVERNMENT"
)
```

Distinct external organisations classified as industry/government.

### External Organisations (D) — *visible*

```dax

CALCULATE (
    DISTINCTCOUNT ( fact_ilab[customer_institute] ),
    dim_ilab_lab[institution_type_lvl_1] = "EXTERNAL"
)
```

Distinct count of external (non-Monash) customer institutes — the base measure the "Management Review" institute-count measures above re-filter.

### Quantity (N) — *visible*

```dax

VAR __table =
    CALCULATETABLE (
        SUMMARIZE ( 'fact_ilab', fact_ilab[charge_id], fact_ilab[quantity] ),
        dim_ilab_services[type] IN { "SERVICE" }
    )
VAR __result =
    SUMX ( __table, fact_ilab[quantity] )
RETURN
    __result
```

Total quantity (hours/units) charged for service-type usage — the SERVICE-side counterpart to `Equipment Hours`.

### Industry Partners (D) — *visible* (defined on `dim_ilab_lab`, not `Key Measures`)

```dax

CALCULATE (
    [External Organisations (D)],
    'dim_ilab_lab'[institution_type] = "INDUSTRY"
)
```

Distinct external organisations specifically classified `"INDUSTRY"` using the raw `institution_type` column (not the grouped `institution_type_lvl_1`/`institution_type_LVL_3`). **Caveat:** this measure lives directly on the `dim_ilab_lab` dimension table rather than in `Key Measures`, breaking this repo's own stated convention of centralising measures (per `CLAUDE.md`) — a candidate for relocation in a future cleanup pass.

### Time Intelligence (calculation group)

`Time Intelligence` is a calculation group, not a plain measure table — each calculation item below re-expresses `SELECTEDMEASURE()` (whatever base measure a visual is showing) under a different date-comparison logic, all keyed off `LASTNONBLANK('CALENDAR'[cal_date], SELECTEDMEASURE())` (the latest date in context with data) and `YEAR(TODAY())`.

#### Total

```dax
SELECTEDMEASURE()
```

Pass-through — the selected measure with no time-intelligence transformation applied; the default/baseline item.

#### CY

```dax

VAR 
__last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())


VAR
__last_day_of_year = ENDOFYEAR(__last_date)

VAR
__this_year = YEAR(TODAY())

VAR
__year_dates = DATESYTD(__last_day_of_year)

VAR
result = CALCULATE(
    SELECTEDMEASURE(),
    // 'calendar'[cal_year] < __this_year,
    __year_dates
)

RETURN
result
```

Year-to-date through the latest date with data in the selected year (based on the end-of-year of the last non-blank date). Contains a commented-out additional filter (`'calendar'[cal_year] < __this_year`) left in as disabled reference code.

#### PY

```dax

VAR 
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
last_day_of_year = ENDOFYEAR(last_date)



VAR
result = CALCULATE(
    SELECTEDMEASURE(),
    'calendar'[cal_year] < YEAR(TODAY())-1,
    DATESYTD(DATEADD(last_day_of_year,-1,YEAR))
)


RETURN
result

```

Prior-year year-to-date — same logic as `CY` shifted back one year via `DATEADD(...,-1,YEAR)`, restricted to years before last year.

#### YoY (%)

```dax
VAR
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
__end_of_current_year = ENDOFYEAR(last_date)


VAR
__end_of_previous_year =  DATEADD(__end_of_current_year,-1,YEAR)

VAR
fiscal_YTD = CALCULATE(
    SELECTEDMEASURE(),
    'calendar'[cal_year] < YEAR(TODAY()),
    DATESYTD(__end_of_current_year)
)


VAR
py_ytd = CALCULATE(
    SELECTEDMEASURE(),
    'calendar'[cal_year] < YEAR(TODAY())-1,
    DATESYTD(__end_of_previous_year)
)

VAR
result = DIVIDE((fiscal_YTD-py_ytd), py_ytd)

RETURN
result
```

Year-over-year percent change between current fiscal year-to-date and prior-year year-to-date. `formatStringDefinition = "0.0%"`.

#### CML.

```dax

VAR 
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
result = CALCULATE(SELECTEDMEASURE(),
'calendar'[cal_date] < last_date)

RETURN
result
```

Cumulative-to-date — the selected measure filtered to all dates strictly before the last non-blank date (a running total up to the last visible date).

#### YTD

```dax


VAR 
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
__this_year = YEAR(TODAY())

VAR
result = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(last_date),
    'calendar'[cal_year] = __this_year
    )

RETURN
result
```

Year-to-date restricted specifically to the current calendar year (`YEAR(TODAY())`).

#### PY YTD

```dax

VAR 
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
__this_year = YEAR(TODAY())

VAR
result = 
CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(DATEADD(last_date,-1,YEAR)),
    'calendar'[cal_year] = __this_year-1
    )

RETURN
result
```

Prior-year year-to-date, restricted to last year (`YEAR(TODAY())-1`).

#### YTD(%)

```dax
VAR
last_date = LASTNONBLANK('CALENDAR'[cal_date],SELECTEDMEASURE())

VAR
__this_year = YEAR(TODAY())

VAR
fiscal_YTD = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(last_date),
    'calendar'[cal_year] = __this_year
    )
    
    
VAR
py_ytd = CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD(DATEADD(last_date,-1,YEAR)),
    'calendar'[cal_year] = __this_year-1)
    
VAR
result = DIVIDE((fiscal_YTD-py_ytd), py_ytd)

RETURN
result
```

Percent change between current YTD and prior-year YTD (a `YTD`/`PY YTD`-based counterpart to `YoY (%)`, which instead uses fiscal-year-end anchored variables). `formatStringDefinition = "0.0%"`.

## See also

- [[iLab Utilisation]] — the repo entry note
- [[iLab Utilisation Data Model]] — the tables and relationships these measures read
- [[iLab Utilisation Gotchas]] — including the measures flagged as unreliable
- [[Shared Conventions]] — why measures are centralised in one table
- **Derived layer** (`graphify/`, never hand-edited): [[_COMMUNITY_Key Measures]], [[dim_ilab_services]], [[dim_ilab_lab]], [[ilab_award_income_researcher_1]]

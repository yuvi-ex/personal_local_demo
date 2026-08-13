# Sales Insights (TPC-H)

Source: standard TPC-H benchmark tables in `TPCH` (30,000 orders, 120,515 line items,
1992-01-01 to 1998-08-02). Sales grain is the line item; `LINEITEM` is joined up through
`ORDERS -> CUSTOMER -> NATION -> REGION` in a `WITH SALES AS (...)` CTE duplicated at the top
of every query file (no cross-file SQL includes exist in dash-server).

## Layman relabeling

Raw TPC-H codes are translated for display only (the underlying GROUP BY/WHERE still use raw
values):

- `O_ORDERSTATUS`: `O` -> "Open", `F` -> "Completed", `P` -> "In Progress" (`STATUS_LABELS`).
- `L_SHIPMODE`: `REG AIR` -> "Regular Air", `FOB` -> "Freight (FOB)" (`SHIP_MODE_LABELS`); the
  rest (`AIR`, `MAIL`, `RAIL`, `SHIP`, `TRUCK`) are already plain English.
- `C_MKTSEGMENT`: title-cased only (e.g. `BUILDING` -> "Building").
- Revenue is the standard TPC-H "net sales" formula: `L_EXTENDEDPRICE * (1 - L_DISCOUNT)`
  (matches TPC-H Query 1's pricing summary), not the raw list price and not `O_TOTALPRICE`
  (which also isn't reproduced from line items - it's a separately generated column). Every
  dollar figure on the dashboard is this same measure, formatted via `_format_usd()`.

## Filters

- `region` / `segment` / `status` (checklists) + their `_all` flags - the IN-list-with-
  non-empty-fallback pattern used throughout this project's dashboards, to avoid pyexasol's
  empty-list placeholder crash.
- `year_min` / `year_max` (a `dcc.RangeSlider`) - bounds are queried live on page load from
  `filter_bounds.sql` (`MIN/MAX(EXTRACT(YEAR FROM O_ORDERDATE))`) rather than hardcoded, since
  the order date range is real data that could change if this table is reloaded.

## One query, four charts

`breakdowns.sql` UNIONs four `GROUP BY` breakdowns (region, customer type, order status,
shipping method) tagged with a `DIMENSION` column, all against the *same* filtered CTE - one
query instead of four near-identical ones. `app.py` splits the rows by `DIMENSION` in Python
for the four separate charts.

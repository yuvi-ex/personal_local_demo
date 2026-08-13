# ETF SIP Advisor

Source: `STARTER_KIT.MW_ETF_05_AUG_2026` (339 NSE-listed ETFs, single-day market-watch snapshot).

## Data cleanup

Many numeric columns (`OPEN`, `HIGH`, `LOW`, `PREV. CLOSE`, `LTP`, `NAV`, `52W H`, `52W L`,
`VALUE (Crores)`) are stored as `VARCHAR` with comma thousands-separators and `-` for missing/
no-trade rows. Cleaned via `CAST(NULLIF(REPLACE(col, ',', ''), '-') AS DOUBLE)` in every query,
and rows with a NULL `LTP`/`NAV`/`VALUE (Crores)` after cleanup are excluded (no-trade / broken
rows, not real signal).

`UNDERLYING ASSET ` has a trailing space in its actual column name - always quote it exactly.

## Category classification

Exasol does not support `ILIKE`; use `UPPER(col) LIKE '%PATTERN%'`. `UNDERLYING ASSET ` is free
text (263 distinct values), bucketed into 6 categories via a `CASE` on keyword patterns (Silver,
Gold, Debt/Liquid, International Equity, Broad Market Equity, else Sectoral/Thematic Equity).
The same `CASE` block is duplicated at the top of every business query (`WITH BASE AS (...)`) -
no cross-file SQL includes are supported.

## Filters

- `category` (checklist, multi-select) + `category_all` flag - same IN-list pattern as the
  student-performance dashboard: `{category_all!d} = 1 OR "CATEGORY" IN ({category!s})`, and the
  list passed to `{category!s}` is never empty (falls back to the full category universe) to
  avoid pyexasol's empty-list placeholder crash.
- `liquid_only` (single checkbox, default checked) - filters to `VALUE_CR >= 1.0` (>= ₹1 Cr/day
  turnover) when set.

## Suggested SIP allocation

`recommendations.sql` picks the most liquid ETF per category (ties broken implicitly by ROW_NUMBER
over `VALUE_CR DESC`). `app.py` applies a fixed core-satellite weight table (`BASE_WEIGHTS`),
renormalized in Python across whichever categories survive the current filters, then multiplies
by the user-entered monthly SIP amount. This is illustrative, not personalized financial advice -
see the in-app disclaimer.

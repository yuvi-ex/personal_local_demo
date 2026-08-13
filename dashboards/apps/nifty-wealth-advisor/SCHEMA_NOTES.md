# Nifty Wealth Advisor

Source: 5 separate NSE market-watch snapshot tables uploaded from Downloads, one per segment:

- `STARTER_KIT.MW_NIFTY_50_04_AUG_2026`
- `STARTER_KIT.MW_NIFTY_BANK_04_AUG_2026`
- `STARTER_KIT.MW_NIFTY_FINANCIAL_SERVICES_04_AUG_2026`
- `STARTER_KIT.MW_NIFTY_MIDCAP_SELECT_04_AUG_2026`
- `STARTER_KIT.MW_NIFTY_NEXT_50_04_AUG_2026`

Each table's **first row is the index itself** (e.g. `SYMBOL = 'NIFTY 50'`), and the remaining rows
are its constituent stocks. Verified that the index row's `VALUE (Crores)` equals the sum of its
constituents' `VALUE (Crores)` - it's a real aggregate, safe to use directly as segment turnover.

## Why two query files, not one per segment

Since the 5 segments live in 5 separate physical tables (not one table with a category column),
`summary.sql` and `constituents.sql` each `UNION ALL` all 5 tables with a literal `'Nifty ...'`
label per branch, then filter/aggregate. No cross-file SQL includes exist, so this `UNION ALL`
block isn't shared with any other file.

`constituents.sql` dedupes by `SYMBOL` (`ROW_NUMBER() OVER (PARTITION BY SYMBOL ...)`) because the
same large stock (e.g. HDFCBANK) legitimately appears in multiple segment tables (Nifty 50 *and*
Nifty Bank *and* Nifty Financial Services all include it).

## Filters

- `segment` (checklist) + `segment_all` flag - same IN-list-with-fallback pattern as the other
  dashboards in this project. Segment names are hardcoded in `app.py` (`SEGMENT_ORDER`), not
  queried live, because they are literally which of the 5 tables to union, not a data column with
  values that could drift - the anti-pattern this project usually guards against (a stale
  hardcoded fallback for a live distinct-values column) doesn't apply here.
- `horizon` (radio: Last 1 Year / Last 30 Days) - purely a Python-side choice of which already-
  fetched column (`RET_1Y` vs `RET_30D`) drives the charts/insight; no extra query.
- `invest-amount` (₹ number input, default 50,000) - purely arithmetic in Python
  (`amount * (1 + pct/100)`), applied to already-fetched percentages.

## Currency formatting

`_format_inr()` in `app.py` implements Indian digit grouping (lakhs/crores: `1,02,935`, not the
western `102,935`) since this is an Indian retail-investor context. Applied to every KPI, chart
label, and recommendation card per the "convert numbers to currency wherever applicable" ask.

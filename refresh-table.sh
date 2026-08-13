#!/usr/bin/env bash
# Safely refresh a dashboard's data WITHOUT breaking the table name the app is wired to.
#
# Usage:
#   ./refresh-table.sh <schema.table> <csv-file>
#
# What it does:
#   1. Strips Windows CRLF line endings (NSE/Windows-exported CSVs often have them
#      and Exasol's importer chokes on the trailing \r in the last column).
#   2. TRUNCATEs the target table (keeps the table object + name intact - this is
#      the critical part, since every dashboard's SQL is hardcoded to an exact
#      table name. DROP + recreate is what silently breaks the dashboards).
#   3. Re-uploads the fresh CSV into that same table.
#   4. Prints the before/after row count so you can see it worked live on stage.
#
# It does NOT restart dash-server and does NOT need to - the dashboards query
# Exasol live on every page load / 60s auto-refresh, so new data just appears.

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <schema.table> <csv-file>" >&2
  exit 1
fi

TABLE="$1"
CSV_FILE="$2"
PROFILE="starter-kit"
TMP_CLEAN="/tmp/$(basename "$CSV_FILE" | tr ' ' '_').clean.csv"

if [ ! -f "$CSV_FILE" ]; then
  echo "File not found: $CSV_FILE" >&2
  exit 1
fi

echo "== $TABLE =="
echo "-- before --"
exapump sql -p "$PROFILE" "SELECT COUNT(*) AS ROW_COUNT FROM $TABLE" || true

echo "-- cleaning line endings --"
tr -d '\r' < "$CSV_FILE" > "$TMP_CLEAN"

echo "-- truncating (table + name stay intact) --"
exapump sql -p "$PROFILE" "TRUNCATE TABLE $TABLE"

echo "-- loading $CSV_FILE --"
exapump upload "$TMP_CLEAN" --table "$TABLE" -p "$PROFILE"

echo "-- after --"
exapump sql -p "$PROFILE" "SELECT COUNT(*) AS ROW_COUNT FROM $TABLE"

rm -f "$TMP_CLEAN"
echo "Done. Reload the dashboard tab in your browser to see it."

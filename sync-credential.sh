#!/usr/bin/env bash
# Fixes "Connection exception - authentication failed" across ALL dash-server
# dashboards at once.
#
# Root cause: the local Exasol runtime rotates the mcp_readonly DB user's
# password on restart. dash-server's own stored credential for its
# "starter-kit" profile does not auto-update, so every dashboard's queries
# start failing with an auth error that looks nothing like a data problem.
#
# Run this any time all dashboards go blank/error together right after an
# Exasol or laptop restart. Safe to run anytime - it's idempotent.

set -euo pipefail

CURRENT_PW_FILE="$HOME/.exasol-starter-kit/credentials/mcp_readonly_password"
DASH_SECRET_FILE="$HOME/dash-server/instance/exasol-secrets/starter-kit.json"

if [ ! -f "$CURRENT_PW_FILE" ]; then
  echo "Can't find current password at $CURRENT_PW_FILE - is the starter kit running? (exakit status)" >&2
  exit 1
fi

CURRENT_PW=$(cat "$CURRENT_PW_FILE")

python3 - "$DASH_SECRET_FILE" "$CURRENT_PW" <<'EOF'
import json, sys
path, pw = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
before = data.get("secret")
data["secret"] = pw
with open(path, "w") as f:
    json.dump(data, f)
print("Secret updated." if before != pw else "Secret already up to date.")
EOF

echo "-- restarting dash-server --"
PID=$(pgrep -f '\.venv/bin/dash-server$' || true)
if [ -n "$PID" ]; then
  kill "$PID"
  sleep 2
fi

cd "$HOME/dash-server"
nohup .venv/bin/dash-server > /tmp/dash-server.log 2>&1 &
disown
sleep 3

if pgrep -f '\.venv/bin/dash-server$' > /dev/null; then
  echo "dash-server is back up. Reload your dashboard tabs."
else
  echo "dash-server did not start - check /tmp/dash-server.log" >&2
  exit 1
fi

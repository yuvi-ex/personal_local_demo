# AI Summit Demo Runbook

## Why the dashboards kept going blank (root causes, now fixed)

1. **Table name mismatch.** Each dashboard's SQL is hardcoded to an exact table
   name (e.g. `MW_ETF_05_AUG_2026`). Loading a CSV under any other name (or
   letting a tool auto-derive a name from today's filename) silently breaks
   the dashboard - no error on screen, just empty charts.
   Fix: always load into the **exact table name** the dashboard already
   expects (see reference table below), never a new name.

2. **Table dropped instead of refreshed.** `exapump upload` into a *new*
   table, or a DROP + recreate, changes the table's identity even if the name
   looks the same. `exapump upload` into an *existing* table **appends**
   rather than replaces - so re-uploading the same file twice doubles the
   rows. Fix: always `TRUNCATE` the table first, then upload. This is exactly
   what `refresh-table.sh` in this folder does.

3. **Credential rotation.** The local Exasol runtime rotates the
   `mcp_readonly` DB password on restart. `dash-server`'s stored credential
   for that user doesn't auto-update, so every dashboard fails with
   `authentication failed` - which looks like a data problem but isn't.
   Fix: run `sync-credential.sh` any time this happens (e.g. right after any
   Exasol/laptop restart).

## Table name reference - never change these

| Dashboard | Table(s) |
|---|---|
| ETF SIP Advisor | `STARTER_KIT.MW_ETF_05_AUG_2026` |
| Nifty Wealth Advisor | `STARTER_KIT.MW_NIFTY_50_04_AUG_2026`, `MW_NIFTY_BANK_04_AUG_2026`, `MW_NIFTY_FINANCIAL_SERVICES_04_AUG_2026`, `MW_NIFTY_MIDCAP_SELECT_04_AUG_2026`, `MW_NIFTY_NEXT_50_04_AUG_2026` |
| Student Performance | `STARTER_KIT.STUDENTS_PERFORMANCE_DATASET_CLEAN` |
| Employee Insights | `STARTER_KIT.EMPLOYEES` |

Yes, the ETF/Nifty table names have "05_AUG_2026" / "04_AUG_2026" baked in even
if you load a newer day's file into them on stage - that's just a leftover
label from when they were first built, nobody sees the table name in the UI.
Don't rename the table to match the new date; renaming breaks the dashboard's
SQL again (that's the mismatch bug from point 1). Truncate + reload into the
same name.

## Pre-demo checklist (do this the day before, not the morning of)

1. `exakit status` - confirm the runtime is `running`.
2. Open all 4 dashboard URLs in your demo browser and confirm each shows data:
   - `http://127.0.0.1:5100/apps/etf-sip-advisor`
   - `http://127.0.0.1:5100/apps/nifty-wealth-advisor`
   - `http://127.0.0.1:5100/apps/student-performance`
   - `http://127.0.0.1:5100/apps/employee-insights`
3. Do a full **dry run** of the live-reload moment you plan to show on stage,
   using `refresh-table.sh`, and confirm the chart actually updates when you
   reload the browser tab. Don't discover surprises live.
4. Close and reopen the browser tabs once after the dry run so you start the
   real demo from a known-clean state.
5. Turn off automatic OS/network updates and sleep on the demo machine for the
   duration of the summit - a surprise reboot rotates the Exasol password and
   your dashboards go blank mid-talk.

## Live-reload moment (on stage)

1. Have a terminal window ready, already `cd`'d to `~/ai-summit-demo`.
2. Say what you're about to do, then run:
   ```
   ./refresh-table.sh STARTER_KIT.MW_ETF_05_AUG_2026 /path/to/todays/MW-ETF-*.csv
   ```
3. Switch to the browser tab and reload it (or just wait up to 60s - the
   dashboard auto-refreshes on its own interval). The numbers/charts update
   live in front of the audience.
4. If anything looks wrong: run `./sync-credential.sh` first (covers the most
   likely failure), then retry step 2.

## Cold start: uninstall now (off-stage), fresh install live (on-stage)

Two separate moments, don't conflate them:

- **Uninstall happens now, before the summit, with nobody watching.** It's
  just to leave the machine clean so the live install has something to do.
- **The fresh install is the on-stage moment.** That's the part the audience
  actually sees - `exakit uninstall` never happens in front of them.

This is a different, bigger reset than "refresh some data" - it wipes the
entire local Exasol database. Know exactly what survives and what doesn't:

**Removed by `exakit uninstall`:** the local Exasol DB and ALL its data,
`~/.exasol-starter-kit` (credentials, logs, pyexasol venv), exapump profiles,
and the MCP connection config inside Claude Code / Claude Desktop / Cursor /
Codex.

**NOT touched:** `~/dash-server` and everything in it - the 4 dashboards
(their `app.py`, SQL queries, design) survive completely untouched. You do
not need to rebuild anything dashboard-side after a reinstall.

**The catch:** reconnecting the MCP server requires restarting Claude Code.
The conversation you're using to load files in cannot "keep going" through a
reinstall - after the curl install re-registers MCP, you must open a **new**
Claude Code session before handing over file paths. Plan the demo narration
around that beat (e.g. "let's open a fresh Claude session now that the
database is back").

### Exact sequence

**Off-stage, now, machine left idle until the summit:**

0. `exakit uninstall --yes` - irreversible, wipes the local DB and all
   starter-kit state. Nobody sees this.

**On-stage, at the summit, in front of the audience:**

1. Run the install command from the summit slide/notes
   (the public `install.sh` one-liner). Answer its prompts (MCP client =
   Claude Code, sample data = your choice) or let it use defaults if it's
   non-interactive.
2. **Open a new Claude Code session** (there is no "old" MCP connection left
   at this point - the machine was left uninstalled since step 0). This is
   simply "open Claude Code" as your very first on-stage AI step.
3. In that session, give Claude the 7 file paths as before - it re-uploads
   everything into the exact same table names (see reference table above),
   since `~/dash-server`'s apps are unchanged and still expect those names.
4. Do your text-to-SQL demo moment in that same session.
5. **Run the dashboard command** (this is the one new thing a fresh install
   requires that a same-session data refresh doesn't):
   ```
   ~/ai-summit-demo/sync-credential.sh
   ```
   This is required every time because the reinstall generates a brand-new
   `mcp_readonly` password, and `dash-server`'s stored credential for it goes
   stale immediately - exactly the auth failure from earlier today, just
   triggered by reinstall instead of a plain restart.
6. Open the 4 dashboard URLs (see Pre-demo checklist above).

### Rehearse this exact sequence at least once before the real event

Do a full dry run of steps 0-6 beforehand - uninstall, then reinstall, then
the whole Claude Code + upload + dashboard flow - so the on-stage install
(steps 1-6) has zero surprises left in it. A live install in front of 1,000
people is still real-time and network-dependent (a slow/failed curl, a slow
deploy, a fumbled prompt answer), so know the install's expected timing and
what each prompt asks before you're up there.

## Fallback plan (do not skip this)

Load real, working data into every table **before you go on stage**, so the
dashboards look complete and correct even if the live-reload step doesn't go
perfectly. Treat "loading fresh data live" as a flourish on top of an already-
working demo, not the only path to a working demo. If the live reload hiccups
in front of 1,000 people, you can say "let's come back to that" and move on -
the dashboards still have good data on screen from before you went up.

## If something breaks mid-demo

- Charts blank / "authentication failed" anywhere → `./sync-credential.sh`
- Charts blank but no auth error → check you loaded into the exact table name
  above, and that you used `TRUNCATE` (not a fresh table with a new name).
- Whole server unresponsive → restart it:
  ```
  pkill -f '.venv/bin/dash-server$'
  cd ~/dash-server && nohup .venv/bin/dash-server > /tmp/dash-server.log 2>&1 &
  ```

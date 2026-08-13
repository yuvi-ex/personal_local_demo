# Getting Started From Scratch

`RUNBOOK.md` assumes the local Exasol + dash-server stack already exists (it's the
on-stage/day-of playbook). This document is the missing piece: how to go from a fresh
clone of this repo to the whole demo running, on a machine that has nothing installed
yet.

Prerequisites: macOS or Linux, 8GB+ RAM, Python 3.11+.

## 1. Install Exasol Personal (Local Starter Kit)

```bash
curl -fsSL https://raw.githubusercontent.com/exasol-labs/exasol-personal-local-starterkit/main/install.sh | sh
```

Repo: [exasol-labs/exasol-personal-local-starterkit](https://github.com/exasol-labs/exasol-personal-local-starterkit).
Answer its prompts (MCP client = your AI assistant of choice; sample data = your
choice). This installs the `exakit`/`exasol`/`exapump` CLIs and a local Exasol database
listening on `127.0.0.1:8563`.

## 2. Install the Python3 script language container

The local runtime ships with no UDF language containers by default:

```bash
exasol slc install python3 --auto-approve
```

This restarts the database once to mount it (~30-60s) — a normal step, not a problem.

## 3. Install and start dash-server

```bash
git clone https://github.com/exasol-labs/dash-server.git
cd dash-server
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

Register the same Exasol profile every dashboard in this repo expects, by copying it
into dash-server's own GitOps state before first start:

```bash
mkdir -p instance/gitops-repo/profiles/exasol
cp /path/to/personal_local_demo/dashboards/profiles/exasol/starter-kit.json \
   instance/gitops-repo/profiles/exasol/starter-kit.json
```

Then start it:

```bash
dash-server
```

Default local URL: `http://127.0.0.1:5100`. The profile's `secret_ref` points at a
local file dash-server manages itself — the actual `mcp_readonly` password is synced
into it by `sync-credential.sh` (step 6), not stored anywhere in this repo.

## 4. Load the data

Each dashboard's SQL is hardcoded to an exact table name — see the reference table in
`RUNBOOK.md`. Load every CSV in `data/` into its matching table with `exapump`:

```bash
exapump upload data/MW-ETF-05-Aug-2026.csv                      --table STARTER_KIT.MW_ETF_05_AUG_2026            -p starter-kit
exapump upload data/MW-NIFTY-50-04-Aug-2026.csv                  --table STARTER_KIT.MW_NIFTY_50_04_AUG_2026        -p starter-kit
exapump upload data/MW-NIFTY-BANK-04-Aug-2026.csv                --table STARTER_KIT.MW_NIFTY_BANK_04_AUG_2026      -p starter-kit
exapump upload data/MW-NIFTY-FINANCIAL-SERVICES-04-Aug-2026.csv  --table STARTER_KIT.MW_NIFTY_FINANCIAL_SERVICES_04_AUG_2026 -p starter-kit
exapump upload data/MW-NIFTY-MIDCAP-SELECT-04-Aug-2026.csv       --table STARTER_KIT.MW_NIFTY_MIDCAP_SELECT_04_AUG_2026 -p starter-kit
exapump upload data/MW-NIFTY-NEXT-50-04-Aug-2026.csv             --table STARTER_KIT.MW_NIFTY_NEXT_50_04_AUG_2026   -p starter-kit
exapump upload "data/Students Performance Dataset.csv"           --table STARTER_KIT.STUDENTS_PERFORMANCE_DATASET_CLEAN -p starter-kit
exapump upload data/employees.csv                                --table STARTER_KIT.EMPLOYEES                     -p starter-kit
exapump upload ml/WA_Fn-UseC_-Telco-Customer-Churn.csv           --table STARTER_KIT.TELCO_CUSTOMER_CHURN           -p starter-kit
```

(`exapump upload` creates the table on first load since none of these exist yet; use
`refresh-table.sh` instead for any later reload so you truncate rather than duplicate.)

## 5. Train and deploy the churn model

```bash
cd ml
python3 -m venv churn_demo_venv
source churn_demo_venv/bin/activate
pip install pandas==2.3.2 scikit-learn==1.7.2 numpy==1.26.4   # pinned to match the SLC's installed versions — see note below
python train_model.py     # writes churn_model.pkl
```

**Why pinned versions:** a model pickled with numpy 2.x fails to load inside the UDF,
which runs numpy 1.26.4 (numpy 2.x renamed an internal module the pickle depends on).
Check the SLC's actual installed versions any time with a one-line diagnostic UDF if
you're unsure they still match.

Upload the trained model into Exasol's BucketFS. This requires SSH access to the local
Exasol VM — get the port and key path from
`~/.exasol/personal/deployments/default/deployment.json` (`connection.sshPort`) and
`local/node_access.pem`:

```bash
scp -i <deployment_dir>/local/node_access.pem -P <sshPort> \
  churn_model.pkl root@127.0.0.1:/var/lib/exa/bucketfs/bfsdefault/default/churn_model.pkl
```

The first time you register a new bucket path like this, restart Exasol so it's
reconciled and exposed to UDFs (`exasol stop && exasol start`); replacing the file
in-place later does not need a restart. A restart rotates the `mcp_readonly` password,
so run `sync-credential.sh` afterward.

Create the UDF and build the scored table:

```bash
exapump sql -p starter-kit < predict_churn.sql
exapump sql -p starter-kit < build_churn_scores.sql
```

## 6. Sync the credential and start the dashboards

```bash
cd ..
./sync-credential.sh
```

Restore the 5 dashboards from `dashboards/apps/` into dash-server. The supported way is
through dash-server's own MCP tools (the same way they were originally built) — connect
an MCP-capable AI assistant to `http://127.0.0.1:5100/mcp` and, for each folder under
`dashboards/apps/`, have it call `app_create_from_files` with that folder's files, then
`app_validate` → `app_deploy_draft` (`deployment_target: "live"`) → `app_start`.

Once running, open:

- `http://127.0.0.1:5100/apps/etf-sip-advisor`
- `http://127.0.0.1:5100/apps/nifty-wealth-advisor`
- `http://127.0.0.1:5100/apps/student-performance`
- `http://127.0.0.1:5100/apps/employee-insights`
- `http://127.0.0.1:5100/apps/churn-insights`

From here, `RUNBOOK.md` covers day-to-day operation: refreshing data live on stage,
fixing the credential-rotation error, and the full cold-start (uninstall/reinstall)
sequence.

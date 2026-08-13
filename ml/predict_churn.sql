CREATE OR REPLACE PYTHON3 SCALAR SCRIPT STARTER_KIT.predict_churn(
    "tenure" DECIMAL(36,0),
    "MonthlyCharges" DOUBLE,
    "Contract" VARCHAR(50)
)
RETURNS DOUBLE AS

import pickle

_bundle = None

def _load_bundle():
    global _bundle
    if _bundle is None:
        with open('/buckets/bfsdefault/default/churn_model.pkl', 'rb') as f:
            _bundle = pickle.load(f)
    return _bundle

def run(ctx):
    bundle = _load_bundle()
    model = bundle["model"]
    le_contract = bundle["contract_encoder"]

    try:
        contract_enc = le_contract.transform([ctx.Contract])[0]
    except ValueError:
        contract_enc = 0  # unseen category fallback

    features = [[ctx.tenure, ctx.MonthlyCharges, contract_enc]]
    proba = model.predict_proba(features)[0][1]
    return float(proba)

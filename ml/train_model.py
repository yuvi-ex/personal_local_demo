# train_model.py
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Load however you originally got the CSV in (same file used for Exasol load)
df = pd.read_csv("WA_Fn-UseC_-Telco-Customer-Churn.csv")

# --- clean TotalCharges: blank strings for tenure=0 customers ---
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["TotalCharges"] = df["TotalCharges"].fillna(0)

# --- encode categorical fields we'll use as features ---
le_contract = LabelEncoder()
df["Contract_enc"] = le_contract.fit_transform(df["Contract"])

le_churn = LabelEncoder()
df["Churn_enc"] = le_churn.fit_transform(df["Churn"])  # Yes/No -> 1/0

features = ["tenure", "MonthlyCharges", "Contract_enc"]
X = df[features]
y = df["Churn_enc"]

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

bundle = {
    "model": model,
    "contract_encoder": le_contract,
    "churn_encoder": le_churn,   # keep for reference (0/1 -> No/Yes)
    "feature_order": features,
}

with open("churn_model.pkl", "wb") as f:
    pickle.dump(bundle, f)

print("Saved churn_model.pkl")
print("Contract classes:", list(le_contract.classes_))
print("Churn classes:", list(le_churn.classes_))

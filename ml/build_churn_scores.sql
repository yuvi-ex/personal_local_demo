CREATE OR REPLACE TABLE STARTER_KIT.CHURN_SCORES AS
SELECT "customerID", "tenure", "MonthlyCharges", "Contract", "Churn",
       STARTER_KIT.predict_churn("tenure", "MonthlyCharges", "Contract") AS churn_probability
FROM STARTER_KIT.TELCO_CUSTOMER_CHURN

import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

from generate_data import generate_dataset
from preprocess import preprocess_data

df = generate_dataset()

X = preprocess_data(df) 

# Initialize and train Isolation Forest
model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=6,
    verbose=1,
    n_jobs=-1
)

model.fit(X)
print("Prediction model trained")

# Save model
joblib.dump(model, "../models/isolation_forest_model.pkl")
print("Prediction model saved\n")
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

from generate_data import generate_dataset
from preprocess import preprocess_data

df = generate_dataset()

df_preproc = preprocess_data(df)

# print("Fitting isolation forest model\n")       # To comment after first use
# model = IsolationForest(n_estimators=100,
#                         contamination=0.05,
#                         random_state=6,
#                         verbose = 3,
#                         n_jobs=-1)              # To comment after first use

# model.fit(df_preproc)                           # To comment after first use
# print("Isolation model fitted\n")               # To comment after first use

model = joblib.load("../models/isolation_forest_model.pkl")
print("Loaded prediction model\n")

# Savind model (To comment after first use)
# joblib.dump(model, "../models/isolation_forest_model.pkl")
# print("Prediction model saved\n")
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

def preprocess_data(df):
    df_encoded = pd.get_dummies(df, columns = ["location", "device_type", "transaction_type"])

    features = ["amount", "merchant_id", "user_id"] + \
               [col for col in df_encoded.columns if col.startswith(("location_", "device_type_", "transaction_type_"))]

    # scaler = StandardScaler()                       # To comment after first use
    scaler = joblib.load("../models/std_scaler.pkl") # To uncomment if model exists

    # X = scaler.fit_transform(df_encoded[features])  # To comment after first use 
    X = scaler.transform(df_encoded[features])
    print("Data preprocessed\n")
    # joblib.dump(scaler, "std_scaler.pkl")           # To comment after first use
    # print("Standard scaler saved\n")                # To comment after first use

    return X
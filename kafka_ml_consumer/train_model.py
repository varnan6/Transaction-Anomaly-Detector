import os
import joblib
from sklearn.ensemble import IsolationForest

from scripts.generate_data import generate_dataset
from utils.transformer import FeatureTransformer

### Configs
MODEL_DIR = "../models"
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest_model.pkl")
TRANSFORMER_PATH = os.path.join(MODEL_DIR, "feature_transformer.pkl")

def main():

    os.makedirs(MODEL_DIR, exist_ok=True)

    print("="*5 + "Generate synthetic data"+ "="*5)
    df = generate_dataset(n_normal = 950, n_fraud=50)

    print("="*5 + "Fitting feature transformer" + "="*5)
    transformer = FeatureTransformer()
    X = transformer.fit_transform(df)

    print("="*5 + "Training Isolation Forest Model on transformed synthetic data" + "="*5)
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=6,
        n_jobs=-1,
        verbose=1
    )

    model.fit(X)
    print("="*5 + "Model training completed" + "="*5)

    print("="*5 + "Dumping model" + "="*5)
    joblib.dump(model, MODEL_PATH)
    print("="*5 + "Saving transformer" + "="*5)
    transformer.save(TRANSFORMER_PATH)

    print("Save locations: \n")
    print(f"Model: {MODEL_PATH}")
    print(f"Transformer: {TRANSFORMER_PATH}")


if __name__ == "__main__":
    main()
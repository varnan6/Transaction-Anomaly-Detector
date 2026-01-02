from sklearn.preprocessing import StandardScaler
import pandas as pd
import joblib

class FeatureTransformer:

    def __init__(self):

        self.numerical_columns = [
            "amount",
            "merchant_id",
            "user_id"
        ]

        self.categorical_columns = [
            "location",
            "device_type",
            "transaction_type"
        ]

        self.scaler = StandardScaler()
        self.feature_columns_ = None
        self._is_fitted = False

    
####### Core functions
    def fit(self, df: pd.DataFrame):

        df = self._validate_input(df) # The dataframe is validated for proper input

        df_encoded = pd.get_dummies(
            df,
            columns = self.categorical_columns,
            drop_first=False
        )

        self.feature_columns_ = (
            self.numerical_columns + [col for col in df_encoded.columns if col not in self.numerical_columns and col not in self._ignored_columns()]
        ) # Setting the final features as a set of numerical columns and one hot encoded categorical columns (excluding the columns which are to be ignored)

        self.scaler.fit(df_encoded[self.numerical_columns]) # Fitting standardizing function on numerical columns
        self._is_fitted = True

        return self
    
    def transform(self, df: pd.DataFrame):

        if not self._is_fitted:
            raise RuntimeError("The transformer must be fitted before calling transform() function")
        
        df = self._validate_input(df) # Validating dataframe consistency

        # One hot encoding the categorical columns
        df_encoded = pd.get_dummies(
            df,
            columns = self.categorical_columns,
            drop_first=False
        )

        # If the col is not present in the one hot encoded df, then add that column with a "0" value
        for col in self.feature_columns_:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        
        df_encoded = df_encoded[self.feature_columns_]

        # Scale numerical features
        df_encoded[self.numerical_columns] = self.scaler.transform(
            df_encoded[self.numerical_columns]
        )

        return df_encoded.values
    
    def fit_transform(self, df: pd.DataFrame):
        self.fit(df)
        return self.transform(df)
    
####### Auxiliary functions
    def save(self, path: str):
        joblib.dump(self, path)

    @staticmethod
    def load(path: str):
        return joblib.load(path)

####### Internal Helping Functions
    def _ignored_columns(self):
        return {"transaction_id",
                "timestamp",
                "is_fraud"}
    
    def _validate_input(self, df: pd.DataFrame):

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input is not a pandas DataFrame")

        df = df.copy()

        for col in self._ignored_columns():
            if col in df.columns:
                df.drop(columns = col, inplace = True)
        
        required_cols = set(self.numerical_columns + self.categorical_columns)
        missing = required_cols - set(df.columns)
        
        if missing:
            raise ValueError(f"Columns missing: {missing}")
        
        return df

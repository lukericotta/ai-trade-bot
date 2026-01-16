import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class DataAnalyzer:
    """
    Analyzes market data using technical indicators and machine learning models.
    """

    def __init__(self, config):
        self.config = config
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def compute_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Compute technical indicators such as Moving Average, RSI, etc.

        Args:
            data: DataFrame containing historical price data

        Returns:
            DataFrame: Enhanced data with technical indicators
        """
        # Example: adding moving averages
        data['SMA_10'] = data['close'].rolling(window=10).mean()
        data['SMA_50'] = data['close'].rolling(window=50).mean()
        
        # Example: calculating RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        return data
    
    def train_model(self, features: pd.DataFrame, targets: pd.Series):
        """
        Train a machine learning model on the provided features and targets.

        Args:
            features: DataFrame with feature columns
            targets: Series with target variable (trade signals)
        """
        # Scale the features
        features_scaled = self.scaler.fit_transform(features)

        # Train the model
        self.model.fit(features_scaled, targets)

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        Use the model to make predictions on current data.

        Args:
            features: DataFrame with feature columns

        Returns:
            np.ndarray: Predicted signals
        """
        features_scaled = self.scaler.transform(features)
        predictions = self.model.predict(features_scaled)
        return predictions

    def evaluate_model(self, features: pd.DataFrame, targets: pd.Series) -> float:
        """
        Evaluate the model's accuracy on a test dataset.

        Args:
            features: DataFrame with test feature columns
            targets: Series with test target variable

        Returns:
            float: Accuracy score
        """
        features_scaled = self.scaler.transform(features)
        accuracy = self.model.score(features_scaled, targets)
        return accuracy

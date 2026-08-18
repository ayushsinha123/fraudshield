from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "synthetic_user_transactions.csv"
)

MODEL_DIR = PROJECT_ROOT / "models" / "behaviour"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


BEHAVIOUR_FEATURES = [
    "amount",
    "hour",
    "new_recipient",
    "new_device",
    "unusual_hour",
    "burst",
    "location_jump",
    "network_change",
]


class BehaviourEngine:

    def __init__(self):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.10,
            random_state=42,
            n_jobs=-1,
        )

        self.scaler = MinMaxScaler()

    def load_data(self):
        if not DATA_PATH.exists():
            raise FileNotFoundError(
                f"Behaviour dataset not found: {DATA_PATH}"
            )

        return pd.read_csv(DATA_PATH)

    def fit(self, df: pd.DataFrame):

        X = df[BEHAVIOUR_FEATURES].copy()

        # Scale numerical values
        X_scaled = self.scaler.fit_transform(X)

        self.model.fit(X_scaled)

        return self

    def score_transaction(self, transaction: dict):

        X = pd.DataFrame(
            [transaction],
            columns=BEHAVIOUR_FEATURES
        )

        X_scaled = self.scaler.transform(X)

        anomaly_score = self.model.decision_function(X_scaled)[0]
        anomaly_prediction = self.model.predict(X_scaled)[0]

        # Convert anomaly score into 0-100 risk
        raw_risk = max(
            0,
            min(
                100,
                (0.5 - anomaly_score) * 100
            )
        )

        reasons = []

        if transaction.get("new_device", 0) == 1:
            raw_risk += 25
            reasons.append("New device detected")

        if transaction.get("new_recipient", 0) == 1:
            raw_risk += 20
            reasons.append("New recipient detected")

        if transaction.get("unusual_hour", 0) == 1:
            raw_risk += 15
            reasons.append("Unusual transaction time")

        if transaction.get("burst", 0) == 1:
            raw_risk += 15
            reasons.append("Unusual transaction burst")

        if transaction.get("location_jump", 0) == 1:
            raw_risk += 15
            reasons.append("Unusual location change")

        if transaction.get("network_change", 0) == 1:
            raw_risk += 10
            reasons.append("Network change detected")

        if anomaly_prediction == -1:
            reasons.append("Overall transaction behaviour is anomalous")

        risk = int(max(0, min(100, raw_risk)))

        return {
            "behaviour_risk": risk,
            "is_anomalous": bool(anomaly_prediction == -1),
            "reasons": reasons,
        }


if __name__ == "__main__":

    print("Loading synthetic behaviour data...")

    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:", df.shape)

    engine = BehaviourEngine()

    print("Training Isolation Forest...")
    engine.fit(df)

    print("Behaviour model trained successfully.")

    # Test transaction
    test_transaction = {
        "amount": 25000,
        "hour": 2,
        "new_recipient": 1,
        "new_device": 1,
        "unusual_hour": 1,
        "burst": 1,
        "location_jump": 0,
        "network_change": 1,
    }

    result = engine.score_transaction(test_transaction)

    print("\nTest result:")
    print(result)
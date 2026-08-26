# backend/app/services/behaviour_engine.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd


class BehaviourEngine:
    """
    FraudShield behaviour-risk inference service.

    Loads the exact Isolation Forest + MinMaxScaler artifacts
    produced by ml/behaviour/behaviour_model.py and reproduces
    its deterministic rule layer.

    Output:
        behaviour_risk: 0-100
        is_anomalous: bool
        reasons: list[str]
    """

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

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        scaler_path: Optional[str | Path] = None,
    ) -> None:

        project_root = (
            Path(__file__).resolve().parents[3]
        )

        if model_path is None:
            model_path = (
                project_root
                / "models"
                / "behaviour"
                / "behaviour_engine.joblib"
            )

        if scaler_path is None:
            scaler_path = (
                project_root
                / "models"
                / "behaviour"
                / "behaviour_scaler.joblib"
            )

        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)

        # ------------------------------------------
        # Validate artifact files
        # ------------------------------------------

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Behaviour model not found: "
                f"{self.model_path}"
            )

        if not self.scaler_path.exists():
            raise FileNotFoundError(
                f"Behaviour scaler not found: "
                f"{self.scaler_path}"
            )

        # ------------------------------------------
        # Load artifacts
        # ------------------------------------------

        self.model = joblib.load(
            self.model_path
        )

        self.scaler = joblib.load(
            self.scaler_path
        )

        print(
            "BehaviourEngine loaded successfully:"
        )

        print(
            f"  model = {self.model_path}"
        )

        print(
            f"  scaler = {self.scaler_path}"
        )

        print(
            f"  features = "
            f"{len(self.BEHAVIOUR_FEATURES)}"
        )

    # ------------------------------------------------
    # Validation
    # ------------------------------------------------

    def _validate_transaction(
        self,
        transaction: Dict[str, Any],
    ) -> None:

        missing = [
            feature
            for feature in self.BEHAVIOUR_FEATURES
            if feature not in transaction
        ]

        if missing:
            raise ValueError(
                "Missing behaviour features: "
                f"{missing}"
            )

        try:
            float(transaction["amount"])
            int(transaction["hour"])

            for feature in [
                "new_recipient",
                "new_device",
                "unusual_hour",
                "burst",
                "location_jump",
                "network_change",
            ]:
                int(transaction[feature])

        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid behaviour feature values."
            ) from exc

    # ------------------------------------------------
    # Feature construction
    # ------------------------------------------------

    def _build_feature_frame(
        self,
        transaction: Dict[str, Any],
    ) -> pd.DataFrame:

        self._validate_transaction(
            transaction
        )

        row = {
            feature: transaction[feature]
            for feature in self.BEHAVIOUR_FEATURES
        }

        X = pd.DataFrame(
            [row],
            columns=self.BEHAVIOUR_FEATURES,
        )

        return X

    # ------------------------------------------------
    # Score transaction
    # ------------------------------------------------

    def score_transaction(
        self,
        transaction: Dict[str, Any],
    ) -> Dict[str, Any]:

        X = self._build_feature_frame(
            transaction
        )

        # ------------------------------------------
        # Scale exactly as training did
        # ------------------------------------------

        X_scaled = self.scaler.transform(
            X
        )

        # ------------------------------------------
        # Isolation Forest
        # ------------------------------------------

        anomaly_score = float(
            self.model.decision_function(
                X_scaled
            )[0]
        )

        anomaly_prediction = int(
            self.model.predict(
                X_scaled
            )[0]
        )

        # ------------------------------------------
        # Convert anomaly score to 0-100 risk
        #
        # Same formula used in the original model.
        # ------------------------------------------

        raw_risk = max(
            0.0,
            min(
                100.0,
                (0.5 - anomaly_score) * 100.0,
            ),
        )

        reasons: list[str] = []

        # ------------------------------------------
        # Deterministic rules
        # ------------------------------------------

        if int(
            transaction.get(
                "new_device",
                0,
            )
        ) == 1:

            raw_risk += 25

            reasons.append(
                "New device detected"
            )

        if int(
            transaction.get(
                "new_recipient",
                0,
            )
        ) == 1:

            raw_risk += 20

            reasons.append(
                "New recipient detected"
            )

        if int(
            transaction.get(
                "unusual_hour",
                0,
            )
        ) == 1:

            raw_risk += 15

            reasons.append(
                "Unusual transaction time"
            )

        if int(
            transaction.get(
                "burst",
                0,
            )
        ) == 1:

            raw_risk += 15

            reasons.append(
                "Unusual transaction burst"
            )

        if int(
            transaction.get(
                "location_jump",
                0,
            )
        ) == 1:

            raw_risk += 15

            reasons.append(
                "Unusual location change"
            )

        if int(
            transaction.get(
                "network_change",
                0,
            )
        ) == 1:

            raw_risk += 10

            reasons.append(
                "Network change detected"
            )

        if anomaly_prediction == -1:

            reasons.append(
                "Overall transaction behaviour "
                "is anomalous"
            )

        # ------------------------------------------
        # Final risk
        # ------------------------------------------

        risk = int(
            max(
                0,
                min(
                    100,
                    raw_risk,
                ),
            )
        )

        # ------------------------------------------
        # Risk level
        # ------------------------------------------

        if risk >= 80:
            risk_level = "CRITICAL"

        elif risk >= 60:
            risk_level = "HIGH"

        elif risk >= 30:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

        return {
            "behaviour_risk": risk,
            "risk_level": risk_level,
            "is_anomalous": (
                anomaly_prediction == -1
            ),
            "anomaly_score": round(
                anomaly_score,
                6,
            ),
            "reasons": reasons,
        }


# ---------------------------------------------------------
# Local smoke test
# ---------------------------------------------------------

if __name__ == "__main__":

    engine = BehaviourEngine()

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

    result = engine.score_transaction(
        test_transaction
    )

    print(
        "\nBehaviour test result:"
    )

    print(result)
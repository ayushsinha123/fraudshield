from __future__ import annotations

import json

from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd
import shap


class TransactionModel:
    """
    FraudShield transaction-risk inference service.

    Loads the frozen Notebook 02 production XGBoost model and
    reproduces the exact 21-feature preprocessing pipeline.

    Important:
    - Balance-derived PaySim features are NOT used.
    - nameDest is NOT passed directly to XGBoost.
    - nameDest is used only to maintain causal recipient history.
    - Recipient state is updated AFTER the current transaction
      is scored.
    """

    TRANSACTION_TYPES = [
        "CASH_IN",
        "CASH_OUT",
        "DEBIT",
        "PAYMENT",
        "TRANSFER",
    ]

    FEATURE_COLUMNS = [
        "step",
        "amount",
        "hour",
        "day",
        "hour_sin",
        "hour_cos",
        "log_amount",
        "amount_vs_type_mean",
        "amount_vs_type_median",
        "amount_vs_global_median",
        "above_train_p95",
        "above_train_p99",
        "dest_prev_tx_count",
        "log_dest_prev_tx_count",
        "amount_vs_dest_history",
        "new_recipient",
        "type_CASH_IN",
        "type_CASH_OUT",
        "type_DEBIT",
        "type_PAYMENT",
        "type_TRANSFER",
    ]

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
    ) -> None:

        if model_path is None:
            model_path = (
                Path(__file__).resolve()
                .parents[3]
                / "models"
                / "transaction"
                / "transaction_model.joblib"
            )

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Transaction model artifact not found: "
                f"{self.model_path}"
            )

        artifact = joblib.load(self.model_path)

        if not isinstance(artifact, dict):
            raise ValueError(
                "Invalid transaction artifact: "
                "expected a dictionary."
            )

        required_keys = [
            "model",
            "features",
            "training_statistics",
        ]

        missing = [
            key
            for key in required_keys
            if key not in artifact
        ]

        if missing:
            raise ValueError(
                "Transaction artifact is missing keys: "
                f"{missing}"
            )

        self.model = artifact["model"]

        artifact_features = artifact["features"]

        if artifact_features != self.FEATURE_COLUMNS:
            raise ValueError(
                "Feature schema mismatch.\n"
                f"Artifact features: {artifact_features}\n"
                f"Expected features: {self.FEATURE_COLUMNS}"
            )

        training_stats = artifact[
            "training_statistics"
        ]

        self.type_stats = (
            pd.DataFrame(
                training_stats["type_stats"]
            )
        )

        self.global_stats = (
            training_stats["global_amount_stats"]
        )

        # Causal recipient state.
        #
        # key = recipient identifier
        # value = historical statistics
        self.recipient_state: Dict[str, Dict[str, float]] = {}

        # SHAP explainer is created once.
        self.explainer = shap.TreeExplainer(
            self.model
        )

        print(
            "TransactionModel loaded successfully:"
        )
        print(
            f"  artifact = {self.model_path}"
        )
        print(
            f"  features = {len(self.FEATURE_COLUMNS)}"
        )

    # ---------------------------------------------------------
    # Recipient history
    # ---------------------------------------------------------

    def _get_recipient_history(
        self,
        recipient_id: str,
    ) -> Dict[str, float]:

        state = self.recipient_state.get(
            recipient_id
        )

        if state is None:
            return {
                "dest_prev_tx_count": 0.0,
                "dest_prev_mean_amount": float(
                    self.global_stats["median"]
                ),
            }

        return {
            "dest_prev_tx_count": float(
                state["count"]
            ),
            "dest_prev_mean_amount": float(
                state["amount_sum"]
                / max(state["count"], 1.0)
            ),
        }

    def _update_recipient_history(
        self,
        recipient_id: str,
        amount: float,
    ) -> None:

        if recipient_id not in self.recipient_state:
            self.recipient_state[
                recipient_id
            ] = {
                "count": 0.0,
                "amount_sum": 0.0,
            }

        self.recipient_state[
            recipient_id
        ]["count"] += 1.0

        self.recipient_state[
            recipient_id
        ]["amount_sum"] += amount

    # ---------------------------------------------------------
    # Feature engineering
    # ---------------------------------------------------------

    def _build_features(
        self,
        transaction: Dict[str, Any],
        update_history: bool = False,
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:

        required = [
            "step",
            "type",
            "amount",
            "nameDest",
        ]

        missing = [
            key
            for key in required
            if key not in transaction
        ]

        if missing:
            raise ValueError(
                f"Missing transaction fields: {missing}"
            )

        step = int(
            transaction["step"]
        )

        amount = float(
            transaction["amount"]
        )

        transaction_type = str(
            transaction["type"]
        )

        recipient_id = str(
            transaction["nameDest"]
        )

        if transaction_type not in self.TRANSACTION_TYPES:
            raise ValueError(
                f"Unknown transaction type: "
                f"{transaction_type}"
            )

        if amount < 0:
            raise ValueError(
                "Transaction amount cannot be negative."
            )

        # -----------------------------------------------------
        # Recipient history BEFORE current transaction
        # -----------------------------------------------------

        recipient_history = (
            self._get_recipient_history(
                recipient_id
            )
        )

        prev_count = recipient_history[
            "dest_prev_tx_count"
        ]

        prev_mean_amount = recipient_history[
            "dest_prev_mean_amount"
        ]

        new_recipient = (
            1 if prev_count == 0 else 0
        )

        # -----------------------------------------------------
        # Time
        # -----------------------------------------------------

        hour = step % 24
        day = step // 24

        hour_sin = np.sin(
            2 * np.pi * hour / 24
        )

        hour_cos = np.cos(
            2 * np.pi * hour / 24
        )

        # -----------------------------------------------------
        # Amount
        # -----------------------------------------------------

        log_amount = np.log1p(
            amount
        )

        type_mean = float(
            self.type_stats[
                "type_mean"
            ].get(
                transaction_type,
                self.global_stats["mean"],
            )
        )

        type_median = float(
            self.type_stats[
                "type_median"
            ].get(
                transaction_type,
                self.global_stats["median"],
            )
        )

        amount_vs_type_mean = (
            amount
            / (type_mean + 1.0)
        )

        amount_vs_type_median = (
            amount
            / (type_median + 1.0)
        )

        amount_vs_global_median = (
            amount
            / (
                self.global_stats["median"]
                + 1.0
            )
        )

        above_train_p95 = int(
            amount
            >= self.global_stats["p95"]
        )

        above_train_p99 = int(
            amount
            >= self.global_stats["p99"]
        )

        # -----------------------------------------------------
        # Recipient-history features
        # -----------------------------------------------------

        amount_vs_dest_history = (
            amount
            / (
                prev_mean_amount
                + 1.0
            )
        )

        log_dest_prev_tx_count = (
            np.log1p(prev_count)
        )

        # -----------------------------------------------------
        # Transaction type one-hot
        # -----------------------------------------------------

        type_flags = {
            f"type_{t}": int(
                transaction_type == t
            )
            for t in self.TRANSACTION_TYPES
        }

        # -----------------------------------------------------
        # EXACT 21 features
        # -----------------------------------------------------

        feature_row = {
            "step": step,
            "amount": amount,
            "hour": hour,
            "day": day,
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "log_amount": log_amount,
            "amount_vs_type_mean": (
                amount_vs_type_mean
            ),
            "amount_vs_type_median": (
                amount_vs_type_median
            ),
            "amount_vs_global_median": (
                amount_vs_global_median
            ),
            "above_train_p95": (
                above_train_p95
            ),
            "above_train_p99": (
                above_train_p99
            ),
            "dest_prev_tx_count": (
                prev_count
            ),
            "log_dest_prev_tx_count": (
                log_dest_prev_tx_count
            ),
            "amount_vs_dest_history": (
                amount_vs_dest_history
            ),
            "new_recipient": (
                new_recipient
            ),
            **type_flags,
        }

        X = pd.DataFrame(
            [feature_row],
            columns=self.FEATURE_COLUMNS,
        )

        # Update recipient history ONLY after
        # feature construction.
        if update_history:
            self._update_recipient_history(
                recipient_id,
                amount,
            )

        context = {
            "recipient_id": recipient_id,
            "previous_recipient_count": (
                prev_count
            ),
            "previous_recipient_mean": (
                prev_mean_amount
            ),
            "new_recipient": bool(
                new_recipient
            ),
            "amount_vs_recipient_history": (
                amount_vs_dest_history
            ),
        }

        return X, context

    # ---------------------------------------------------------
    # SHAP explanation
    # ---------------------------------------------------------

    def _build_reasons(
        self,
        X: pd.DataFrame,
        shap_values: np.ndarray,
        context: Dict[str, Any],
        top_k: int = 5,
    ) -> list[str]:

        values = np.asarray(
            shap_values
        )

        if values.ndim == 2:
            values = values[0]

        pairs = list(
            zip(
                self.FEATURE_COLUMNS,
                values,
                strict=True,
            )
        )

        # Only keep features pushing the
        # prediction toward fraud.
        positive = [
            (feature, float(value))
            for feature, value in pairs
            if value > 0
        ]

        positive.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        reasons = []

        amount = float(
            X.iloc[0]["amount"]
        )

        amount_vs_dest = float(
            context[
                "amount_vs_recipient_history"
            ]
        )

        new_recipient = context[
            "new_recipient"
        ]

        if new_recipient:
            reasons.append(
                "New recipient detected"
            )

        elif (
            context["previous_recipient_count"]
            > 0
            and amount_vs_dest >= 2.0
        ):
            reasons.append(
                "Amount is substantially higher "
                "than this recipient's previous "
                "transaction pattern"
            )

        for feature, _ in positive:

            if len(reasons) >= top_k:
                break

            if feature in {
                "new_recipient",
                "dest_prev_tx_count",
                "amount_vs_dest_history",
                "log_dest_prev_tx_count",
            }:
                continue

            if feature == "amount":
                reasons.append(
                    f"Large transaction amount "
                    f"detected: {amount:.2f}"
                )

            elif feature == "amount_vs_type_mean":
                reasons.append(
                    "Amount is unusually high "
                    "for this transaction type"
                )

            elif feature == "amount_vs_type_median":
                reasons.append(
                    "Amount is well above the "
                    "typical median for this "
                    "transaction type"
                )

            elif feature == "amount_vs_global_median":
                reasons.append(
                    "Amount is unusually large "
                    "relative to typical transactions"
                )

            elif feature == "above_train_p95":
                reasons.append(
                    "Transaction is above the "
                    "historical high-value threshold"
                )

            elif feature == "above_train_p99":
                reasons.append(
                    "Transaction is in the extreme "
                    "high-value range"
                )

            elif feature == "hour":
                reasons.append(
                    "Transaction occurs at an "
                    "unusual time"
                )

            elif feature == "step":
                reasons.append(
                    "Transaction timing contributes "
                    "to elevated risk"
                )

            elif feature == "type_TRANSFER":
                if int(
                    X.iloc[0]["type_TRANSFER"]
                ) == 1:
                    reasons.append(
                        "Transfer transaction contributes "
                        "to elevated risk"
                    )

            elif feature == "type_CASH_OUT":
                if int(
                    X.iloc[0]["type_CASH_OUT"]
                ) == 1:
                    reasons.append(
                        "Cash-out transaction contributes "
                        "to elevated risk"
                    )

            elif feature == "type_PAYMENT":
                if int(
                    X.iloc[0]["type_PAYMENT"]
                ) == 1:
                    reasons.append(
                        "Payment transaction contributes "
                        "to elevated risk"
                    )

            elif feature == "type_CASH_IN":
                if int(
                    X.iloc[0]["type_CASH_IN"]
                ) == 1:
                    reasons.append(
                        "Cash-in transaction contributes "
                        "to elevated risk"
                    )

            elif feature == "type_DEBIT":
                if int(
                    X.iloc[0]["type_DEBIT"]
                ) == 1:
                    reasons.append(
                        "Debit transaction contributes "
                        "to elevated risk"
                    )

        if not reasons:
            reasons.append(
                "Transaction model detected "
                "no major individual risk driver"
            )

        return reasons[:top_k]

    # ---------------------------------------------------------
    # Public inference method
    # ---------------------------------------------------------

    def score_transaction(
        self,
        transaction: Dict[str, Any],
        update_history: bool = True,
    ) -> Dict[str, Any]:

        X, context = self._build_features(
            transaction,
            update_history=update_history,
        )

        probability = float(
            self.model.predict_proba(X)[0, 1]
        )

        transaction_risk = (
            probability * 100.0
        )

        if transaction_risk >= 80:
            risk_level = "CRITICAL"

        elif transaction_risk >= 60:
            risk_level = "HIGH"

        elif transaction_risk >= 30:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

        # SHAP
        shap_values = (
            self.explainer.shap_values(X)
        )

        reasons = self._build_reasons(
            X,
            shap_values,
            context,
        )

        return {
            "transaction_risk": round(
                transaction_risk,
                2,
            ),
            "fraud_probability": round(
                probability,
                6,
            ),
            "risk_level": risk_level,
            "reasons": reasons,
            "recipient_context": {
                "previous_transaction_count": (
                    int(
                        context[
                            "previous_recipient_count"
                        ]
                    )
                ),
                "new_recipient": (
                    context[
                        "new_recipient"
                    ]
                ),
                "amount_vs_recipient_history": (
                    round(
                        context[
                            "amount_vs_recipient_history"
                        ],
                        3,
                    )
                ),
            },
            "features": X.to_dict(
                orient="records"
            )[0],
        }


# -------------------------------------------------------------
# Local smoke test
# -------------------------------------------------------------

if __name__ == "__main__":

    engine = TransactionModel()

    test_transaction = {
        "step": 100,
        "type": "TRANSFER",
        "amount": 5000.0,
        "nameDest": "C123456789",
    }

    result = engine.score_transaction(
        test_transaction,
        update_history=True,
    )

    print("\nTransaction test result:")
    print(json.dumps(result, indent=2))
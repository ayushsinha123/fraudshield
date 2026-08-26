from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from backend.app.services.transaction_model import TransactionModel


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_shap_contributions(
    engine: TransactionModel,
    transaction: dict,
) -> tuple[float, pd.DataFrame, dict]:
    """
    Rebuild the exact production features and inspect
    the raw SHAP contribution of every feature.
    """

    X, context = engine._build_features(
        transaction,
        update_history=False,
    )

    probability = float(
        engine.model.predict_proba(X)[0, 1]
    )

    shap_values = engine.explainer.shap_values(X)

    values = np.asarray(shap_values)

    if values.ndim == 2:
        values = values[0]

    contributions = pd.DataFrame(
        {
            "feature": engine.FEATURE_COLUMNS,
            "value": X.iloc[0].values,
            "shap": values,
        }
    )

    contributions["abs_shap"] = (
        contributions["shap"].abs()
    )

    contributions = contributions.sort_values(
        "abs_shap",
        ascending=False,
    ).reset_index(drop=True)

    return probability, contributions, context


def run_case(
    name: str,
    transaction: dict,
) -> None:

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    # Fresh model for every case so recipient history
    # from one test cannot contaminate another.
    engine = TransactionModel()

    result = engine.score_transaction(
        transaction,
        update_history=False,
    )

    probability, contributions, context = (
        get_shap_contributions(
            engine,
            transaction,
        )
    )

    print("\nInput:")
    print(transaction)

    print("\nModel output:")
    print(f"Transaction risk : {result['transaction_risk']}")
    print(f"Fraud probability: {probability:.6f}")
    print(f"Risk level       : {result['risk_level']}")

    print("\nRecipient context:")
    print(context)

    print("\nTop SHAP contributions:")
    print(
        contributions[
            [
                "feature",
                "value",
                "shap",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nGenerated reasons:")
    for reason in result["reasons"]:
        print(f"- {reason}")


def main() -> None:

    # ---------------------------------------------------------
    # CASE 1
    # ₹500 PAYMENT, new recipient
    # ---------------------------------------------------------

    run_case(
        "CASE 1 — ₹500 PAYMENT / NEW RECIPIENT",
        {
            "step": 12,
            "type": "PAYMENT",
            "amount": 500,
            "nameDest": "TEST_RECIPIENT_1",
        },
    )

    # ---------------------------------------------------------
    # CASE 2
    # ₹5000 PAYMENT, new recipient
    # ---------------------------------------------------------

    run_case(
        "CASE 2 — ₹5000 PAYMENT / NEW RECIPIENT",
        {
            "step": 12,
            "type": "PAYMENT",
            "amount": 5000,
            "nameDest": "TEST_RECIPIENT_2",
        },
    )

    # ---------------------------------------------------------
    # CASE 3
    # ₹5000 TRANSFER, new recipient
    # ---------------------------------------------------------

    run_case(
        "CASE 3 — ₹5000 TRANSFER / NEW RECIPIENT",
        {
            "step": 12,
            "type": "TRANSFER",
            "amount": 5000,
            "nameDest": "TEST_RECIPIENT_3",
        },
    )

    # ---------------------------------------------------------
    # CASE 4
    # ₹500 TRANSFER, new recipient
    # ---------------------------------------------------------

    run_case(
        "CASE 4 — ₹500 TRANSFER / NEW RECIPIENT",
        {
            "step": 12,
            "type": "TRANSFER",
            "amount": 500,
            "nameDest": "TEST_RECIPIENT_4",
        },
    )

    # ---------------------------------------------------------
    # CASE 5
    # ₹5000 TRANSFER, KNOWN recipient
    #
    # First transaction establishes history.
    # Second transaction is the actual test.
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("CASE 5 — ₹5000 TRANSFER / KNOWN RECIPIENT")
    print("=" * 80)

    engine = TransactionModel()

    known_recipient = "KNOWN_RECIPIENT_1"

    # Establish prior history.
    engine.score_transaction(
        {
            "step": 10,
            "type": "PAYMENT",
            "amount": 500,
            "nameDest": known_recipient,
        },
        update_history=True,
    )

    transaction = {
        "step": 12,
        "type": "TRANSFER",
        "amount": 5000,
        "nameDest": known_recipient,
    }

    result = engine.score_transaction(
        transaction,
        update_history=False,
    )

    probability, contributions, context = (
        get_shap_contributions(
            engine,
            transaction,
        )
    )

    print("\nInput:")
    print(transaction)

    print("\nModel output:")
    print(f"Transaction risk : {result['transaction_risk']}")
    print(f"Fraud probability: {probability:.6f}")
    print(f"Risk level       : {result['risk_level']}")

    print("\nRecipient context:")
    print(context)

    print("\nTop SHAP contributions:")
    print(
        contributions[
            [
                "feature",
                "value",
                "shap",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nGenerated reasons:")
    for reason in result["reasons"]:
        print(f"- {reason}")


if __name__ == "__main__":
    main()
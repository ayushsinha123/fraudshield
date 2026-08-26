from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)

from ml.transaction.train import (
    add_causal_recipient_history,
    chronological_split,
    compute_training_statistics,
    create_features,
    prepare_dataset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "paysim"
    / "PS_20174392719_1491204439457_log.csv"
)

ARTIFACT_PATH = (
    PROJECT_ROOT
    / "models"
    / "transaction"
    / "transaction_model.joblib"
)

CALIBRATOR_PATH = (
    PROJECT_ROOT
    / "models"
    / "transaction"
    / "transaction_platt_calibrator.joblib"
)


def logit(
    probabilities: np.ndarray,
) -> np.ndarray:
    """
    Convert probabilities to log-odds.

    Clipping prevents log(0) and log(infinity).
    """
    probabilities = np.clip(
        probabilities,
        1e-7,
        1.0 - 1e-7,
    )

    return np.log(
        probabilities
        / (1.0 - probabilities)
    )


def evaluate_calibration(
    name: str,
    calibrated_probability: np.ndarray,
    y_test: pd.Series,
    raw_probability: np.ndarray,
) -> None:

    y = y_test.to_numpy()

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    print(
        f"Raw Brier score        : "
        f"{brier_score_loss(y, raw_probability):.6f}"
    )

    print(
        f"Calibrated Brier score : "
        f"{brier_score_loss(y, calibrated_probability):.6f}"
    )

    print(
        f"Raw mean probability   : "
        f"{raw_probability.mean():.6f}"
    )

    print(
        f"Calibrated mean        : "
        f"{calibrated_probability.mean():.6f}"
    )

    print(
        f"Raw max probability    : "
        f"{raw_probability.max():.6f}"
    )

    print(
        f"Calibrated max         : "
        f"{calibrated_probability.max():.6f}"
    )

    print(
        f"Calibrated PR-AUC      : "
        f"{average_precision_score(y, calibrated_probability):.6f}"
    )

    print(
        f"Calibrated ROC-AUC     : "
        f"{roc_auc_score(y, calibrated_probability):.6f}"
    )


def apply_platt_calibrator(
    calibrator: LogisticRegression,
    probability: float,
) -> float:

    probability_array = np.array(
        [probability],
        dtype=float,
    )

    calibrated = calibrator.predict_proba(
        logit(probability_array).reshape(-1, 1)
    )[0, 1]

    return float(
        np.clip(
            calibrated,
            0.0,
            1.0,
        )
    )


def build_case_features(
    case: dict,
    type_stats: pd.DataFrame,
    global_stats: dict[str, float],
):
    """
    Build a single controlled test case using the
    same feature-generation logic as the production
    transaction pipeline.

    Recipient-history fields are supplied explicitly
    so controlled cases remain deterministic.
    """

    amount = float(
        case["amount"]
    )

    previous_count = float(
        case.get(
            "dest_prev_tx_count",
            0.0,
        )
    )

    previous_mean = float(
        case.get(
            "dest_prev_mean_amount",
            global_stats["median"],
        )
    )

    amount_vs_recipient_history = (
        amount
        / (previous_mean + 1.0)
    )

    row = pd.DataFrame(
        [
            {
                "step": int(case["step"]),
                "type": str(case["type"]),
                "amount": amount,
                "nameDest": str(
                    case["nameDest"]
                ),
                "dest_prev_tx_count": previous_count,
                "dest_prev_amount_sum": (
                    previous_count
                    * previous_mean
                ),
                "dest_prev_mean_amount": previous_mean,
                "amount_vs_dest_history": (
                    amount_vs_recipient_history
                ),
                "new_recipient": int(
                    case.get(
                        "new_recipient",
                        1,
                    )
                ),
                "isFraud": 0,
            }
        ]
    )

    X, _ = create_features(
        row,
        type_stats,
        global_stats,
    )

    context = {
        "new_recipient": bool(
            case.get(
                "new_recipient",
                1,
            )
        ),
        "previous_recipient_count": (
            previous_count
        ),
        "amount_vs_recipient_history": (
            amount_vs_recipient_history
        ),
    }

    return X, context


def analyze_controlled_cases(
    name: str,
    calibrator: LogisticRegression,
    cases: list[dict],
    model,
    type_stats: pd.DataFrame,
    global_stats: dict[str, float],
) -> None:

    print("\n" + "=" * 80)
    print(f"{name} — CONTROLLED CASES")
    print("=" * 80)

    for case in cases:

        X, context = build_case_features(
            case,
            type_stats,
            global_stats,
        )

        raw_probability = float(
            model.predict_proba(X)[0, 1]
        )

        calibrated_probability = (
            apply_platt_calibrator(
                calibrator,
                raw_probability,
            )
        )

        print("\n" + "-" * 70)
        print(case["name"])
        print("-" * 70)

        print(
            f"Type                  : "
            f"{case['type']}"
        )

        print(
            f"Amount                : "
            f"₹{case['amount']:.2f}"
        )

        print(
            f"Raw probability       : "
            f"{raw_probability:.6f}"
        )

        print(
            f"Raw transaction risk  : "
            f"{raw_probability * 100:.2f}"
        )

        print(
            f"Calibrated probability: "
            f"{calibrated_probability:.6f}"
        )

        print(
            f"Calibrated risk       : "
            f"{calibrated_probability * 100:.2f}"
        )

        print(
            f"New recipient         : "
            f"{context['new_recipient']}"
        )

        print(
            f"Previous recipient tx: "
            f"{context['previous_recipient_count']:.0f}"
        )

        print(
            f"Amount vs recipient history: "
            f"{context['amount_vs_recipient_history']:.3f}"
        )


def main() -> None:

    print("=" * 80)
    print("FRAUDSHIELD — TRANSACTION RISK CALIBRATION EXPERIMENT")
    print("=" * 80)

    # ---------------------------------------------------------
    # Validate paths
    # ---------------------------------------------------------

    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Transaction model artifact not found:\n"
            f"{ARTIFACT_PATH}"
        )

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"PaySim dataset not found:\n"
            f"{DATA_PATH}"
        )

    # ---------------------------------------------------------
    # Load existing production model
    # ---------------------------------------------------------

    artifact = joblib.load(
        ARTIFACT_PATH
    )

    model = artifact["model"]

    print(
        f"\nLoaded model:\n{ARTIFACT_PATH}"
    )

    # ---------------------------------------------------------
    # Load and prepare PaySim
    # ---------------------------------------------------------

    df = pd.read_csv(
        DATA_PATH
    )

    print(
        f"\nRaw shape: {df.shape}"
    )

    df = prepare_dataset(
        df
    )

    # ---------------------------------------------------------
    # Chronological split
    # ---------------------------------------------------------

    (
        train_df,
        val_df,
        test_df,
    ) = chronological_split(
        df
    )

    print("\nChronological split:")

    print(
        f"Train      : {train_df.shape}"
    )

    print(
        f"Validation : {val_df.shape}"
    )

    print(
        f"Test       : {test_df.shape}"
    )

    # ---------------------------------------------------------
    # Training-only statistics
    # ---------------------------------------------------------

    (
        type_stats,
        global_stats,
    ) = compute_training_statistics(
        train_df
    )

    # ---------------------------------------------------------
    # Causal recipient history
    # ---------------------------------------------------------

    (
        train_hist,
        val_hist,
        test_hist,
    ) = add_causal_recipient_history(
        train_df,
        val_df,
        test_df,
        global_stats,
    )

    # ---------------------------------------------------------
    # Exact production feature generation
    # ---------------------------------------------------------

    (
        X_train,
        y_train,
    ) = create_features(
        train_hist,
        type_stats,
        global_stats,
    )

    (
        X_val,
        y_val,
    ) = create_features(
        val_hist,
        type_stats,
        global_stats,
    )

    (
        X_test,
        y_test,
    ) = create_features(
        test_hist,
        type_stats,
        global_stats,
    )

    # ---------------------------------------------------------
    # Verify artifact schema
    # ---------------------------------------------------------

    artifact_features = artifact[
        "features"
    ]

    if list(X_test.columns) != list(
        artifact_features
    ):
        raise ValueError(
            "Feature schema mismatch between "
            "training pipeline and production artifact."
        )

    print(
        "\nFeature schema verification: PASSED"
    )

    # ---------------------------------------------------------
    # Generate raw probabilities
    # ---------------------------------------------------------

    val_probability = (
        model.predict_proba(
            X_val
        )[:, 1]
    )

    test_probability = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    print(
        "\nRaw model probabilities generated."
    )

    # ---------------------------------------------------------
    # Train Platt calibrator
    # ---------------------------------------------------------

    print(
        "\nTraining Platt calibrator..."
    )

    platt = LogisticRegression(
        random_state=42,
        max_iter=1000,
    )

    platt.fit(
        logit(
            val_probability
        ).reshape(-1, 1),
        y_val,
    )

    print(
        "Platt calibrator trained successfully."
    )

    # ---------------------------------------------------------
    # Save calibrator
    # ---------------------------------------------------------

    CALIBRATOR_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        platt,
        CALIBRATOR_PATH,
    )

    print(
        f"\nPlatt calibrator saved to:\n"
        f"{CALIBRATOR_PATH}"
    )

    # ---------------------------------------------------------
    # Apply Platt calibration to test set
    # ---------------------------------------------------------

    platt_test_probability = (
        platt.predict_proba(
            logit(
                test_probability
            ).reshape(-1, 1)
        )[:, 1]
    )

    evaluate_calibration(
        "CALIBRATION — PLATT SCALING",
        platt_test_probability,
        y_test,
        test_probability,
    )

    # ---------------------------------------------------------
    # Isotonic experiment for comparison only
    # ---------------------------------------------------------

    print(
        "\nTraining isotonic calibrator "
        "for comparison only..."
    )

    isotonic = IsotonicRegression(
        y_min=0.0,
        y_max=1.0,
        out_of_bounds="clip",
    )

    isotonic.fit(
        val_probability,
        y_val,
    )

    isotonic_test_probability = (
        isotonic.predict(
            test_probability
        )
    )

    evaluate_calibration(
        "CALIBRATION — ISOTONIC COMPARISON",
        isotonic_test_probability,
        y_test,
        test_probability,
    )

    # ---------------------------------------------------------
    # Controlled cases
    # ---------------------------------------------------------

    cases = [
        {
            "name": "₹500 PAYMENT / NEW RECIPIENT",
            "step": 12,
            "type": "PAYMENT",
            "amount": 500.0,
            "nameDest": "CALIBRATION_RECIPIENT_1",
            "new_recipient": 1,
            "dest_prev_tx_count": 0,
            "dest_prev_mean_amount": (
                global_stats["median"]
            ),
        },
        {
            "name": "₹5000 PAYMENT / NEW RECIPIENT",
            "step": 12,
            "type": "PAYMENT",
            "amount": 5000.0,
            "nameDest": "CALIBRATION_RECIPIENT_2",
            "new_recipient": 1,
            "dest_prev_tx_count": 0,
            "dest_prev_mean_amount": (
                global_stats["median"]
            ),
        },
        {
            "name": "₹500 TRANSFER / NEW RECIPIENT",
            "step": 12,
            "type": "TRANSFER",
            "amount": 500.0,
            "nameDest": "CALIBRATION_RECIPIENT_3",
            "new_recipient": 1,
            "dest_prev_tx_count": 0,
            "dest_prev_mean_amount": (
                global_stats["median"]
            ),
        },
        {
            "name": "₹5000 TRANSFER / NEW RECIPIENT",
            "step": 12,
            "type": "TRANSFER",
            "amount": 5000.0,
            "nameDest": "CALIBRATION_RECIPIENT_4",
            "new_recipient": 1,
            "dest_prev_tx_count": 0,
            "dest_prev_mean_amount": (
                global_stats["median"]
            ),
        },
    ]

    analyze_controlled_cases(
        "PLATT CALIBRATION",
        platt,
        cases,
        model,
        type_stats,
        global_stats,
    )

    # ---------------------------------------------------------
    # Final status
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("CALIBRATION EXPERIMENT COMPLETE")
    print("=" * 80)

    print(
        "\nProduction transaction model artifact:"
    )

    print(
        ARTIFACT_PATH
    )

    print(
        "\nProduction artifact was NOT modified."
    )

    print(
        "Only the separate Platt calibrator was saved:"
    )

    print(
        CALIBRATOR_PATH
    )


if __name__ == "__main__":
    main()
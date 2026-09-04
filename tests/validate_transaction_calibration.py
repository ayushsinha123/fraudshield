from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
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

MODEL_PATH = (
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


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def apply_platt(
    calibrator,
    raw_probability: np.ndarray,
) -> np.ndarray:

    raw_probability = np.clip(
        raw_probability,
        1e-7,
        1.0 - 1e-7,
    )

    logit_probability = np.log(
        raw_probability
        / (1.0 - raw_probability)
    )

    calibrated = calibrator.predict_proba(
        logit_probability.reshape(-1, 1)
    )[:, 1]

    return np.clip(
        calibrated,
        0.0,
        1.0,
    )


def risk_band(
    risk: np.ndarray,
) -> np.ndarray:

    return np.select(
        [
            risk >= 80,
            risk >= 60,
            risk >= 30,
        ],
        [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
        ],
        default="LOW",
    )


def print_binary_metrics(
    name: str,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> None:

    predictions = (
        probabilities >= threshold
    ).astype(int)

    precision = precision_score(
        y_true,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        predictions,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1],
    ).ravel()

    print(f"\n{name}")
    print("-" * 60)
    print(
        f"Threshold            : {threshold:.2f}"
    )
    print(
        f"Precision            : {precision:.6f}"
    )
    print(
        f"Recall               : {recall:.6f}"
    )
    print(
        f"F1                   : {f1:.6f}"
    )
    print(
        f"True negatives       : {tn:,}"
    )
    print(
        f"False positives      : {fp:,}"
    )
    print(
        f"False negatives      : {fn:,}"
    )
    print(
        f"True positives       : {tp:,}"
    )

    legitimate = y_true == 0
    fraud = y_true == 1

    legitimate_flagged = (
        predictions[legitimate] == 1
    ).sum()

    fraud_captured = (
        predictions[fraud] == 1
    ).sum()

    legitimate_count = legitimate.sum()
    fraud_count = fraud.sum()

    print(
        f"Legitimate flagged  : "
        f"{legitimate_flagged:,} / {legitimate_count:,} "
        f"({legitimate_flagged / legitimate_count * 100:.4f}%)"
    )

    print(
        f"Fraud captured      : "
        f"{fraud_captured:,} / {fraud_count:,} "
        f"({fraud_captured / fraud_count * 100:.4f}%)"
    )


def probability_summary(
    name: str,
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> None:

    legitimate = probabilities[
        y_true == 0
    ]

    fraud = probabilities[
        y_true == 1
    ]

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    print("\nLEGITIMATE TRANSACTIONS")
    print(
        f"Count    : {len(legitimate):,}"
    )
    print(
        f"Mean     : {legitimate.mean():.6f}"
    )
    print(
        f"Median   : {np.median(legitimate):.6f}"
    )
    print(
        f"P90      : {np.percentile(legitimate, 90):.6f}"
    )
    print(
        f"P95      : {np.percentile(legitimate, 95):.6f}"
    )
    print(
        f"P99      : {np.percentile(legitimate, 99):.6f}"
    )
    print(
        f"Max      : {legitimate.max():.6f}"
    )

    print("\nFRAUDULENT TRANSACTIONS")
    print(
        f"Count    : {len(fraud):,}"
    )
    print(
        f"Mean     : {fraud.mean():.6f}"
    )
    print(
        f"Median   : {np.median(fraud):.6f}"
    )
    print(
        f"P10      : {np.percentile(fraud, 10):.6f}"
    )
    print(
        f"P25      : {np.percentile(fraud, 25):.6f}"
    )
    print(
        f"P50      : {np.percentile(fraud, 50):.6f}"
    )
    print(
        f"P75      : {np.percentile(fraud, 75):.6f}"
    )
    print(
        f"P90      : {np.percentile(fraud, 90):.6f}"
    )
    print(
        f"Max      : {fraud.max():.6f}"
    )


def band_distribution(
    name: str,
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> pd.DataFrame:

    risk_scores = probabilities * 100.0

    bands = risk_band(
        risk_scores
    )

    frame = pd.DataFrame(
        {
            "label": y_true,
            "risk_score": risk_scores,
            "band": bands,
        }
    )

    summary = (
        frame.groupby(
            "band",
            sort=False,
        )
        .agg(
            transactions=(
                "label",
                "count",
            ),
            fraud_count=(
                "label",
                "sum",
            ),
        )
    )

    summary["legitimate_count"] = (
        summary["transactions"]
        - summary["fraud_count"]
    )

    summary["fraud_rate_%"] = (
        summary["fraud_count"]
        / summary["transactions"]
        * 100
    )

    band_order = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]

    summary = (
        summary
        .reindex(band_order)
        .fillna(0)
    )

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    print(
        summary.to_string(
            float_format=lambda x: f"{x:.6f}"
        )
    )

    return summary


def decile_calibration_table(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> pd.DataFrame:

    frame = pd.DataFrame(
        {
            "actual": y_true,
            "probability": probabilities,
        }
    )

    # qcut can produce fewer than 10 bins when
    # many predictions are tied.
    frame["decile"] = pd.qcut(
        frame["probability"],
        q=10,
        labels=False,
        duplicates="drop",
    )

    table = (
        frame.groupby(
            "decile",
            observed=True,
        )
        .agg(
            count=(
                "actual",
                "count",
            ),
            mean_predicted_probability=(
                "probability",
                "mean",
            ),
            observed_fraud_rate=(
                "actual",
                "mean",
            ),
        )
        .reset_index()
    )

    table["observed_fraud_rate_%"] = (
        table["observed_fraud_rate"] * 100
    )

    table["mean_predicted_probability_%"] = (
        table[
            "mean_predicted_probability"
        ] * 100
    )

    return table[
        [
            "decile",
            "count",
            "mean_predicted_probability_%",
            "observed_fraud_rate_%",
        ]
    ]


def threshold_table(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> pd.DataFrame:

    rows = []

    legitimate = y_true == 0
    fraud = y_true == 1

    for score_threshold in [
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        80,
        90,
    ]:

        prediction = (
            probabilities * 100
            >= score_threshold
        )

        legitimate_flag_rate = (
            prediction[legitimate].mean()
            * 100
        )

        fraud_capture_rate = (
            prediction[fraud].mean()
            * 100
        )

        precision = precision_score(
            y_true,
            prediction.astype(int),
            zero_division=0,
        )

        rows.append(
            {
                "risk_threshold": score_threshold,
                "legitimate_flag_rate_%": (
                    legitimate_flag_rate
                ),
                "fraud_capture_rate_%": (
                    fraud_capture_rate
                ),
                "precision": precision,
            }
        )

    return pd.DataFrame(rows)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> None:

    print("=" * 80)
    print(
        "FRAUDSHIELD — FULL TRANSACTION CALIBRATION VALIDATION"
    )
    print("=" * 80)

    # --------------------------------------------------------
    # Validate files
    # --------------------------------------------------------

    for path in [
        DATA_PATH,
        MODEL_PATH,
        CALIBRATOR_PATH,
    ]:

        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{path}"
            )

    # --------------------------------------------------------
    # Load artifacts
    # --------------------------------------------------------

    print("\nLoading transaction model...")

    artifact = joblib.load(
        MODEL_PATH
    )

    model = artifact["model"]

    print(
        "Loading Platt calibrator..."
    )

    calibrator = joblib.load(
        CALIBRATOR_PATH
    )

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    print(
        "\nLoading PaySim..."
    )

    df = pd.read_csv(
        DATA_PATH
    )

    print(
        f"Raw dataset shape: {df.shape}"
    )

    df = prepare_dataset(
        df
    )

    # --------------------------------------------------------
    # Chronological split
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Training-only statistics
    # --------------------------------------------------------

    (
        type_stats,
        global_stats,
    ) = compute_training_statistics(
        train_df
    )

    # --------------------------------------------------------
    # Causal recipient history
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Build exact production features
    # --------------------------------------------------------

    X_test, y_test = create_features(
        test_hist,
        type_stats,
        global_stats,
    )

    artifact_features = artifact[
        "features"
    ]

    if list(X_test.columns) != list(
        artifact_features
    ):
        raise ValueError(
            "Feature schema mismatch."
        )

    y = y_test.to_numpy()

    # --------------------------------------------------------
    # Raw and calibrated predictions
    # --------------------------------------------------------

    print(
        "\nGenerating raw probabilities..."
    )

    raw_probability = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    print(
        "Applying Platt calibration..."
    )

    calibrated_probability = apply_platt(
        calibrator,
        raw_probability,
    )

    # --------------------------------------------------------
    # Core metrics
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("PROBABILITY QUALITY")
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
        f"Raw PR-AUC             : "
        f"{average_precision_score(y, raw_probability):.6f}"
    )

    print(
        f"Calibrated PR-AUC      : "
        f"{average_precision_score(y, calibrated_probability):.6f}"
    )

    print(
        f"Raw ROC-AUC            : "
        f"{roc_auc_score(y, raw_probability):.6f}"
    )

    print(
        f"Calibrated ROC-AUC     : "
        f"{roc_auc_score(y, calibrated_probability):.6f}"
    )

    # --------------------------------------------------------
    # Distribution comparison
    # --------------------------------------------------------

    probability_summary(
        "RAW PROBABILITY DISTRIBUTION",
        y,
        raw_probability,
    )

    probability_summary(
        "CALIBRATED PROBABILITY DISTRIBUTION",
        y,
        calibrated_probability,
    )

    # --------------------------------------------------------
    # Existing risk bands
    # --------------------------------------------------------

    raw_bands = band_distribution(
        "RAW MODEL — EXISTING RISK BANDS",
        y,
        raw_probability,
    )

    calibrated_bands = band_distribution(
        "CALIBRATED MODEL — EXISTING RISK BANDS",
        y,
        calibrated_probability,
    )

    # --------------------------------------------------------
    # Threshold analysis
    # --------------------------------------------------------

    threshold_results = threshold_table(
        y,
        calibrated_probability,
    )

    print("\n" + "=" * 80)
    print(
        "CALIBRATED RISK THRESHOLD ANALYSIS"
    )
    print("=" * 80)

    print(
        threshold_results.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    # --------------------------------------------------------
    # Explicit existing bands
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print(
        "EXISTING 30 / 60 / 80 THRESHOLD PERFORMANCE"
    )
    print("=" * 80)

    for threshold in [
        30,
        60,
        80,
    ]:

        print_binary_metrics(
            f"CALIBRATED RISK >= {threshold}",
            y,
            calibrated_probability,
            threshold / 100.0,
        )

    # --------------------------------------------------------
    # Decile calibration
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print(
        "CALIBRATED DECILE RELIABILITY TABLE"
    )
    print("=" * 80)

    deciles = decile_calibration_table(
        y,
        calibrated_probability,
    )

    print(
        deciles.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    # --------------------------------------------------------
    # Fraud / legitimate separation
    # --------------------------------------------------------

    legitimate = (
        calibrated_probability[y == 0]
    )

    fraud = (
        calibrated_probability[y == 1]
    )

    print("\n" + "=" * 80)
    print(
        "FRAUD VS LEGITIMATE SEPARATION"
    )
    print("=" * 80)

    print(
        f"Legitimate mean      : "
        f"{legitimate.mean():.6f}"
    )

    print(
        f"Fraud mean           : "
        f"{fraud.mean():.6f}"
    )

    print(
        f"Legitimate median    : "
        f"{np.median(legitimate):.6f}"
    )

    print(
        f"Fraud median         : "
        f"{np.median(fraud):.6f}"
    )

    print(
        f"Legitimate P95       : "
        f"{np.percentile(legitimate, 95):.6f}"
    )

    print(
        f"Fraud P10            : "
        f"{np.percentile(fraud, 10):.6f}"
    )

    # --------------------------------------------------------
    # Decision guidance
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print(
        "THRESHOLD DECISION CHECK"
    )
    print("=" * 80)

    for threshold in [
        30,
        60,
        80,
    ]:

        flagged = (
            calibrated_probability
            >= threshold / 100.0
        )

        flagged_fraud_rate = (
            y[flagged].mean() * 100
            if flagged.any()
            else 0.0
        )

        legitimate_false_positive_rate = (
            flagged[y == 0].mean() * 100
        )

        fraud_capture_rate = (
            flagged[y == 1].mean() * 100
        )

        print(
            f"\nThreshold {threshold}:"
        )

        print(
            f"  Precision among flagged : "
            f"{flagged_fraud_rate:.4f}%"
        )

        print(
            f"  Legitimate flagged      : "
            f"{legitimate_false_positive_rate:.4f}%"
        )

        print(
            f"  Fraud captured          : "
            f"{fraud_capture_rate:.4f}%"
        )

    print("\n" + "=" * 80)
    print(
        "CALIBRATION VALIDATION COMPLETE"
    )
    print("=" * 80)

    print(
        "\nNo model or calibrator artifact was modified."
    )


if __name__ == "__main__":
    main()
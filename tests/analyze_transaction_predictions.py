from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
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

ARTIFACT_PATH = (
    PROJECT_ROOT
    / "models"
    / "transaction"
    / "transaction_model.joblib"
)


def precision_at_top_percent(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    percent: float,
) -> float:
    k = max(
        1,
        int(np.ceil(len(y_true) * percent / 100)),
    )

    top_indices = np.argsort(
        probabilities
    )[::-1][:k]

    return float(
        y_true[top_indices].mean()
    )


def main() -> None:

    print("=" * 80)
    print("FRAUDSHIELD — TRANSACTION MODEL DIAGNOSTIC")
    print("=" * 80)

    # ---------------------------------------------------------
    # Load artifact
    # ---------------------------------------------------------

    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Artifact not found: {ARTIFACT_PATH}"
        )

    artifact = joblib.load(
        ARTIFACT_PATH
    )

    model = artifact["model"]

    print("\nArtifact:")
    print(ARTIFACT_PATH)

    print("\nFeature schema:")

    for feature in artifact["features"]:
        print(f"  - {feature}")

    # ---------------------------------------------------------
    # Load dataset
    # ---------------------------------------------------------

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    print(
        f"\nRaw dataset shape: {df.shape}"
    )

    # ---------------------------------------------------------
    # EXACT SAME PREPARATION AS train.py
    # ---------------------------------------------------------

    df = prepare_dataset(df)

    train_df, val_df, test_df = (
        chronological_split(df)
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
    # EXACT SAME TRAINING STATISTICS
    # ---------------------------------------------------------

    type_stats, global_stats = (
        compute_training_statistics(
            train_df
        )
    )

    # ---------------------------------------------------------
    # EXACT SAME CAUSAL RECIPIENT HISTORY
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
    # EXACT SAME FEATURE ENGINEERING
    # ---------------------------------------------------------

    X_train, y_train = create_features(
        train_hist,
        type_stats,
        global_stats,
    )

    X_val, y_val = create_features(
        val_hist,
        type_stats,
        global_stats,
    )

    X_test, y_test = create_features(
        test_hist,
        type_stats,
        global_stats,
    )

    print("\nFeature shapes:")

    print(
        f"Train      : {X_train.shape}"
    )

    print(
        f"Validation : {X_val.shape}"
    )

    print(
        f"Test       : {X_test.shape}"
    )

    # ---------------------------------------------------------
    # Verify artifact schema
    # ---------------------------------------------------------

    artifact_features = artifact["features"]

    if list(X_test.columns) != list(
        artifact_features
    ):
        raise ValueError(
            "Artifact feature schema does not "
            "match the current training pipeline."
        )

    print(
        "\nFeature schema verification: PASSED"
    )

    # ---------------------------------------------------------
    # Predictions
    # ---------------------------------------------------------

    probabilities = (
        model.predict_proba(X_test)[:, 1]
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    results = test_df[
        [
            "step",
            "type",
            "amount",
            "nameDest",
            "isFraud",
        ]
    ].copy()

    results["fraud_probability"] = (
        probabilities
    )

    results["prediction"] = (
        predictions
    )

    # ---------------------------------------------------------
    # Overall metrics
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("OVERALL TEST METRICS")
    print("=" * 80)

    print(
        f"PR-AUC   : "
        f"{average_precision_score(y_test, probabilities):.6f}"
    )

    print(
        f"ROC-AUC  : "
        f"{roc_auc_score(y_test, probabilities):.6f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y_test, predictions, zero_division=0):.6f}"
    )

    print(
        f"Recall   : "
        f"{recall_score(y_test, predictions, zero_division=0):.6f}"
    )

    print(
        f"F1       : "
        f"{f1_score(y_test, predictions, zero_division=0):.6f}"
    )

    print(
        "\nPrecision at top-ranked transactions:"
    )

    for percent in [
        0.1,
        0.5,
        1.0,
        2.0,
        5.0,
    ]:

        score = precision_at_top_percent(
            y_test.to_numpy(),
            probabilities,
            percent,
        )

        print(
            f"Top {percent}% : "
            f"{score:.6f}"
        )

    # ---------------------------------------------------------
    # Metrics by transaction type
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("TRANSACTION TYPE ANALYSIS")
    print("=" * 80)

    for transaction_type in sorted(
        results["type"].unique()
    ):

        subset = results[
            results["type"]
            == transaction_type
        ]

        y_type = subset[
            "isFraud"
        ].to_numpy()

        p_type = subset[
            "fraud_probability"
        ].to_numpy()

        pred_type = (
            p_type >= 0.5
        ).astype(int)

        print(
            f"\n--- {transaction_type} ---"
        )

        print(
            f"Transactions       : "
            f"{len(subset):,}"
        )

        print(
            f"Actual fraud       : "
            f"{int(subset['isFraud'].sum()):,}"
        )

        print(
            f"Actual fraud rate  : "
            f"{subset['isFraud'].mean() * 100:.6f}%"
        )

        print(
            f"Mean probability   : "
            f"{p_type.mean():.6f}"
        )

        print(
            f"Median probability : "
            f"{np.median(p_type):.6f}"
        )

        print(
            f"Max probability    : "
            f"{p_type.max():.6f}"
        )

        print(
            f"Predicted fraud    : "
            f"{int(pred_type.sum()):,}"
        )

        print(
            f"Predicted fraud %  : "
            f"{pred_type.mean() * 100:.6f}%"
        )

        print(
            f"Precision           : "
            f"{precision_score(y_type, pred_type, zero_division=0):.6f}"
        )

        print(
            f"Recall              : "
            f"{recall_score(y_type, pred_type, zero_division=0):.6f}"
        )

        print(
            f"F1                  : "
            f"{f1_score(y_type, pred_type, zero_division=0):.6f}"
        )

        if len(np.unique(y_type)) == 2:

            print(
                f"PR-AUC             : "
                f"{average_precision_score(y_type, p_type):.6f}"
            )

            print(
                f"ROC-AUC            : "
                f"{roc_auc_score(y_type, p_type):.6f}"
            )

    # ---------------------------------------------------------
    # Summary table
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("TYPE SUMMARY")
    print("=" * 80)

    summary = (
        results.groupby("type")
        .agg(
            transactions=(
                "isFraud",
                "count",
            ),
            fraud_count=(
                "isFraud",
                "sum",
            ),
            fraud_rate=(
                "isFraud",
                "mean",
            ),
            mean_probability=(
                "fraud_probability",
                "mean",
            ),
            median_probability=(
                "fraud_probability",
                "median",
            ),
            max_probability=(
                "fraud_probability",
                "max",
            ),
            predicted_fraud=(
                "prediction",
                "sum",
            ),
        )
        .sort_values(
            "mean_probability",
            ascending=False,
        )
    )

    summary["fraud_rate"] *= 100

    summary["predicted_fraud_rate"] = (
        summary["predicted_fraud"]
        / summary["transactions"]
        * 100
    )

    print(
        summary.to_string()
    )

    # ---------------------------------------------------------
    # Top 20 highest-risk transactions
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("TOP 20 HIGHEST-RISK TRANSACTIONS")
    print("=" * 80)

    top_20 = (
        results
        .sort_values(
            "fraud_probability",
            ascending=False,
        )
        .head(20)
    )

    print(
        top_20[
            [
                "step",
                "type",
                "amount",
                "isFraud",
                "fraud_probability",
            ]
        ].to_string(
            index=False
        )
    )

    print("\nDiagnostic complete.")


if __name__ == "__main__":
    main()
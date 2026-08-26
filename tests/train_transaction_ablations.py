from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ml.transaction.train import (
    add_causal_recipient_history,
    chronological_split,
    compute_training_statistics,
    create_features,
    prepare_dataset,
    train_model,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "paysim"
    / "PS_20174392719_1491204439457_log.csv"
)


# ============================================================
# Ablation definitions
# ============================================================

TYPE_FEATURES = [
    "type_CASH_IN",
    "type_CASH_OUT",
    "type_DEBIT",
    "type_PAYMENT",
    "type_TRANSFER",
]

TYPE_CONDITIONED_FEATURES = [
    "amount_vs_type_mean",
    "amount_vs_type_median",
]


# ============================================================
# Utility
# ============================================================

def precision_at_percent(
    y_true: pd.Series,
    scores: np.ndarray,
    percent: float,
) -> float:

    y_values = np.asarray(y_true)
    scores = np.asarray(scores)

    k = max(
        1,
        int(len(scores) * percent / 100),
    )

    top_indices = np.argsort(scores)[-k:]

    return float(
        y_values[top_indices].mean()
    )


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:

    probabilities = (
        model.predict_proba(X_test)[:, 1]
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    from sklearn.metrics import (
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    return {
        "pr_auc": float(
            average_precision_score(
                y_test,
                probabilities,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                y_test,
                probabilities,
            )
        ),
        "precision": float(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "top_0.5_precision": precision_at_percent(
            y_test,
            probabilities,
            0.5,
        ),
        "top_1.0_precision": precision_at_percent(
            y_test,
            probabilities,
            1.0,
        ),
    }


def analyze_by_type(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    test_df: pd.DataFrame,
    model_name: str,
) -> None:

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
            "isFraud",
        ]
    ].copy()

    results["fraud_probability"] = probabilities
    results["prediction"] = predictions

    print("\n")
    print("=" * 80)
    print(f"{model_name} — RESULTS BY TRANSACTION TYPE")
    print("=" * 80)

    summary_rows = []

    for transaction_type in sorted(
        results["type"].unique()
    ):

        subset = results[
            results["type"] == transaction_type
        ]

        y_type = subset["isFraud"].to_numpy()
        p_type = subset["fraud_probability"].to_numpy()
        pred_type = subset["prediction"].to_numpy()

        from sklearn.metrics import (
            average_precision_score,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )

        row = {
            "type": transaction_type,
            "transactions": len(subset),
            "actual_fraud": int(
                subset["isFraud"].sum()
            ),
            "actual_fraud_rate_%": (
                subset["isFraud"].mean() * 100
            ),
            "mean_probability": p_type.mean(),
            "median_probability": np.median(p_type),
            "max_probability": p_type.max(),
            "predicted_fraud": int(
                pred_type.sum()
            ),
            "predicted_fraud_rate_%": (
                pred_type.mean() * 100
            ),
            "precision": precision_score(
                y_type,
                pred_type,
                zero_division=0,
            ),
            "recall": recall_score(
                y_type,
                pred_type,
                zero_division=0,
            ),
            "f1": f1_score(
                y_type,
                pred_type,
                zero_division=0,
            ),
        }

        if len(np.unique(y_type)) == 2:
            row["pr_auc"] = (
                average_precision_score(
                    y_type,
                    p_type,
                )
            )
            row["roc_auc"] = (
                roc_auc_score(
                    y_type,
                    p_type,
                )
            )
        else:
            row["pr_auc"] = np.nan
            row["roc_auc"] = np.nan

        summary_rows.append(row)

    summary = pd.DataFrame(
        summary_rows
    ).set_index("type")

    print(
        summary.to_string(
            float_format=lambda x: f"{x:.6f}"
        )
    )


def print_overall_metrics(
    name: str,
    metrics: dict[str, float],
) -> None:

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    for key, value in metrics.items():
        print(
            f"{key:25s}: {value:.6f}"
        )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 80)
    print("FRAUDSHIELD — TRANSACTION ABLATION EXPERIMENT")
    print("=" * 80)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"PaySim dataset not found:\n{DATA_PATH}"
        )

    # --------------------------------------------------------
    # Load + prepare
    # --------------------------------------------------------

    print("\nLoading PaySim...")

    df = pd.read_csv(DATA_PATH)

    print(
        f"Raw shape: {df.shape}"
    )

    df = prepare_dataset(df)

    print(
        f"Prepared shape: {df.shape}"
    )

    # --------------------------------------------------------
    # Chronological split
    # --------------------------------------------------------

    (
        train_df,
        val_df,
        test_df,
    ) = chronological_split(df)

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
    # Training statistics
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
    # Exact original feature generation
    # --------------------------------------------------------

    (
        X_train_full,
        y_train,
    ) = create_features(
        train_hist,
        type_stats,
        global_stats,
    )

    (
        X_val_full,
        y_val,
    ) = create_features(
        val_hist,
        type_stats,
        global_stats,
    )

    (
        X_test_full,
        y_test,
    ) = create_features(
        test_hist,
        type_stats,
        global_stats,
    )

    print(
        "\nOriginal feature count:",
        X_train_full.shape[1],
    )

    # ========================================================
    # MODEL A
    # Remove transaction-type one-hot features only
    # ========================================================

    print("\n")
    print("=" * 80)
    print("MODEL A")
    print("Remove transaction-type one-hot features")
    print("=" * 80)

    model_a_features = [
        feature
        for feature in X_train_full.columns
        if feature not in TYPE_FEATURES
    ]

    X_train_a = X_train_full[
        model_a_features
    ].copy()

    X_val_a = X_val_full[
        model_a_features
    ].copy()

    X_test_a = X_test_full[
        model_a_features
    ].copy()

    print(
        f"Feature count: {len(model_a_features)}"
    )

    print("Removed:")

    for feature in TYPE_FEATURES:
        print(
            f"  - {feature}"
        )

    print("\nTraining Model A...")

    model_a = train_model(
        X_train_a,
        y_train,
        X_val_a,
        y_val,
    )

    metrics_a = evaluate_model(
        model_a,
        X_test_a,
        y_test,
    )

    print_overall_metrics(
        "MODEL A — OVERALL METRICS",
        metrics_a,
    )

    analyze_by_type(
        model_a,
        X_test_a,
        y_test,
        test_df,
        "MODEL A",
    )

    # ========================================================
    # MODEL B
    # Remove type one-hot + type-conditioned amount features
    # ========================================================

    print("\n")
    print("=" * 80)
    print("MODEL B")
    print(
        "Remove transaction-type one-hot + "
        "type-conditioned amount features"
    )
    print("=" * 80)

    remove_model_b = (
        set(TYPE_FEATURES)
        | set(TYPE_CONDITIONED_FEATURES)
    )

    model_b_features = [
        feature
        for feature in X_train_full.columns
        if feature not in remove_model_b
    ]

    X_train_b = X_train_full[
        model_b_features
    ].copy()

    X_val_b = X_val_full[
        model_b_features
    ].copy()

    X_test_b = X_test_full[
        model_b_features
    ].copy()

    print(
        f"Feature count: {len(model_b_features)}"
    )

    print("Removed:")

    for feature in sorted(
        remove_model_b
    ):
        print(
            f"  - {feature}"
        )

    print("\nTraining Model B...")

    model_b = train_model(
        X_train_b,
        y_train,
        X_val_b,
        y_val,
    )

    metrics_b = evaluate_model(
        model_b,
        X_test_b,
        y_test,
    )

    print_overall_metrics(
        "MODEL B — OVERALL METRICS",
        metrics_b,
    )

    analyze_by_type(
        model_b,
        X_test_b,
        y_test,
        test_df,
        "MODEL B",
    )

    # ========================================================
    # Direct comparison
    # ========================================================

    print("\n")
    print("=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)

    comparison = pd.DataFrame(
        {
            "Current_21_feature": {
                "PR-AUC": 0.639812,
                "ROC-AUC": 0.966669,
                "Precision": 0.044148,
                "Recall": 0.981629,
                "F1": 0.084496,
                "Top_0.5_Precision": 0.926339,
                "Top_1.0_Precision": 0.700559,
            },
            "A_no_type_one_hot": {
                key: metrics_a[
                    key_name
                ]
                for key, key_name in {
                    "PR-AUC": "pr_auc",
                    "ROC-AUC": "roc_auc",
                    "Precision": "precision",
                    "Recall": "recall",
                    "F1": "f1",
                    "Top_0.5_Precision":
                        "top_0.5_precision",
                    "Top_1.0_Precision":
                        "top_1.0_precision",
                }.items()
            },
            "B_no_type_features": {
                key: metrics_b[
                    key_name
                ]
                for key, key_name in {
                    "PR-AUC": "pr_auc",
                    "ROC-AUC": "roc_auc",
                    "Precision": "precision",
                    "Recall": "recall",
                    "F1": "f1",
                    "Top_0.5_Precision":
                        "top_0.5_precision",
                    "Top_1.0_Precision":
                        "top_1.0_precision",
                }.items()
            },
        }
    )

    print(
        comparison.to_string(
            float_format=lambda x: f"{x:.6f}"
        )
    )

    print("\n")
    print("=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)

    print(
        "\nIMPORTANT:"
    )

    print(
        "The current production artifact was NOT modified."
    )


if __name__ == "__main__":
    main()
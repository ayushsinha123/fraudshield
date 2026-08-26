from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)
from xgboost import XGBClassifier


# ============================================================
# Configuration
# ============================================================

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

RANDOM_STATE = 42


# ============================================================
# Data loading
# ============================================================

def load_paysim(path: str | Path) -> pd.DataFrame:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"PaySim dataset not found: {path}"
        )

    df = pd.read_csv(path)

    required_columns = [
        "step",
        "type",
        "amount",
        "nameDest",
        "isFraud",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {missing}"
        )

    return df


# ============================================================
# Dataset preparation
# ============================================================

def prepare_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.copy()

    # Balance fields and direct IDs are not model inputs.
    # nameDest is retained temporarily because it is needed
    # to construct causal recipient-history features.
    drop_columns = [
        "oldbalanceOrg",
        "oldbalanceDest",
        "newbalanceOrig",
        "newbalanceDest",
        "nameOrig",
        "isFlaggedFraud",
    ]

    data = data.drop(
        columns=drop_columns,
        errors="ignore",
    )

    data = data.drop_duplicates()

    data = data.dropna(
        subset=[
            "step",
            "type",
            "amount",
            "nameDest",
            "isFraud",
        ]
    )

    data = (
        data
        .sort_values(
            "step",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    return data


# ============================================================
# Chronological split
# ============================================================

def chronological_split(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    unique_steps = np.sort(
        df["step"].unique()
    )

    n_steps = len(unique_steps)

    train_idx = int(n_steps * 0.70)
    val_idx = int(n_steps * 0.85)

    train_end = unique_steps[
        train_idx - 1
    ]

    val_end = unique_steps[
        val_idx - 1
    ]

    train_df = df[
        df["step"] <= train_end
    ].copy()

    val_df = df[
        (df["step"] > train_end)
        & (df["step"] <= val_end)
    ].copy()

    test_df = df[
        df["step"] > val_end
    ].copy()

    return (
        train_df,
        val_df,
        test_df,
    )


# ============================================================
# Training-only statistics
# ============================================================

def compute_training_statistics(
    train_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:

    type_stats = (
        train_df
        .groupby("type")["amount"]
        .agg(
            type_mean="mean",
            type_median="median",
        )
    )

    global_stats = {
        "mean": float(
            train_df["amount"].mean()
        ),
        "median": float(
            train_df["amount"].median()
        ),
        "std": float(
            train_df["amount"].std()
        ),
        "p95": float(
            train_df["amount"].quantile(0.95)
        ),
        "p99": float(
            train_df["amount"].quantile(0.99)
        ),
    }

    return (
        type_stats,
        global_stats,
    )


# ============================================================
# Causal recipient history
# ============================================================

def add_causal_recipient_history(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    global_stats: dict[str, float],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:

    combined = pd.concat(
        [
            train_df.assign(
                _split="train"
            ),
            val_df.assign(
                _split="validation"
            ),
            test_df.assign(
                _split="test"
            ),
        ],
        ignore_index=True,
    )

    combined["_row_order"] = np.arange(
        len(combined)
    )

    combined = (
        combined
        .sort_values(
            ["step", "_row_order"],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    recipient_count: dict[str, int] = {}
    recipient_amount_sum: dict[str, float] = {}

    history_count = np.zeros(
        len(combined),
        dtype=np.int64,
    )

    history_amount_sum = np.zeros(
        len(combined),
        dtype=np.float64,
    )

    i = 0

    while i < len(combined):

        current_step = combined.loc[
            i,
            "step",
        ]

        j = i

        while (
            j < len(combined)
            and combined.loc[j, "step"]
            == current_step
        ):
            j += 1

        # Read historical state before updating
        # it with the current step.
        for row_idx in range(i, j):

            recipient = str(
                combined.loc[
                    row_idx,
                    "nameDest",
                ]
            )

            history_count[row_idx] = (
                recipient_count.get(
                    recipient,
                    0,
                )
            )

            history_amount_sum[row_idx] = (
                recipient_amount_sum.get(
                    recipient,
                    0.0,
                )
            )

        # Update state only after all rows
        # from this step have been scored.
        for row_idx in range(i, j):

            recipient = str(
                combined.loc[
                    row_idx,
                    "nameDest",
                ]
            )

            amount = float(
                combined.loc[
                    row_idx,
                    "amount",
                ]
            )

            recipient_count[recipient] = (
                recipient_count.get(
                    recipient,
                    0,
                ) + 1
            )

            recipient_amount_sum[recipient] = (
                recipient_amount_sum.get(
                    recipient,
                    0.0,
                ) + amount
            )

        i = j

    combined[
        "dest_prev_tx_count"
    ] = history_count

    combined[
        "dest_prev_amount_sum"
    ] = history_amount_sum

    combined[
        "dest_prev_mean_amount"
    ] = (
        combined["dest_prev_amount_sum"]
        /
        combined[
            "dest_prev_tx_count"
        ].replace(0, np.nan)
    )

    combined[
        "dest_prev_mean_amount"
    ] = (
        combined[
            "dest_prev_mean_amount"
        ]
        .fillna(
            global_stats["median"]
        )
    )

    combined[
        "amount_vs_dest_history"
    ] = (
        combined["amount"]
        /
        (
            combined[
                "dest_prev_mean_amount"
            ]
            + 1.0
        )
    )

    combined[
        "new_recipient"
    ] = (
        (
            combined[
                "dest_prev_tx_count"
            ]
            == 0
        )
        .astype(int)
    )

    train_out = (
        combined[
            combined["_split"] == "train"
        ]
        .drop(
            columns=[
                "_split",
                "_row_order",
            ]
        )
        .copy()
    )

    val_out = (
        combined[
            combined["_split"] == "validation"
        ]
        .drop(
            columns=[
                "_split",
                "_row_order",
            ]
        )
        .copy()
    )

    test_out = (
        combined[
            combined["_split"] == "test"
        ]
        .drop(
            columns=[
                "_split",
                "_row_order",
            ]
        )
        .copy()
    )

    return (
        train_out,
        val_out,
        test_out,
    )


# ============================================================
# Feature engineering
# ============================================================

def create_features(
    dataframe: pd.DataFrame,
    type_stats: pd.DataFrame,
    global_stats: dict[str, float],
) -> tuple[pd.DataFrame, pd.Series]:

    data = dataframe.copy()

    # ----------------------------
    # Time
    # ----------------------------

    data["hour"] = (
        data["step"] % 24
    )

    data["day"] = (
        data["step"] // 24
    )

    data["hour_sin"] = np.sin(
        2 * np.pi * data["hour"] / 24
    )

    data["hour_cos"] = np.cos(
        2 * np.pi * data["hour"] / 24
    )

    # ----------------------------
    # Amount
    # ----------------------------

    data["log_amount"] = np.log1p(
        data["amount"]
    )

    data["type_mean_amount"] = (
        data["type"]
        .map(type_stats["type_mean"])
        .fillna(global_stats["mean"])
    )

    data["type_median_amount"] = (
        data["type"]
        .map(type_stats["type_median"])
        .fillna(global_stats["median"])
    )

    data["amount_vs_type_mean"] = (
        data["amount"]
        /
        (
            data["type_mean_amount"]
            + 1.0
        )
    )

    data["amount_vs_type_median"] = (
        data["amount"]
        /
        (
            data["type_median_amount"]
            + 1.0
        )
    )

    data["amount_vs_global_median"] = (
        data["amount"]
        /
        (
            global_stats["median"]
            + 1.0
        )
    )

    data["above_train_p95"] = (
        data["amount"]
        >= global_stats["p95"]
    ).astype(int)

    data["above_train_p99"] = (
        data["amount"]
        >= global_stats["p99"]
    ).astype(int)

    # ----------------------------
    # Recipient history
    # ----------------------------

    data[
        "log_dest_prev_tx_count"
    ] = np.log1p(
        data["dest_prev_tx_count"]
    )

    data[
        "amount_vs_dest_history"
    ] = (
        data["amount_vs_dest_history"]
        .fillna(1.0)
    )

    data[
        "new_recipient"
    ] = (
        data["new_recipient"]
        .fillna(1)
        .astype(int)
    )

    # ----------------------------
    # Transaction type
    # ----------------------------

    data = pd.get_dummies(
        data,
        columns=["type"],
        prefix="type",
        dtype=int,
    )

    for transaction_type in TRANSACTION_TYPES:

        column = (
            f"type_{transaction_type}"
        )

        if column not in data.columns:
            data[column] = 0

    X = data[
        FEATURE_COLUMNS
    ].copy()

    y = data[
        "isFraud"
    ].astype(int)

    return (
        X,
        y,
    )


# ============================================================
# Train model
# ============================================================

def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> XGBClassifier:

    scale_pos_weight = (
        y_train.value_counts()[0]
        /
        y_train.value_counts()[1]
    )

    model = XGBClassifier(
        n_estimators=1000,
        max_depth=6,
        learning_rate=0.05,
        min_child_weight=3,
        subsample=0.85,
        colsample_bytree=0.85,
        gamma=0,
        objective="binary:logistic",
        eval_metric="aucpr",
        scale_pos_weight=scale_pos_weight,
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        early_stopping_rounds=75,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[
            (X_val, y_val)
        ],
        verbose=50,
    )

    return model


# ============================================================
# Evaluation
# ============================================================

def precision_at_percent(
    y_true: pd.Series,
    scores: np.ndarray,
    percent: float,
) -> float:

    y_values = np.asarray(
        y_true
    )

    scores = np.asarray(
        scores
    )

    k = max(
        1,
        int(
            len(scores)
            * percent
            / 100
        ),
    )

    top_indices = np.argsort(
        scores
    )[-k:]

    return float(
        y_values[top_indices].mean()
    )


def evaluate_model(
    model: XGBClassifier,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:

    val_proba = (
        model
        .predict_proba(
            X_val
        )[:, 1]
    )

    test_proba = (
        model
        .predict_proba(
            X_test
        )[:, 1]
    )

    test_pred = (
        test_proba >= 0.5
    ).astype(int)

    metrics = {
        "validation_pr_auc":
            float(
                average_precision_score(
                    y_val,
                    val_proba,
                )
            ),

        "validation_roc_auc":
            float(
                roc_auc_score(
                    y_val,
                    val_proba,
                )
            ),

        "test_pr_auc":
            float(
                average_precision_score(
                    y_test,
                    test_proba,
                )
            ),

        "test_roc_auc":
            float(
                roc_auc_score(
                    y_test,
                    test_proba,
                )
            ),

        "test_precision":
            float(
                precision_score(
                    y_test,
                    test_pred,
                    zero_division=0,
                )
            ),

        "test_recall":
            float(
                recall_score(
                    y_test,
                    test_pred,
                    zero_division=0,
                )
            ),

        "test_f1":
            float(
                f1_score(
                    y_test,
                    test_pred,
                    zero_division=0,
                )
            ),

        "precision_at_top_0.1_percent":
            precision_at_percent(
                y_test,
                test_proba,
                0.1,
            ),

        "precision_at_top_0.5_percent":
            precision_at_percent(
                y_test,
                test_proba,
                0.5,
            ),

        "precision_at_top_1_percent":
            precision_at_percent(
                y_test,
                test_proba,
                1.0,
            ),

        "precision_at_top_2_percent":
            precision_at_percent(
                y_test,
                test_proba,
                2.0,
            ),
    }

    return metrics


# ============================================================
# Artifact
# ============================================================

def save_artifact(
    model: XGBClassifier,
    type_stats: pd.DataFrame,
    global_stats: dict[str, float],
    metrics: dict[str, float],
    output_path: str | Path,
) -> None:

    artifact = {
        "model": model,

        "model_type": "XGBoost",

        "model_role":
            "FraudShield production "
            "transaction-risk model",

        "dataset": "PaySim",

        "dataset_type":
            "synthetic mobile-money simulation",

        "split_type":
            "chronological",

        "random_state":
            RANDOM_STATE,

        "feature_schema_version":
            "transaction_v2",

        "preprocessing_version":
            "causal_recipient_history_v1",

        "features":
            FEATURE_COLUMNS,

        "excluded_model_features": [
            "oldbalanceOrg",
            "oldbalanceDest",
            "newbalanceOrig",
            "newbalanceDest",
            "nameOrig",
            "nameDest",
            "isFlaggedFraud",
        ],

        "runtime_context_fields": [
            "nameDest",
        ],

        "feature_engineering": [
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
            "destination_transaction_count",
            "destination_previous_mean_amount",
            "amount_vs_destination_history",
            "new_recipient",
            "log_destination_transaction_count",
            "one_hot_transaction_type",
        ],

        "training_statistics": {
            "type_stats":
                type_stats.to_dict(),

            "global_amount_stats":
                global_stats,
        },

        "recipient_history_definition": {
            "history_is_causal": True,
            "same_step_transactions_excluded": True,
            "history_source": "nameDest",
            "current_transaction_included": False,
        },

        "metrics": metrics,

        "output_semantics": {
            "model_output":
                "fraud_probability between 0 and 1",

            "backend_output":
                "transaction_risk between 0 and 100",

            "threshold":
                "Risk thresholds handled by "
                "the fusion engine.",
        },
    }

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        artifact,
        output_path,
    )

    print(
        f"Artifact saved to: {output_path}"
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "FraudShield transaction model "
            "training reference pipeline."
        )
    )

    parser.add_argument(
        "--data",
        required=True,
        help="Path to PaySim CSV.",
    )

    parser.add_argument(
        "--output",
        default=(
            "models/transaction/"
            "transaction_model.joblib"
        ),
        help="Output artifact path.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("FRAUDSHIELD TRANSACTION MODEL TRAINING")
    print("=" * 70)

    df = load_paysim(
        args.data
    )

    print(
        "\nRaw shape:",
        df.shape,
    )

    df = prepare_dataset(
        df
    )

    print(
        "Prepared shape:",
        df.shape,
    )

    train_df, val_df, test_df = (
        chronological_split(
            df
        )
    )

    print("\nChronological split:")
    print(
        "Train:",
        train_df.shape,
        f"| fraud={train_df['isFraud'].sum():,}",
    )
    print(
        "Validation:",
        val_df.shape,
        f"| fraud={val_df['isFraud'].sum():,}",
    )
    print(
        "Test:",
        test_df.shape,
        f"| fraud={test_df['isFraud'].sum():,}",
    )

    type_stats, global_stats = (
        compute_training_statistics(
            train_df
        )
    )

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

    X_train, y_train = (
        create_features(
            train_hist,
            type_stats,
            global_stats,
        )
    )

    X_val, y_val = (
        create_features(
            val_hist,
            type_stats,
            global_stats,
        )
    )

    X_test, y_test = (
        create_features(
            test_hist,
            type_stats,
            global_stats,
        )
    )

    print("\nFeature matrix:")
    print(
        "Train:",
        X_train.shape,
    )
    print(
        "Validation:",
        X_val.shape,
    )
    print(
        "Test:",
        X_test.shape,
    )

    print(
        "\nTraining XGBoost..."
    )

    model = train_model(
        X_train,
        y_train,
        X_val,
        y_val,
    )

    metrics = evaluate_model(
        model,
        X_val,
        y_val,
        X_test,
        y_test,
    )

    print(
        "\nEvaluation:"
    )

    for key, value in metrics.items():
        print(
            f"{key}: {value:.6f}"
        )

    print(
        "\nBest boosting round:",
        model.best_iteration,
    )

    print(
        "Best validation PR-AUC:",
        model.best_score,
    )

    save_artifact(
        model,
        type_stats,
        global_stats,
        metrics,
        args.output,
    )

    print(
        "\nTraining pipeline completed."
    )


if __name__ == "__main__":
    main()
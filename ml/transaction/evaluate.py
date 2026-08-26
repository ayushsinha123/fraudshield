from __future__ import annotations

import argparse
from pathlib import Path

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


def load_artifact(path: str | Path) -> dict:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Artifact not found: {path}"
        )

    artifact = joblib.load(path)

    if not isinstance(artifact, dict):
        raise ValueError(
            "Invalid artifact format."
        )

    required = [
        "model",
        "features",
        "metrics",
    ]

    missing = [
        key
        for key in required
        if key not in artifact
    ]

    if missing:
        raise ValueError(
            f"Artifact missing keys: {missing}"
        )

    return artifact


def precision_at_percent(
    y_true,
    scores,
    percent: float,
) -> float:

    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    k = max(
        1,
        int(len(scores) * percent / 100),
    )

    top_indices = np.argsort(scores)[-k:]

    return float(
        y_true[top_indices].mean()
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Verify and inspect a "
            "FraudShield transaction artifact."
        )
    )

    parser.add_argument(
        "--artifact",
        required=True,
        help="Path to transaction_model.joblib",
    )

    args = parser.parse_args()

    artifact = load_artifact(
        args.artifact
    )

    model = artifact["model"]

    print("=" * 70)
    print("FRAUDSHIELD TRANSACTION ARTIFACT")
    print("=" * 70)

    print(
        "\nModel type:",
        type(model).__name__,
    )

    print(
        "Model role:",
        artifact.get(
            "model_role",
            "unknown",
        ),
    )

    print(
        "Dataset:",
        artifact.get(
            "dataset",
            "unknown",
        ),
    )

    print(
        "Split type:",
        artifact.get(
            "split_type",
            "unknown",
        ),
    )

    print(
        "Feature schema:",
        artifact.get(
            "feature_schema_version",
            "unknown",
        ),
    )

    print(
        "Preprocessing:",
        artifact.get(
            "preprocessing_version",
            "unknown",
        ),
    )

    print(
        "\nFeature count:",
        len(artifact["features"]),
    )

    print("\nFeatures:")

    for feature in artifact["features"]:
        print(" -", feature)

    print("\nStored evaluation metrics:")

    for key, value in artifact[
        "metrics"
    ].items():
        if isinstance(value, (int, float)):
            print(
                f"{key}: {value:.6f}"
            )
        else:
            print(
                f"{key}: {value}"
            )

    print("\nArtifact verification complete.")


if __name__ == "__main__":
    main()
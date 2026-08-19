from __future__ import annotations

from pathlib import Path

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]

VOICE_MODEL_DIR = (
    PROJECT_ROOT / "models" / "voice"
)

CLASSIFIER_PATH = (
    VOICE_MODEL_DIR / "voice_classifier.joblib"
)

CONFIG_PATH = (
    VOICE_MODEL_DIR / "voice_config.joblib"
)

EMBEDDING_MODEL_PATH = (
    VOICE_MODEL_DIR / "embedding_model"
)


def validate_voice_artifacts() -> None:

    print("Checking FraudShield voice artifacts...")
    print("=" * 60)

    required = {
        "Classifier": CLASSIFIER_PATH,
        "Config": CONFIG_PATH,
        "Embedding model": EMBEDDING_MODEL_PATH,
    }

    missing = False

    for name, path in required.items():

        exists = path.exists()

        print(
            f"{name:20} : "
            f"{'OK' if exists else 'MISSING'}"
        )

        print(
            f"Path                 : {path}"
        )

        if not exists:
            missing = True

    if missing:
        raise FileNotFoundError(
            "\nOne or more voice artifacts are missing."
        )

    classifier = joblib.load(
        CLASSIFIER_PATH
    )

    config = joblib.load(
        CONFIG_PATH
    )

    print("\nClassifier type:")
    print(type(classifier).__name__)

    print("\nEmbedding model:")
    print(
        config.get(
            "embedding_model",
            "Not found",
        )
    )

    print("\nConfigured risk signals:")
    print(
        list(
            config.get(
                "risk_patterns",
                {}
            ).keys()
        )
    )

    print(
        "\nVoice artifacts are valid."
    )


if __name__ == "__main__":
    validate_voice_artifacts()
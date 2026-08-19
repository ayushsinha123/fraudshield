from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import joblib
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

VOICE_MODEL_DIR = PROJECT_ROOT / "models" / "voice"

CLASSIFIER_PATH = (
    VOICE_MODEL_DIR / "voice_classifier.joblib"
)

CONFIG_PATH = (
    VOICE_MODEL_DIR / "voice_config.joblib"
)

EMBEDDING_MODEL_PATH = (
    VOICE_MODEL_DIR / "embedding_model"
)


class VoiceRiskAnalyzer:
    """
    FraudShield transcript-level social-engineering
    and vishing risk analyzer.
    """

    def __init__(
        self,
        classifier_path: Path = CLASSIFIER_PATH,
        config_path: Path = CONFIG_PATH,
        embedding_model_path: Path = EMBEDDING_MODEL_PATH,
    ) -> None:

        self.classifier_path = Path(
            classifier_path
        )
        self.config_path = Path(
            config_path
        )
        self.embedding_model_path = Path(
            embedding_model_path
        )

        self._validate_artifacts()

        self.classifier = joblib.load(
            self.classifier_path
        )

        self.config = joblib.load(
            self.config_path
        )

        self.embedding_model = SentenceTransformer(
            str(self.embedding_model_path)
        )

        self.risk_patterns = self.config.get(
            "risk_patterns",
            {},
        )

        self.signal_weights = self.config.get(
            "signal_weights",
            {},
        )

    def _validate_artifacts(self) -> None:

        required = {
            "classifier": self.classifier_path,
            "config": self.config_path,
            "embedding_model": self.embedding_model_path,
        }

        missing = [
            f"{name}: {path}"
            for name, path in required.items()
            if not path.exists()
        ]

        if missing:
            raise FileNotFoundError(
                "Missing voice model artifacts:\n"
                + "\n".join(missing)
            )

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        if not isinstance(text, str):
            text = str(text)

        return text.strip()

    def detect_risk_signals(
        self,
        text: str,
    ) -> list[str]:

        text = self._normalize_text(text)

        detected_signals: list[str] = []

        for signal, patterns in self.risk_patterns.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    detected_signals.append(signal)
                    break

        return detected_signals

    def calculate_rule_risk(
        self,
        signals: list[str],
    ) -> float:

        if not signals:
            return 0.0

        total_risk = 0.0

        for signal in signals:

            weight = self.signal_weights.get(
                signal,
                10,
            )

            total_risk += float(weight)

        return min(total_risk, 100.0)

    def analyze(
        self,
        transcript: str,
    ) -> dict[str, Any]:

        transcript = self._normalize_text(
            transcript
        )

        if not transcript:
            return {
                "transcript": "",
                "fraud_probability": 0.0,
                "voice_risk": 0.0,
                "rule_risk": 0.0,
                "risk_signals": [],
                "risk_level": "LOW",
                "reasons": [],
            }

        embedding = self.embedding_model.encode(
            [transcript],
            normalize_embeddings=True,
        )

        fraud_probability = float(
            self.classifier.predict_proba(
                embedding
            )[0, 1]
        )

        ml_risk = fraud_probability * 100.0

        risk_signals = self.detect_risk_signals(
            transcript
        )

        rule_risk = self.calculate_rule_risk(
            risk_signals
        )

        final_voice_risk = (
            0.70 * ml_risk
            + 0.30 * rule_risk
        )

        final_voice_risk = min(
            max(final_voice_risk, 0.0),
            100.0,
        )

        if final_voice_risk >= 80:
            risk_level = "CRITICAL"
        elif final_voice_risk >= 60:
            risk_level = "HIGH"
        elif final_voice_risk >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        reasons = [
            f"Suspicious {signal.replace('_', ' ')} signal detected"
            for signal in risk_signals
        ]

        if ml_risk >= 80:
            reasons.append(
                "Speech content strongly resembles "
                "fraudulent social-engineering language"
            )

        return {
            "transcript": transcript,
            "fraud_probability": fraud_probability,
            "voice_risk": round(
                final_voice_risk,
                2,
            ),
            "rule_risk": round(
                rule_risk,
                2,
            ),
            "ml_risk": round(
                ml_risk,
                2,
            ),
            "risk_signals": risk_signals,
            "risk_level": risk_level,
            "reasons": reasons,
        }


if __name__ == "__main__":

    analyzer = VoiceRiskAnalyzer()

    test_text = (
        "Your bank account will be blocked immediately. "
        "Give me your OTP now."
    )

    result = analyzer.analyze(
        test_text
    )

    print("\nVoice risk test")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")
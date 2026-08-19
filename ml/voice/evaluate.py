from __future__ import annotations

from ml.voice.features import (
    VoiceRiskAnalyzer,
)


def main() -> None:

    analyzer = VoiceRiskAnalyzer()

    test_cases = [
        (
            "Fraudulent English",
            "Your bank account will be blocked immediately. "
            "Give me your OTP now.",
        ),
        (
            "Legitimate English",
            "Your appointment is confirmed for tomorrow "
            "at 10 AM.",
        ),
        (
            "Fraudulent French",
            "Votre compte sera bloqué immédiatement. "
            "Donnez-moi votre code de vérification.",
        ),
        (
            "Fraudulent Arabic",
            "سيتم إيقاف حسابك الآن. "
            "أعطني رمز التحقق.",
        ),
    ]

    print(
        "FraudShield Voice Engine Evaluation"
    )
    print("=" * 80)

    for name, text in test_cases:

        result = analyzer.analyze(text)

        print("\n" + "-" * 80)
        print(name)
        print("-" * 80)

        print("Transcript:")
        print(text)

        print(
            "\nFraud probability:",
            f"{result['fraud_probability']:.4f}",
        )

        print(
            "ML risk:",
            f"{result['ml_risk']:.2f}",
        )

        print(
            "Rule risk:",
            f"{result['rule_risk']:.2f}",
        )

        print(
            "Final voice risk:",
            f"{result['voice_risk']:.2f}",
        )

        print(
            "Risk level:",
            result["risk_level"],
        )

        print(
            "Risk signals:",
            result["risk_signals"],
        )

        print(
            "Reasons:",
            result["reasons"],
        )


if __name__ == "__main__":
    main()
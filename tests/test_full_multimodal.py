from __future__ import annotations

import argparse
import json

from backend.app.services.transaction_model import TransactionModel
from backend.app.services.behaviour_engine import BehaviourEngine
from backend.app.services.device_engine import DeviceEngine
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.voice_engine import VoiceEngine


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_multimodal_test(audio_path: str | None = None) -> None:
    # =========================================================
    # 1. INPUT SCENARIO
    # =========================================================

    transaction = {
        "step": 12,
        "type": "TRANSFER",
        "amount": 5000.0,
        "nameDest": "MULTIMODAL_TEST_RECIPIENT",
    }

    # Strong suspicious behavioural context.
    behaviour_input = {
        "amount": 5000.0,
        "hour": 2,
        "new_recipient": 1,
        "new_device": 1,
        "unusual_hour": 1,
        "burst": 1,
        "location_jump": 1,
        "network_change": 1,
    }

    # Strong suspicious device context.
    device_input = {
        "new_device": True,
        "network_change": True,
        "location_jump": True,
        "sim_change": True,
    }

    print_section("FRAUDSHIELD — FULL MULTIMODAL TEST")

    print("\nTransaction input:")
    print(json.dumps(transaction, indent=2))

    print("\nBehaviour context:")
    print(json.dumps(behaviour_input, indent=2))

    print("\nDevice context:")
    print(json.dumps(device_input, indent=2))

    # =========================================================
    # 2. TRANSACTION MODEL
    # =========================================================

    print_section("1. TRANSACTION MODEL")

    transaction_engine = TransactionModel()

    transaction_result = (
        transaction_engine.score_transaction(
            transaction,
            update_history=False,
        )
    )

    print(
        f"Raw probability        : "
        f"{transaction_result['raw_fraud_probability']}"
    )

    print(
        f"Calibrated probability : "
        f"{transaction_result['calibrated_fraud_probability']}"
    )

    print(
        f"Transaction risk       : "
        f"{transaction_result['transaction_risk']}"
    )

    print(
        f"Transaction level      : "
        f"{transaction_result['risk_level']}"
    )

    print("\nTransaction reasons:")
    for reason in transaction_result["reasons"]:
        print(f"- {reason}")

    # =========================================================
    # 3. BEHAVIOUR ENGINE
    # =========================================================

    print_section("2. BEHAVIOUR ENGINE")

    behaviour_engine = BehaviourEngine()

    behaviour_result = (
        behaviour_engine.score_transaction(
            behaviour_input
        )
    )

    print(
        f"Behaviour risk         : "
        f"{behaviour_result['behaviour_risk']}"
    )

    print(
        f"Behaviour level        : "
        f"{behaviour_result['risk_level']}"
    )

    print(
        f"Anomalous               : "
        f"{behaviour_result['is_anomalous']}"
    )

    print(
        f"Anomaly score           : "
        f"{behaviour_result['anomaly_score']}"
    )

    print("\nBehaviour reasons:")
    for reason in behaviour_result["reasons"]:
        print(f"- {reason}")

    # =========================================================
    # 4. DEVICE ENGINE
    # =========================================================

    print_section("3. DEVICE ENGINE")

    device_engine = DeviceEngine()

    device_result = (
        device_engine.calculate_risk(
            device_input
        )
    )

    print(
        f"Device risk            : "
        f"{device_result['device_risk']}"
    )

    print(
        f"Device level           : "
        f"{device_result['risk_level']}"
    )

    print("\nDevice reasons:")
    for reason in device_result["reasons"]:
        print(f"- {reason}")

    # =========================================================
    # 5. VOICE ENGINE
    # =========================================================

    print_section("4. VOICE ENGINE")

    voice_risk = 0.0
    voice_result = None

    if audio_path:
        print(
            f"Analyzing audio file:\n"
            f"{audio_path}"
        )

        voice_engine = VoiceEngine()

        voice_result = (
            voice_engine.analyze_audio(
                audio_path
            )
        )

        voice_risk = float(
            voice_result["voice_risk"]
        )

        print(
            f"\nVoice risk            : "
            f"{voice_result['voice_risk']}"
        )

        print(
            f"Voice probability     : "
            f"{voice_result['fraud_probability']}"
        )

        print(
            f"Voice level           : "
            f"{voice_result['risk_level']}"
        )

        print(
            f"Language              : "
            f"{voice_result['language']}"
        )

        print("\nVoice reasons:")
        for reason in voice_result["reasons"]:
            print(f"- {reason}")

    else:
        print(
            "No audio file supplied."
        )
        print(
            "Voice risk = 0.0 for this run."
        )
        print(
            "Pass --audio <path-to-audio> "
            "to include the real VoiceEngine."
        )

    # =========================================================
    # 6. RISK ENGINE
    # =========================================================

    print_section("5. RISK ENGINE — MULTIMODAL FUSION")

    risk_engine = RiskEngine()

    risk_result = risk_engine.calculate_risk(
        transaction_risk=float(
            transaction_result[
                "transaction_risk"
            ]
        ),
        behaviour_risk=float(
            behaviour_result[
                "behaviour_risk"
            ]
        ),
        device_risk=float(
            device_result[
                "device_risk"
            ]
        ),
        voice_risk=voice_risk,
        transaction_reasons=(
            transaction_result["reasons"]
        ),
        behaviour_reasons=(
            behaviour_result["reasons"]
        ),
        device_reasons=(
            device_result["reasons"]
        ),
        voice_reasons=(
            voice_result["reasons"]
            if voice_result
            else []
        ),
    )

    # =========================================================
    # 7. FINAL RESULT
    # =========================================================

    print_section("FINAL FRAUDSHIELD RESULT")

    print(
        f"Transaction risk : "
        f"{risk_result['component_risks']['transaction_risk']}"
    )

    print(
        f"Behaviour risk   : "
        f"{risk_result['component_risks']['behaviour_risk']}"
    )

    print(
        f"Device risk      : "
        f"{risk_result['component_risks']['device_risk']}"
    )

    print(
        f"Voice risk       : "
        f"{risk_result['component_risks']['voice_risk']}"
    )

    print(
        f"\nFINAL RISK       : "
        f"{risk_result['final_risk']}"
    )

    print(
        f"FINAL LEVEL      : "
        f"{risk_result['risk_level']}"
    )

    print("\nWeighted contributions:")
    print(
        json.dumps(
            risk_result[
                "weighted_contributions"
            ],
            indent=2,
        )
    )

    print("\nCombined reasons:")
    for reason in risk_result["reasons"]:
        print(f"- {reason}")

    print("\nComplete result:")
    print(
        json.dumps(
            risk_result,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "FraudShield full multimodal "
            "risk test"
        )
    )

    parser.add_argument(
        "--audio",
        type=str,
        default=None,
        help=(
            "Optional path to an audio file "
            "for VoiceEngine testing"
        ),
    )

    args = parser.parse_args()

    run_multimodal_test(
        audio_path=args.audio
    )


if __name__ == "__main__":
    main()
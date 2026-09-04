from backend.app.services.risk_engine import RiskEngine


def run_case(
    name: str,
    transaction: float,
    behaviour: float,
    device: float,
    voice: float,
) -> None:
    engine = RiskEngine()

    result = engine.calculate_risk(
        transaction_risk=transaction,
        behaviour_risk=behaviour,
        device_risk=device,
        voice_risk=voice,
    )

    print(f"\n{name}")
    print("-" * 60)
    print(f"Transaction : {transaction}")
    print(f"Behaviour   : {behaviour}")
    print(f"Device      : {device}")
    print(f"Voice       : {voice}")
    print(f"Final risk  : {result['final_risk']}")
    print(f"Risk level  : {result['risk_level']}")
    print(f"Contrib.    : {result['weighted_contributions']}")


def main() -> None:
    run_case(
        "CASE A — SAFE PAYMENT",
        0.0,
        0.0,
        0.0,
        0.0,
    )

    run_case(
        "CASE B — ₹5000 TRANSFER / CALIBRATED TRANSACTION ONLY",
        5.54,
        0.0,
        0.0,
        0.0,
    )

    run_case(
        "CASE C — STRONG MULTIMODAL",
        5.54,
        90.0,
        85.0,
        84.11,
    )

    run_case(
        "CASE D — MAXIMUM NON-TRANSACTION SIGNALS",
        5.54,
        100.0,
        100.0,
        100.0,
    )


if __name__ == "__main__":
    main()
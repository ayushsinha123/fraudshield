from __future__ import annotations


def classify_base_risk(risk: float) -> str:
    if risk >= 80:
        return "CRITICAL"
    if risk >= 60:
        return "HIGH"
    if risk >= 30:
        return "MEDIUM"
    return "LOW"


def candidate_policy(
    transaction: float,
    behaviour: float,
    device: float,
    voice: float,
) -> tuple[float, str, str]:
    # Existing weighted fusion
    base_risk = (
        0.50 * transaction
        + 0.20 * behaviour
        + 0.10 * device
        + 0.20 * voice
    )

    final_risk = base_risk
    escalation = "NONE"

    # Candidate 1:
    # Strong behaviour + device combination
    if behaviour >= 80 and device >= 80:
        final_risk = max(final_risk, 60.0)
        escalation = "BEHAVIOUR+DEVICE"

    # Candidate 2:
    # Strong voice combined with another strong modality
    if voice >= 80 and (
        behaviour >= 80 or device >= 80
    ):
        final_risk = max(final_risk, 80.0)
        escalation = "VOICE+STRONG_MODALITY"

    # Candidate 3:
    # Extremely strong multi-modal evidence
    strong_modalities = sum(
        score >= 80
        for score in [
            transaction,
            behaviour,
            device,
            voice,
        ]
    )

    if strong_modalities >= 3:
        final_risk = max(final_risk, 80.0)
        escalation = "3+_STRONG_MODALITIES"

    final_risk = min(100.0, final_risk)

    return (
        round(base_risk, 2),
        round(final_risk, 2),
        escalation,
    )


def run_case(
    name: str,
    transaction: float,
    behaviour: float,
    device: float,
    voice: float,
) -> None:
    base, final, escalation = candidate_policy(
        transaction,
        behaviour,
        device,
        voice,
    )

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print(f"Transaction : {transaction}")
    print(f"Behaviour   : {behaviour}")
    print(f"Device      : {device}")
    print(f"Voice       : {voice}")

    print(f"\nBase fusion : {base}")
    print(f"Escalation  : {escalation}")
    print(f"Final risk  : {final}")
    print(f"Final level : {classify_base_risk(final)}")


def main() -> None:
    # A — Safe payment
    run_case(
        "CASE A — SAFE PAYMENT",
        transaction=0.0,
        behaviour=0.0,
        device=0.0,
        voice=0.0,
    )

    # B — ₹5000 payment, isolated transaction signal
    run_case(
        "CASE B — ₹5000 PAYMENT",
        transaction=0.0,
        behaviour=0.0,
        device=0.0,
        voice=0.0,
    )

    # C — Suspicious transfer alone
    run_case(
        "CASE C — ₹5000 TRANSFER",
        transaction=5.54,
        behaviour=0.0,
        device=0.0,
        voice=0.0,
    )

    # D — Strong behaviour + device
    run_case(
        "CASE D — STRONG BEHAVIOUR + DEVICE",
        transaction=5.54,
        behaviour=100.0,
        device=100.0,
        voice=0.0,
    )

    # E — Strong behaviour + device + voice
    run_case(
        "CASE E — STRONG MULTIMODAL",
        transaction=5.54,
        behaviour=100.0,
        device=100.0,
        voice=84.11,
    )

    # F — Maximum non-transaction evidence
    run_case(
        "CASE F — MAXIMUM MULTIMODAL",
        transaction=5.54,
        behaviour=100.0,
        device=100.0,
        voice=100.0,
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

from typing import Any, Dict, Optional


class RiskEngine:
    """
    FraudShield multimodal risk fusion engine.

    Combines:
        transaction_risk
        behaviour_risk
        device_risk
        voice_risk

    Baseline fusion weights:
        Transaction = 50%
        Behaviour  = 20%
        Device     = 10%
        Voice      = 20%

    After the weighted fusion, a policy-level multimodal
    escalation layer is applied.

    The escalation layer does NOT replace the weighted fusion.
    It exists to ensure that strong independent signals from
    multiple modalities can elevate the final product risk.

    Product-risk layers:

        component risks
              ↓
        weighted fusion
              ↓
        multimodal escalation policy
              ↓
        final product risk
              ↓
        risk level
    """

    # ---------------------------------------------------------
    # Baseline fusion weights
    # ---------------------------------------------------------

    WEIGHTS = {
        "transaction": 0.50,
        "behaviour": 0.20,
        "device": 0.10,
        "voice": 0.20,
    }

    # ---------------------------------------------------------
    # Policy thresholds
    # ---------------------------------------------------------

    STRONG_MODALITY_THRESHOLD = 80.0

    BEHAVIOUR_DEVICE_ESCALATION_RISK = 60.0

    MULTIMODAL_ESCALATION_RISK = 80.0

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:

        self.weights = (
            weights.copy()
            if weights is not None
            else self.WEIGHTS.copy()
        )

        self._validate_weights()

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate_weights(self) -> None:

        required = {
            "transaction",
            "behaviour",
            "device",
            "voice",
        }

        if set(self.weights.keys()) != required:
            raise ValueError(
                "Risk weights must contain exactly: "
                f"{sorted(required)}"
            )

        if any(
            weight < 0
            for weight in self.weights.values()
        ):
            raise ValueError(
                "Risk weights cannot be negative."
            )

        total = sum(
            self.weights.values()
        )

        if not abs(total - 1.0) < 1e-9:
            raise ValueError(
                f"Risk weights must sum to 1.0, "
                f"got {total}"
            )

    # ---------------------------------------------------------
    # Risk level
    # ---------------------------------------------------------

    @staticmethod
    def get_risk_level(
        risk: float,
    ) -> str:

        if risk >= 80:
            return "CRITICAL"

        if risk >= 60:
            return "HIGH"

        if risk >= 30:
            return "MEDIUM"

        return "LOW"

    # ---------------------------------------------------------
    # Clamp
    # ---------------------------------------------------------

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                100.0,
                float(value),
            ),
        )

    # ---------------------------------------------------------
    # Multimodal escalation policy
    # ---------------------------------------------------------

    def _apply_multimodal_policy(
        self,
        base_risk: float,
        transaction_risk: float,
        behaviour_risk: float,
        device_risk: float,
        voice_risk: float,
    ) -> tuple[float, list[str]]:
        """
        Apply the tested multimodal escalation policy.

        The baseline weighted fusion remains the primary score.

        Policy rules:

        1. Strong behaviour + strong device:
           final product risk cannot be below HIGH (60).

        2. Strong voice + either strong behaviour or device:
           final product risk cannot be below CRITICAL (80).

        3. Three or more strong modalities:
           final product risk cannot be below CRITICAL (80).

        "Strong" means component risk >= 80.

        Returns:
            (
                final_risk,
                escalation_reasons
            )
        """

        final_risk = base_risk
        escalation_reasons: list[str] = []

        # -----------------------------------------------------
        # Rule 1:
        # Strong behaviour + device
        # -----------------------------------------------------

        if (
            behaviour_risk
            >= self.STRONG_MODALITY_THRESHOLD
            and device_risk
            >= self.STRONG_MODALITY_THRESHOLD
        ):
            final_risk = max(
                final_risk,
                self.BEHAVIOUR_DEVICE_ESCALATION_RISK,
            )

            escalation_reasons.append(
                "Strong behaviour and device risk combination detected"
            )

        # -----------------------------------------------------
        # Rule 2:
        # Strong voice + another strong modality
        # -----------------------------------------------------

        if (
            voice_risk
            >= self.STRONG_MODALITY_THRESHOLD
            and (
                behaviour_risk
                >= self.STRONG_MODALITY_THRESHOLD
                or device_risk
                >= self.STRONG_MODALITY_THRESHOLD
            )
        ):
            final_risk = max(
                final_risk,
                self.MULTIMODAL_ESCALATION_RISK,
            )

            escalation_reasons.append(
                "Strong voice and contextual fraud signals detected"
            )

        # -----------------------------------------------------
        # Rule 3:
        # Three or more strong modalities
        # -----------------------------------------------------

        strong_modalities = sum(
            score >= self.STRONG_MODALITY_THRESHOLD
            for score in [
                transaction_risk,
                behaviour_risk,
                device_risk,
                voice_risk,
            ]
        )

        if strong_modalities >= 3:
            final_risk = max(
                final_risk,
                self.MULTIMODAL_ESCALATION_RISK,
            )

            escalation_reasons.append(
                "Strong multimodal fraud signal detected"
            )

        return (
            self._clamp(final_risk),
            escalation_reasons,
        )

    # ---------------------------------------------------------
    # Fuse scores
    # ---------------------------------------------------------

    def calculate_risk(
        self,
        transaction_risk: float,
        behaviour_risk: float,
        device_risk: float,
        voice_risk: float,
        transaction_reasons: Optional[list[str]] = None,
        behaviour_reasons: Optional[list[str]] = None,
        device_reasons: Optional[list[str]] = None,
        voice_reasons: Optional[list[str]] = None,
    ) -> Dict[str, Any]:

        # -----------------------------------------------------
        # Clamp component scores
        # -----------------------------------------------------

        transaction_risk = self._clamp(
            transaction_risk
        )

        behaviour_risk = self._clamp(
            behaviour_risk
        )

        device_risk = self._clamp(
            device_risk
        )

        voice_risk = self._clamp(
            voice_risk
        )

        # -----------------------------------------------------
        # Baseline weighted fusion
        # -----------------------------------------------------

        transaction_contribution = (
            self.weights["transaction"]
            * transaction_risk
        )

        behaviour_contribution = (
            self.weights["behaviour"]
            * behaviour_risk
        )

        device_contribution = (
            self.weights["device"]
            * device_risk
        )

        voice_contribution = (
            self.weights["voice"]
            * voice_risk
        )

        base_risk = (
            transaction_contribution
            + behaviour_contribution
            + device_contribution
            + voice_contribution
        )

        base_risk = self._clamp(
            base_risk
        )

        # -----------------------------------------------------
        # Multimodal policy escalation
        # -----------------------------------------------------

        final_risk, escalation_reasons = (
            self._apply_multimodal_policy(
                base_risk=base_risk,
                transaction_risk=transaction_risk,
                behaviour_risk=behaviour_risk,
                device_risk=device_risk,
                voice_risk=voice_risk,
            )
        )

        # -----------------------------------------------------
        # Final risk level
        # -----------------------------------------------------

        risk_level = self.get_risk_level(
            final_risk
        )

        # -----------------------------------------------------
        # Reasons
        # -----------------------------------------------------

        reasons: list[str] = []

        for source_reasons in [
            transaction_reasons,
            behaviour_reasons,
            device_reasons,
            voice_reasons,
        ]:
            if source_reasons:
                reasons.extend(
                    source_reasons
                )

        # Add policy-level explanations.
        reasons.extend(
            escalation_reasons
        )

        # Remove duplicates while preserving order.
        unique_reasons = list(
            dict.fromkeys(reasons)
        )

        # -----------------------------------------------------
        # Component contributions
        #
        # These remain based on the original
        # transparent 50/20/10/20 weighted fusion.
        # -----------------------------------------------------

        contributions = {
            "transaction": round(
                transaction_contribution,
                2,
            ),
            "behaviour": round(
                behaviour_contribution,
                2,
            ),
            "device": round(
                device_contribution,
                2,
            ),
            "voice": round(
                voice_contribution,
                2,
            ),
        }

        # -----------------------------------------------------
        # Return
        # -----------------------------------------------------

        return {
            "final_risk": round(
                final_risk,
                2,
            ),

            "base_fusion_risk": round(
                base_risk,
                2,
            ),

            "risk_level": risk_level,

            "component_risks": {
                "transaction_risk": round(
                    transaction_risk,
                    2,
                ),
                "behaviour_risk": round(
                    behaviour_risk,
                    2,
                ),
                "device_risk": round(
                    device_risk,
                    2,
                ),
                "voice_risk": round(
                    voice_risk,
                    2,
                ),
            },

            "weighted_contributions": contributions,

            "weights": self.weights.copy(),

            "escalation_reasons": (
                escalation_reasons
            ),

            "reasons": unique_reasons,
        }


# -------------------------------------------------------------
# Local smoke test
# -------------------------------------------------------------

if __name__ == "__main__":

    engine = RiskEngine()

    result = engine.calculate_risk(
        transaction_risk=75,
        behaviour_risk=90,
        device_risk=85,
        voice_risk=84.11,

        transaction_reasons=[
            "New recipient detected",
            "Large transaction amount detected",
        ],

        behaviour_reasons=[
            "Unusual transaction burst",
            "Overall transaction behaviour is anomalous",
        ],

        device_reasons=[
            "New device detected",
            "New network detected",
        ],

        voice_reasons=[
            "Suspicious social-engineering indicators detected",
        ],
    )

    print(
        "Risk engine test result:"
    )

    print(result)
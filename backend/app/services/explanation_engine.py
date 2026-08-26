# backend/app/services/explanation_engine.py

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ExplanationEngine:
    """
    Converts FraudShield's multimodal risk outputs into
    a structured, user-friendly explanation.

    Inputs:
        - final_risk
        - risk_level
        - component_risks
        - weighted_contributions
        - reasons

    Output:
        - concise summary
        - risk message
        - grouped reasons
        - component contribution breakdown
    """

    RISK_MESSAGES = {
        "LOW": (
            "This payment appears to have a low level of risk."
        ),
        "MEDIUM": (
            "This payment shows some unusual signals. "
            "Please review the payment details carefully."
        ),
        "HIGH": (
            "This payment shows multiple elevated-risk signals. "
            "Please verify the recipient and payment details before continuing."
        ),
        "CRITICAL": (
            "This payment shows multiple strong fraud-risk signals. "
            "Verify the recipient, device, and surrounding context before proceeding."
        ),
    }

    def __init__(self) -> None:
        pass

    # ---------------------------------------------------------
    # Risk level
    # ---------------------------------------------------------

    @staticmethod
    def _risk_level(
        final_risk: float,
    ) -> str:

        if final_risk >= 80:
            return "CRITICAL"

        if final_risk >= 60:
            return "HIGH"

        if final_risk >= 30:
            return "MEDIUM"

        return "LOW"

    # ---------------------------------------------------------
    # Reason cleanup
    # ---------------------------------------------------------

    @staticmethod
    def _deduplicate_reasons(
        reasons: Optional[List[str]],
    ) -> List[str]:

        if not reasons:
            return []

        return list(
            dict.fromkeys(
                str(reason).strip()
                for reason in reasons
                if str(reason).strip()
            )
        )

    # ---------------------------------------------------------
    # Component summary
    # ---------------------------------------------------------

    @staticmethod
    def _build_component_summary(
        component_risks: Dict[str, Any],
    ) -> Dict[str, float]:

        return {
            "transaction": round(
                float(
                    component_risks.get(
                        "transaction_risk",
                        0.0,
                    )
                ),
                2,
            ),
            "behaviour": round(
                float(
                    component_risks.get(
                        "behaviour_risk",
                        0.0,
                    )
                ),
                2,
            ),
            "device": round(
                float(
                    component_risks.get(
                        "device_risk",
                        0.0,
                    )
                ),
                2,
            ),
            "voice": round(
                float(
                    component_risks.get(
                        "voice_risk",
                        0.0,
                    )
                ),
                2,
            ),
        }

    # ---------------------------------------------------------
    # Natural-language explanation
    # ---------------------------------------------------------

    @staticmethod
    def _build_summary(
        risk_level: str,
        reasons: List[str],
    ) -> str:

        if not reasons:

            if risk_level == "LOW":
                return (
                    "No major risk indicators were detected."
                )

            return (
                "The system detected elevated risk signals."
            )

        if risk_level == "LOW":
            return (
                "The payment does not currently show "
                "major suspicious indicators."
            )

        if risk_level == "MEDIUM":
            return (
                "The payment shows some unusual activity "
                "that should be reviewed before proceeding."
            )

        if risk_level == "HIGH":
            return (
                "The payment shows multiple elevated-risk "
                "signals and should be verified before proceeding."
            )

        return (
            "The payment shows multiple strong fraud-risk "
            "signals and should be carefully verified before proceeding."
        )

    # ---------------------------------------------------------
    # Main explanation method
    # ---------------------------------------------------------

    def explain(
        self,
        risk_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        if "final_risk" not in risk_result:
            raise ValueError(
                "risk_result must contain 'final_risk'."
            )

        final_risk = float(
            risk_result["final_risk"]
        )

        final_risk = max(
            0.0,
            min(
                100.0,
                final_risk,
            ),
        )

        risk_level = str(
            risk_result.get(
                "risk_level",
                self._risk_level(final_risk),
            )
        ).upper()

        reasons = self._deduplicate_reasons(
            risk_result.get(
                "reasons",
                [],
            )
        )

        component_risks = (
            self._build_component_summary(
                risk_result.get(
                    "component_risks",
                    {},
                )
            )
        )

        weighted_contributions = {
            key: round(
                float(value),
                2,
            )
            for key, value in (
                risk_result.get(
                    "weighted_contributions",
                    {},
                )
            ).items()
        }

        message = self.RISK_MESSAGES.get(
            risk_level,
            self.RISK_MESSAGES["MEDIUM"],
        )

        summary = self._build_summary(
            risk_level,
            reasons,
        )

        # Rank reasons in the order they were
        # supplied by the fusion engine.
        top_reasons = reasons[:5]

        return {
            "risk_score": round(
                final_risk,
                2,
            ),
            "risk_level": risk_level,

            "headline": (
                f"{risk_level} RISK"
            ),

            "summary": summary,

            "message": message,

            "reasons": top_reasons,

            "component_risks": (
                component_risks
            ),

            "weighted_contributions": (
                weighted_contributions
            ),

            "requires_confirmation": (
                final_risk >= 30
            ),

            "high_friction": (
                final_risk >= 80
            ),
        }


# -------------------------------------------------------------
# Local smoke test
# -------------------------------------------------------------

if __name__ == "__main__":

    engine = ExplanationEngine()

    sample_risk = {
        "final_risk": 80.82,
        "risk_level": "CRITICAL",

        "component_risks": {
            "transaction_risk": 75.0,
            "behaviour_risk": 90.0,
            "device_risk": 85.0,
            "voice_risk": 84.11,
        },

        "weighted_contributions": {
            "transaction": 37.5,
            "behaviour": 18.0,
            "device": 8.5,
            "voice": 16.82,
        },

        "reasons": [
            "New recipient detected",
            "Large transaction amount detected",
            "Unusual transaction burst",
            "Overall transaction behaviour is anomalous",
            "New device detected",
            "New network detected",
            "Suspicious social-engineering indicators detected",
        ],
    }

    explanation = engine.explain(
        sample_risk
    )

    print(
        "Explanation engine test result:"
    )

    print(explanation)
# backend/app/services/device_engine.py

from __future__ import annotations

from typing import Any, Dict


class DeviceEngine:
    """
    FraudShield device-risk service.

    Rule-based device/context risk scoring.
    Mirrors ml/device/device_model.py.
    """

    def calculate_risk(
        self,
        event: Dict[str, Any],
    ) -> Dict[str, Any]:

        risk = 0
        reasons: list[str] = []

        # New device
        if event.get("new_device", False):
            risk += 40
            reasons.append(
                "New device detected"
            )

        # Network change
        if event.get("network_change", False):
            risk += 20
            reasons.append(
                "New network detected"
            )

        # Location jump
        if event.get("location_jump", False):
            risk += 25
            reasons.append(
                "Unusual location change"
            )

        # SIM/device change
        if event.get("sim_change", False):
            risk += 15
            reasons.append(
                "Recent SIM/device change detected"
            )

        risk = min(risk, 100)

        if risk >= 70:
            level = "HIGH"
        elif risk >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "device_risk": risk,
            "risk_level": level,
            "reasons": reasons,
        }


if __name__ == "__main__":

    engine = DeviceEngine()

    test_event = {
        "new_device": True,
        "network_change": True,
        "location_jump": True,
        "sim_change": False,
    }

    result = engine.calculate_risk(
        test_event
    )

    print(
        "Device engine test:"
    )

    print(result)
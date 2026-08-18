from typing import Dict, Any


def calculate_device_risk(event: Dict[str, Any]) -> Dict[str, Any]:

    risk = 0
    reasons = []

    if event.get("new_device", False):
        risk += 40
        reasons.append("New device detected")

    if event.get("network_change", False):
        risk += 20
        reasons.append("New network detected")

    if event.get("location_jump", False):
        risk += 25
        reasons.append("Unusual location change")

    if event.get("sim_change", False):
        risk += 15
        reasons.append("Recent SIM/device change detected")

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

    test_event = {
        "new_device": True,
        "network_change": True,
        "location_jump": True,
        "sim_change": False,
    }

    result = calculate_device_risk(test_event)

    print("Device engine test:")
    print(result)
from pathlib import Path
import numpy as np
import pandas as pd


SEED = 42
rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_USERS = 500
TRANSACTIONS_PER_USER = 50


def generate_data():
    rows = []

    for user_id in range(1, N_USERS + 1):
        user_hash = f"user_{user_id:04d}"

        normal_avg = rng.uniform(500, 15000)
        normal_std = normal_avg * rng.uniform(0.15, 0.35)

        usual_start = int(rng.integers(7, 11))
        usual_end = int(rng.integers(18, 23))

        recipients = [
            f"recipient_{user_id}_{i}"
            for i in range(rng.integers(2, 6))
        ]

        device_id = f"device_{user_id}_01"

        for tx_num in range(TRANSACTIONS_PER_USER):

            amount = max(
                10,
                rng.normal(normal_avg, normal_std)
            )

            hour = int(
                rng.integers(
                    usual_start,
                    max(usual_start + 1, usual_end)
                )
            )

            recipient = rng.choice(recipients)

            new_device = 0
            new_recipient = 0
            unusual_hour = 0
            burst = 0
            location_jump = 0
            network_change = 0

            # Inject anomalies into ~10% of transactions
            if rng.random() < 0.10:

                anomaly = rng.choice([
                    "large_amount",
                    "new_recipient",
                    "unusual_hour",
                    "new_device",
                    "burst",
                    "location_jump",
                    "network_change"
                ])

                if anomaly == "large_amount":
                    amount *= rng.uniform(4, 10)

                elif anomaly == "new_recipient":
                    recipient = f"new_recipient_{user_id}_{tx_num}"
                    new_recipient = 1

                elif anomaly == "unusual_hour":
                    hour = int(rng.choice([0, 1, 2, 3, 4, 5]))
                    unusual_hour = 1

                elif anomaly == "new_device":
                    device_id = f"device_{user_id}_02"
                    new_device = 1

                elif anomaly == "burst":
                    burst = 1

                elif anomaly == "location_jump":
                    location_jump = 1

                elif anomaly == "network_change":
                    network_change = 1

            rows.append({
                "user_hash": user_hash,
                "transaction_index": tx_num,
                "amount": round(float(amount), 2),
                "hour": hour,
                "recipient_hash": recipient,
                "device_hash": device_id,
                "new_recipient": new_recipient,
                "new_device": new_device,
                "unusual_hour": unusual_hour,
                "burst": burst,
                "location_jump": location_jump,
                "network_change": network_change
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":

    df = generate_data()

    output_path = OUTPUT_DIR / "synthetic_user_transactions.csv"

    df.to_csv(output_path, index=False)

    print("Synthetic behaviour data generated.")
    print("Shape:", df.shape)
    print("Saved to:", output_path)

    print("\nAnomaly counts:")
    print(df[
        [
            "new_recipient",
            "new_device",
            "unusual_hour",
            "burst",
            "location_jump",
            "network_change"
        ]
    ].sum())
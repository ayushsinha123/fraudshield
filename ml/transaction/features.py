import pandas as pd


TRANSACTION_TYPES = [
    "PAYMENT",
    "TRANSFER",
    "CASH_OUT",
    "DEBIT",
    "CASH_IN",
]


def create_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()

    # -----------------------------------------------------
    # Time features
    # -----------------------------------------------------

    # PaySim step represents an hourly simulation step
    df["hour"] = df["step"] % 24

    df["day"] = df["step"] // 24

    # Cyclical hour representation
    import numpy as np

    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    # -----------------------------------------------------
    # Amount features
    # -----------------------------------------------------

    df["log_amount"] = np.log1p(df["amount"])

    # Amount relative to origin balance
    df["amount_to_origin_balance"] = (
        df["amount"] / (df["oldbalanceOrg"] + 1.0)
    )

    # -----------------------------------------------------
    # Transaction type
    # -----------------------------------------------------

    df = pd.get_dummies(
        df,
        columns=["type"],
        prefix="type",
        dtype=int,
    )

    # Ensure stable transaction-type columns
    for transaction_type in TRANSACTION_TYPES:
        column = f"type_{transaction_type}"

        if column not in df.columns:
            df[column] = 0

    # -----------------------------------------------------
    # Target
    # -----------------------------------------------------

    y = df["isFraud"].astype(int)

    # Remove target
    X = df.drop(columns=["isFraud"])

    return X, y


if __name__ == "__main__":
    from preprocess import load_raw_data, clean_data

    df = load_raw_data()
    df = clean_data(df)

    X, y = create_features(df)

    print("Feature matrix shape:", X.shape)
    print("Target shape:", y.shape)

    print("\nFeatures:")
    print(X.columns.tolist())
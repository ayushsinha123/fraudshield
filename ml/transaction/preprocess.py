from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "paysim"
    / "PS_20174392719_1491204439457_log.csv"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Columns
# ---------------------------------------------------------

DROP_COLUMNS = [
    "newbalanceOrig",
    "newbalanceDest",
    "nameOrig",
    "nameDest",
    "isFlaggedFraud",
]

REQUIRED_COLUMNS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "oldbalanceDest",
    "isFraud",
]


# ---------------------------------------------------------
# Load + clean
# ---------------------------------------------------------

def load_raw_data(path: str | Path = RAW_DATA_PATH) -> pd.DataFrame:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Remove leakage-prone / identifier / existing-fraud-flag columns
    df = df.drop(columns=DROP_COLUMNS, errors="ignore")

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Remove rows with missing required values
    df = df.dropna(subset=REQUIRED_COLUMNS)

    # Data types
    df["step"] = pd.to_numeric(df["step"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["oldbalanceOrg"] = pd.to_numeric(
        df["oldbalanceOrg"], errors="coerce"
    )
    df["oldbalanceDest"] = pd.to_numeric(
        df["oldbalanceDest"], errors="coerce"
    )
    df["isFraud"] = pd.to_numeric(df["isFraud"], errors="coerce").astype(int)

    # Remove invalid numeric rows
    df = df.dropna(
        subset=[
            "step",
            "amount",
            "oldbalanceOrg",
            "oldbalanceDest",
            "isFraud",
        ]
    )

    # Keep only valid transaction types
    valid_types = {
        "PAYMENT",
        "TRANSFER",
        "CASH_OUT",
        "DEBIT",
        "CASH_IN",
    }

    df = df[df["type"].isin(valid_types)]

    # Sort by simulation time
    df = df.sort_values("step").reset_index(drop=True)

    return df


# ---------------------------------------------------------
# Save processed data
# ---------------------------------------------------------

def save_processed_data(
    df: pd.DataFrame,
    filename: str = "paysim_cleaned.csv",
) -> Path:

    output_path = PROCESSED_DIR / filename

    df.to_csv(output_path, index=False)

    return output_path


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    print("Loading PaySim...")
    df = load_raw_data()

    print(f"Raw shape: {df.shape}")

    df = clean_data(df)

    print(f"Cleaned shape: {df.shape}")
    print("\nColumns:")
    print(df.columns.tolist())

    output_path = save_processed_data(df)

    print(f"\nProcessed dataset saved to:")
    print(output_path)
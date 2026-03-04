import numpy as np
import pandas as pd

from src.config import DATA_DIR, RAW_TRANSACTIONS_CSV


def generate_transactions(n_rows: int = 10000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    customer_id = rng.integers(1000, 6000, size=n_rows)
    merchant_id = rng.integers(1, 500, size=n_rows)
    amount = np.round(np.exp(rng.normal(3.2, 1.0, size=n_rows)), 2)
    channel = rng.choice(["web", "mobile", "pos"], size=n_rows, p=[0.45, 0.35, 0.20])
    card_present = np.where(channel == "pos", 1, rng.choice([0, 1], size=n_rows, p=[0.8, 0.2]))
    hour = rng.integers(0, 24, size=n_rows)

    base_score = (
        (amount > 200).astype(int) * 0.7
        + (channel == "web").astype(int) * 0.4
        + (card_present == 0).astype(int) * 0.4
        + ((hour <= 5) | (hour >= 23)).astype(int) * 0.5
    )
    fraud_probability = 1 / (1 + np.exp(-(base_score - 1.2)))
    is_fraud = rng.binomial(1, fraud_probability)

    now = pd.Timestamp.utcnow().floor("s")
    event_time = [now - pd.Timedelta(minutes=int(m)) for m in rng.integers(0, 60 * 24 * 60, size=n_rows)]

    return pd.DataFrame(
        {
            "transaction_id": np.arange(1, n_rows + 1),
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "amount": amount,
            "channel": channel,
            "card_present": card_present,
            "event_time": event_time,
            "is_fraud": is_fraud,
        }
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_transactions()
    df.to_csv(RAW_TRANSACTIONS_CSV, index=False)
    print(f"Saved {len(df)} rows to {RAW_TRANSACTIONS_CSV}")


if __name__ == "__main__":
    main()

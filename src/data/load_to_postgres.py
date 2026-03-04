import os

import pandas as pd
from sqlalchemy import create_engine

from src.config import RAW_TRANSACTIONS_CSV


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Set DATABASE_URL environment variable before running this script.")

    df = pd.read_csv(RAW_TRANSACTIONS_CSV)
    engine = create_engine(database_url)

    customers = (
        df[["customer_id"]]
        .drop_duplicates()
        .assign(country="US", account_age_days=365, is_vip=False)
    )

    merchants = (
        df[["merchant_id"]]
        .drop_duplicates()
        .assign(merchant_category="general", risk_tier="medium")
    )

    customers.to_sql("customers", engine, if_exists="append", index=False, method="multi")
    merchants.to_sql("merchants", engine, if_exists="append", index=False, method="multi")
    df.to_sql("transactions", engine, if_exists="append", index=False, method="multi")

    print("Loaded customers, merchants, and transactions into Postgres")


if __name__ == "__main__":
    main()

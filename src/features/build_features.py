import pandas as pd


REQUIRED_COLUMNS = [
    "amount",
    "channel",
    "card_present",
    "event_time",
    "is_fraud",
]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data = df.copy()
    data["event_time"] = pd.to_datetime(data["event_time"], utc=True, errors="coerce")
    data["hour"] = data["event_time"].dt.hour.fillna(0).astype(int)
    data["is_night"] = ((data["hour"] <= 5) | (data["hour"] >= 23)).astype(int)

    channel_dummies = pd.get_dummies(data["channel"], prefix="channel", dtype=int)
    feature_df = pd.concat(
        [
            data[["amount", "card_present", "hour", "is_night"]].astype(float),
            channel_dummies,
        ],
        axis=1,
    )

    target = data["is_fraud"].astype(int)
    return feature_df, target

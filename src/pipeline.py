import pandas as pd
import numpy as np
import re

from src.config import TOKYO_LAT, TOKYO_LON

COLUMN_RENAME_MAP = {
    "magnitude": "mag",
    "magnitude_value": "mag",
    "lat": "latitude",
    "latitude_deg": "latitude",
    "lon": "longitude",
    "longitude_deg": "longitude",
    "datetime_utc": "time",
    "date_time_utc": "time",
    "depth_km": "depth",
}


def load_and_merge_datasets(file_paths: dict) -> pd.DataFrame:
    frames = []

    for source_name, path in file_paths.items():
        try:
            df = pd.read_csv(path)
            print(f"Loaded {source_name}: {df.shape[0]} rows, {df.shape[1]} columns.")

            df.columns = df.columns.str.lower()

            df = df.rename(
                columns={
                    c: COLUMN_RENAME_MAP[c]
                    for c in df.columns
                    if c in COLUMN_RENAME_MAP
                }
            )

            df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)

            df["source"] = source_name

            frames.append(df)

        except Exception as e:
            print(f"Error loading {source_name} from {path}: {e}")

    if not frames:
        raise ValueError("No datasets were loaded successfully.")

    merged = pd.concat(frames, ignore_index=True)
    print(f"Total rows after merge: {len(merged)}")
    return merged


def extract_region(place: str) -> str:
    if pd.isna(place):
        return "Unknown"

    place_str = str(place)
    if "of" in place_str:
        place_str = place_str.split("of")[-1].strip()

    for region in [
        "Tokyo",
        "Honshu",
        "Hokkaido",
        "Kyushu",
        "Shikoku",
        "Ryukyu",
        "Kurile",
        "Japan",
    ]:
        if re.search(region, place_str, re.IGNORECASE):
            return region

    return place_str.split(",")[-1].strip()


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
    df["mag"] = pd.to_numeric(df["mag"], errors="coerce")

    df.loc[(df["depth"] < 0) | (df["depth"] > 750), "depth"] = np.nan

    before_drop = len(df)
    df = df.dropna(subset=["time", "latitude", "longitude", "mag"])
    print(f"Rows dropped (missing key fields): {before_drop - len(df)}")

    df["depth"] = df["depth"].fillna(df["depth"].median())

    df["month"] = df["time"].dt.strftime("%m")

    bins = [-np.inf, 4.0, 6.0, np.inf]
    labels = ["weak", "medium", "strong"]
    df["category"] = pd.cut(df["mag"], bins=bins, labels=labels, right=False)

    if "place" in df.columns and "region" in df.columns:
        combined = df["place"].fillna(df["region"])
    elif "place" in df.columns:
        combined = df["place"]
    elif "region" in df.columns:
        combined = df["region"]
    else:
        combined = pd.Series("Unknown", index=df.index)

    df["region"] = combined.apply(extract_region).str.strip().str.title()
    df["region"] = df["region"].replace(
        {
            "Osaka Prefecture": "Osaka",
            "Fukushima Prefecture": "Fukushima",
            "Oita Prefecture": "Oita",
        }
    )

    lats = df["latitude"].to_numpy()
    lons = df["longitude"].to_numpy()
    df["dist_to_tokyo"] = np.sqrt((lats - TOKYO_LAT) ** 2 + (lons - TOKYO_LON) ** 2)

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["time", "latitude", "longitude", "mag"])
    print(f"Duplicates removed: {before_dedup - len(df)} rows")

    print(f"Final shape: {df.shape}")
    return df


def calculate_numpy_stats(df: pd.DataFrame) -> dict:
    mags = df["mag"].to_numpy()
    depths = df["depth"].to_numpy()
    return {
        "mean_magnitude": np.mean(mags),
        "variance_magnitude": np.var(mags),
        "quantile_95_magnitude": np.percentile(mags, 95),
        "mean_depth": np.mean(depths),
        "median_depth": np.median(depths),
    }


def analyze_by_month_category(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["month", "category"], observed=True)
        .size()
        .reset_index(name="count")
    )


def analyze_by_region(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("region")
        .agg(
            count=("mag", "size"),
            avg_magnitude=("mag", "mean"),
            avg_depth=("depth", "mean"),
            max_magnitude=("mag", "max"),
            max_depth=("depth", "max"),
        )
        .reset_index()
    )

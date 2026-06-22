import pytest
import pandas as pd
import numpy as np

from src.database import insert_data_to_db
from src.pipeline import (
    preprocess_data,
    calculate_numpy_stats,
    analyze_by_month_category,
    analyze_by_region,
    extract_region,
    load_and_merge_datasets,
)


def create_data():
    return pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2023-01-15T12:00:00Z",
                    "2023-03-20T08:30:00Z",
                    "2023-07-05T22:00:00Z",
                ],
                utc=True,
            ),
            "latitude": [35.6, 36.2, 34.0],
            "longitude": [139.6, 140.1, 138.0],
            "depth": [10.0, 20.0, 50.0],
            "mag": [3.5, 6.5, 5.0],
            "place": [
                "Tokyo, Japan",
                "Fukushima Prefecture",
                "Hokkaido, Japan",
            ],
        }
    )


def test_preprocess_adds_category():
    df = create_data()

    result = preprocess_data(df)

    assert "category" in result.columns


def test_preprocess_adds_region():
    df = create_data()

    result = preprocess_data(df)

    assert "region" in result.columns


def test_preprocess_adds_month():
    df = create_data()

    result = preprocess_data(df)

    assert "month" in result.columns


def test_depth_null_is_filled():
    df = create_data()
    df.loc[0, "depth"] = np.nan

    result = preprocess_data(df)

    assert result["depth"].isnull().sum() == 0


def test_weak_category():
    df = create_data()

    result = preprocess_data(df)

    category = result.loc[result["mag"] == 3.5, "category"].values[0]

    assert category == "weak"


def test_strong_category():
    df = create_data()

    result = preprocess_data(df)

    category = result.loc[result["mag"] == 6.5, "category"].values[0]

    assert category == "strong"


def test_calculate_stats():
    df = preprocess_data(create_data())

    stats = calculate_numpy_stats(df)

    assert "mean_magnitude" in stats
    assert "mean_depth" in stats


def test_mean_depth_positive():
    df = preprocess_data(create_data())

    stats = calculate_numpy_stats(df)

    assert stats["mean_depth"] > 0


def test_extract_region_tokyo():
    assert extract_region("10km NE of Tokyo, Japan") == "Tokyo"


def test_extract_region_hokkaido():
    assert extract_region("Hokkaido, Japan") == "Hokkaido"


def test_extract_region_unknown():
    assert extract_region(None) == "Unknown"


def test_month_analysis_has_count():
    df = preprocess_data(create_data())

    result = analyze_by_month_category(df)

    assert "count" in result.columns


def test_month_analysis_not_empty():
    df = preprocess_data(create_data())

    result = analyze_by_month_category(df)

    assert len(result) > 0


def test_region_analysis_has_region_column():
    df = preprocess_data(create_data())

    result = analyze_by_region(df)

    assert "region" in result.columns


def test_region_analysis_has_count_column():
    df = preprocess_data(create_data())

    result = analyze_by_region(df)

    assert "count" in result.columns


def test_load_empty_data():
    with pytest.raises(ValueError):
        load_and_merge_datasets({})


def test_load_csv(tmp_path):
    csv = (
        "time,latitude,longitude,depth,mag,place\n"
        "2023-01-01T00:00:00Z,35.0,139.0,10.0,4.0,Tokyo\n"
    )

    file = tmp_path / "test.csv"
    file.write_text(csv)

    result = load_and_merge_datasets({"TEST": str(file)})

    assert len(result) == 1


def test_source_column_exists(tmp_path):
    csv = (
        "time,latitude,longitude,depth,mag,place\n"
        "2023-01-01T00:00:00Z,35.0,139.0,10.0,4.0,Tokyo\n"
    )

    file = tmp_path / "test.csv"
    file.write_text(csv)

    result = load_and_merge_datasets({"TEST": str(file)})

    assert "source" in result.columns


def test_insert_dataframe():
    df = pd.DataFrame(
        {
            "time": ["2023-01-01"],
            "latitude": [35.0],
            "longitude": [139.0],
            "depth": [10.0],
            "mag": [4.0],
        }
    )

    try:
        insert_data_to_db(df, "earthquakes")
        assert True
    except Exception:
        assert False


def test_insert_empty_dataframe():
    df = pd.DataFrame(
        columns=[
            "time",
            "latitude",
            "longitude",
            "depth",
            "mag",
        ]
    )

    try:
        insert_data_to_db(df, "earthquakes")
        assert True
    except Exception:
        assert False

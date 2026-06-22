import os
import pandas as pd
from sqlalchemy import text

from src.database import (
    init_database,
    insert_data_to_db,
    run_analytical_queries,
    get_engine,
)
from src.pipeline import (
    analyze_by_month_category,
    analyze_by_region,
    load_and_merge_datasets,
    preprocess_data,
    calculate_numpy_stats,
)
from src.visualizer import generate_plots
from src.config import OUTPUT_DIR


def main():
    print("--- Starting Japan Earthquake Analysis System ---")

    file_paths = {
        "USGS": "data/JAPAN_USGS.csv",
        "GEOFON": "data/JAPAN_GEOFON.csv",
        "EMSC": "data/JAPAN_EMSC.csv",
        "DATASET": "data/JAPAN_DATASET.csv",
    }

    missing = [p for p in file_paths.values() if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"Missing data files: {missing}")

    raw_df = load_and_merge_datasets(file_paths)
    processed_df = preprocess_data(raw_df)

    print("\n--- Monthly Category Analysis ---")
    print(analyze_by_month_category(processed_df).to_string(index=False))

    print("\n--- Regional Analysis ---")
    print(analyze_by_region(processed_df).to_string(index=False))

    print(f"Data integrated and processed successfully. Shape: {processed_df.shape}")
    stats = calculate_numpy_stats(processed_df)

    print("\n--- NumPy Statistical Summary ---")
    for key, value in stats.items():
        print(f"{key}: {value:.4f}")

    init_database()

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE earthquakes;"))

    insert_data_to_db(processed_df, table_name="earthquakes")

    run_analytical_queries()

    generate_plots(processed_df, OUTPUT_DIR)

    print("\n--- Process Completed Successfully! ---")


if __name__ == "__main__":
    main()

from sqlalchemy import create_engine, text
import pandas as pd

from src.config import DATABASE_URL


def get_engine():
    return create_engine(DATABASE_URL)


def init_database():
    engine = get_engine()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS earthquakes (
        id SERIAL PRIMARY KEY,
        time TIMESTAMP WITH TIME ZONE,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        depth DOUBLE PRECISION,
        mag DOUBLE PRECISION,
        category VARCHAR(50),
        region VARCHAR(255),
        dist_to_tokyo DOUBLE PRECISION,
        source VARCHAR(100)
    );
    """

    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_earthquakes_region ON earthquakes(region);",
        "CREATE INDEX IF NOT EXISTS idx_earthquakes_time ON earthquakes(time);",
        "CREATE INDEX IF NOT EXISTS idx_earthquakes_mag ON earthquakes(mag);",
    ]

    with engine.begin() as conn:
        conn.execute(text(create_table_query))
        for q in index_queries:
            conn.execute(text(q))

    print("Database and indexes initialized successfully in PostgreSQL.")


def insert_data_to_db(df: pd.DataFrame, table_name: str = "earthquakes"):
    engine = get_engine()

    allowed_columns = [
        "time",
        "latitude",
        "longitude",
        "depth",
        "mag",
        "category",
        "region",
        "dist_to_tokyo",
        "source",
    ]

    columns_to_keep = [col for col in allowed_columns if col in df.columns]

    final_df = df[columns_to_keep].copy()
    final_df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000,
        method="multi",
    )

    print(f"Successfully inserted {len(final_df)} records...")


def run_analytical_queries():
    engine = get_engine()

    with engine.connect() as conn:
        print("\n--- Total Earthquakes by Region & Month ---")
        q1 = """
        SELECT region, TO_CHAR(time, 'MM') as month, COUNT(*) as count
        FROM earthquakes
        GROUP BY region, month
        ORDER BY count DESC, region ASC
        LIMIT 10;
        """
        df1 = pd.read_sql_query(q1, conn)
        print(df1.to_string(index=False))

        print("\n--- Average Magnitude by Region & Source ---")
        q2 = """
        SELECT region, source, AVG(mag) as avg_mag
        FROM earthquakes
        GROUP BY region, source
        ORDER BY avg_mag DESC
        LIMIT 10;
        """
        df2 = pd.read_sql_query(q2, conn)
        print(df2.to_string(index=False))

        print("\n--- Top 10 Strongest Recent Earthquakes ---")
        q3 = """
        SELECT time, region, mag as magnitude, depth, source
        FROM earthquakes
        ORDER BY mag DESC, time DESC
        LIMIT 10;
        """
        df3 = pd.read_sql_query(q3, conn)
        print(df3.to_string(index=False))

        print("\n--- Max and Min Depth by Region ---")
        q4 = """
        SELECT region, MAX(depth) as max_depth, MIN(depth) as min_depth
        FROM earthquakes
        GROUP BY region
        ORDER BY region ASC
        LIMIT 10;
        """
        df4 = pd.read_sql_query(q4, conn)
        print(df4.to_string(index=False))

        return {"by_region_month": df1, "avg_mag": df2, "top10": df3, "depth": df4}

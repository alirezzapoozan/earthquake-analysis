# Japan Earthquake Analysis System

A comprehensive data engineering and analysis pipeline for seismic activity in Japan. This project collects earthquake data from multiple international sources, processes and stores it in a PostgreSQL database, performs statistical analysis using Pandas and NumPy, and generates visualizations to surface patterns and insights.

---

## Project Structure

```
earthquake-beta/
├── data/
│   ├── JAPAN_USGS.csv        # Data from USGS REST API
│   ├── JAPAN_GEOFON.csv      # Data scraped from GEOFON (GFZ Germany)
│   ├── JAPAN_EMSC.csv        # Data scraped from EMSC (Europe-Mediterranean)
│   └── JAPAN_DATASET.csv     # Reference offline historical dataset
├── src/
│   ├── __init__.py
│   ├── config.py             # Environment variables & constants
│   ├── pipeline.py           # Data loading, preprocessing, NumPy stats
│   ├── database.py           # PostgreSQL init, insert, and SQL queries
│   └── visualizer.py         # Matplotlib/Seaborn chart generation
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py      # Unit tests for the preprocessing pipeline
├── outputs/                  # Generated plots (created at runtime)
├── main.py                   # Entrypoint — runs the full pipeline
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Data Sources

| Source | Organization | Collection Method | Output File |
|---|---|---|---|
| **USGS** | US Geological Survey | RESTful API via `requests` | `JAPAN_USGS.csv` |
| **GEOFON** | GFZ Germany | HTML web scraping via `BeautifulSoup` | `JAPAN_GEOFON.csv` |
| **EMSC** | Euro-Mediterranean Seismological Centre | Dynamic scraping via `Selenium` | `JAPAN_EMSC.csv` |
| **DATASET** | Reference dataset | Pre-collected offline CSV | `JAPAN_DATASET.csv` |

---

## How It Works

The pipeline runs in five sequential stages:

### 1. Data Ingestion & Merging
All four CSV files are loaded with Pandas. Column names are normalized across sources (e.g. `magnitude`, `magnitude_value`, `lat`, `latitude_deg` all become `mag` and `latitude`). A `source` column is added to track the origin of each record, and all frames are concatenated into a single DataFrame.

### 2. Preprocessing & Feature Engineering
- Numeric columns (`latitude`, `longitude`, `depth`, `mag`) are coerced to `float`
- Timestamps are parsed to UTC-aware `datetime`
- Rows missing `time`, `latitude`, `longitude`, or `mag` are dropped
- Out-of-range depths (< 0 or > 750 km) are nulled and filled with the median
- Duplicates (same time + coordinates + magnitude) are removed
- Three new columns are engineered:
  - `month` — extracted from the timestamp
  - `category` — `weak` (mag < 4), `medium` (4–6), `strong` (> 6)
  - `region` — extracted from the `place` field using regex matching
  - `dist_to_tokyo` — Euclidean distance from Tokyo (35.6762°N, 139.6503°E) computed with NumPy vectorization

### 3. NumPy Statistical Analysis
Key statistics computed without Python loops using vectorized NumPy operations:
- Mean and variance of magnitude
- 95th percentile magnitude
- Mean and median depth

### 4. PostgreSQL Storage & SQL Queries
Processed data is inserted into a `earthquakes` table in PostgreSQL using SQLAlchemy with `chunksize=1000`. Indexes are created on `region`, `time`, and `mag` for fast queries. Four analytical SQL queries are then executed:
- Total earthquakes by region and month
- Average magnitude by region and source
- Top 10 strongest recent earthquakes
- Max and min depth per region

### 5. Visualization
Five plots are saved to the `outputs/` directory:

| File | Chart Type | What It Shows |
|---|---|---|
| `01_magnitude_distribution.png` | Histogram | Magnitude distribution per source |
| `02_weekly_trend.png` | Dual-axis Line | Weekly earthquake count and average magnitude |
| `03_scatter_depth_vs_mag.png` | Scatter | Depth vs. magnitude, colored by category |
| `04_boxplot_depth_by_categories.png` | Boxen Plot | Depth spread across weak/medium/strong categories |
| `05_earthquake_heatmap_geo_and_distance.png` | Heatmap | Correlation matrix of all numeric features with highlighting Tokyo distance |

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (running locally or remotely)

### 1. Clone the repository
```bash
git clone https://github.com/jananfar/earthquake-analysis.git
cd earthquake-analysis
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Then open `.env` and fill in your PostgreSQL credentials:
```env
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=japan_earthquakes
```

### 5. Create the database
```bash
psql -U postgres -c "CREATE DATABASE japan_earthquakes;"
```

### 6. Run the pipeline
```bash
python main.py
```

---

## Running Tests

```bash
pytest tests/
```

The test suite covers:
- Row count after preprocessing (rows with null key fields are correctly dropped)
- Null handling (depth nulls are filled, no nulls remain in key columns)
- Category assignment (`mag=3.5` → `weak`, `mag=6.5` → `strong`)
- Region extraction and normalization (`"Fukushima Prefecture"` → `"Fukushima"`)
- Presence and float dtype of the `dist_to_tokyo` column

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `pandas` | 3.0.3 | Data loading, merging, feature engineering |
| `numpy` | 2.4.6 | Vectorized statistical calculations |
| `sqlalchemy` | 2.0.49 | Database ORM and connection management |
| `psycopg2-binary` | 2.9.12 | PostgreSQL driver |
| `matplotlib` | 3.10.9 | Base plotting |
| `seaborn` | 0.13.2 | Statistical visualizations |
| `python-dotenv` | 1.2.2 | `.env` file loading |
| `pytest` | 9.0.3 | Unit testing framework |

---

## Database Schema

```sql
CREATE TABLE earthquakes (
    id              SERIAL PRIMARY KEY,
    time            TIMESTAMP WITH TIME ZONE,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    depth           DOUBLE PRECISION,
    mag             DOUBLE PRECISION,
    category        VARCHAR(50),
    region          VARCHAR(255),
    dist_to_tokyo   DOUBLE PRECISION,
    source          VARCHAR(100)
);

CREATE INDEX idx_earthquakes_region ON earthquakes(region);
CREATE INDEX idx_earthquakes_time   ON earthquakes(time);
CREATE INDEX idx_earthquakes_mag    ON earthquakes(mag);
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASS` | *(required)* | PostgreSQL password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `japan_earthquakes` | Database name |

> **Note:** The application will raise a clear `EnvironmentError` at startup if `DB_PASS` is not set.

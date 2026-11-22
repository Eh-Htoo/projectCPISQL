
import os
import sys

import mysql.connector
import requests
from dotenv import load_dotenv

load_dotenv()

SERIES_ID = "CPIAUCNS"
FRED_URL = "https://api.stlouisfed.org/fred"


def fred_get(endpoint, **params):
    """Call a FRED endpoint and return the parsed JSON."""
    params.update(
        series_id=SERIES_ID,
        api_key=os.environ["FRED_API_KEY"],
        file_type="json",
    )
    resp = requests.get(f"{FRED_URL}/{endpoint}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_series_info():
    return fred_get("series")["seriess"][0]


def fetch_observations():
    rows = []
    for obs in fred_get("series/observations")["observations"]:
        # FRED uses "." for missing values; skip those.
        if obs["value"] == ".":
            continue
        rows.append((SERIES_ID, obs["date"], obs["value"]))
    return rows


def main():
    info = fetch_series_info()
    rows = fetch_observations()
    print(f"Fetched {len(rows)} observations for {SERIES_ID}")

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )
    cur = conn.cursor()
    try:
        # The series row must exist first (observations has a foreign key to it).
        cur.execute(
            """
            INSERT INTO series (series_id, title, units, frequency, last_synced_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                units = VALUES(units),
                frequency = VALUES(frequency),
                last_synced_at = NOW()
            """,
            (SERIES_ID, info["title"], info["units"], info["frequency"]),
        )

        # Upsert every observation in one batch.
        cur.executemany(
            """
            INSERT INTO observations (series_id, obs_date, value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
            """,
            rows,
        )
        conn.commit()
        print("Sync complete.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        sys.exit(f"Missing environment variable: {e}")
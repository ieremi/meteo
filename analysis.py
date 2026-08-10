import argparse
import calendar
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests


parser = argparse.ArgumentParser()

parser.add_argument("year1", type=int)
parser.add_argument("year2", type=int)

parser.add_argument(
    "--month",
    type=int,
    choices=range(1, 13),
)

args = parser.parse_args()


URL = "https://archive-api.open-meteo.com/v1/archive"

LATITUDE = 34.98
LONGITUDE = 138.38

OUTPUT_DIR = Path("/app/output")
DB_PATH = Path("/app/data/weather.db")

def init_db():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_weather (
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                date TEXT NOT NULL,
                mean_temperature REAL,
                PRIMARY KEY (
                    latitude,
                    longitude,
                    date
                )
            )
        """)

def load_temperature_from_db(start_date, end_date):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT
                date,
                mean_temperature AS temperature
            FROM daily_weather
            WHERE latitude = ?
              AND longitude = ?
              AND date BETWEEN ? AND ?
            ORDER BY date
            """,
            conn,
            params=(
                LATITUDE,
                LONGITUDE,
                start_date,
                end_date,
            ),
            parse_dates=["date"],
        )

def save_temperature_to_db(df):
    rows = [
        (
            LATITUDE,
            LONGITUDE,
            row.date.strftime("%Y-%m-%d"),
            row.temperature,
        )
        for row in df.itertuples(index=False)
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO daily_weather (
                latitude,
                longitude,
                date,
                mean_temperature
            )
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )

def get_temperature(year, month=None):
    if month is None:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    else:
        last_day = calendar.monthrange(year, month)[1]

        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day:02d}"

    cached = load_temperature_from_db(
        start_date,
        end_date,
    )

    expected_days = (
        pd.Timestamp(end_date)
        - pd.Timestamp(start_date)
    ).days + 1

    if len(cached) == expected_days:
        print(
            f"cache hit: {start_date} .. {end_date}"
        )
        return cached

    print(
        f"API fetch: {start_date} .. {end_date}"
    )

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean",
        "timezone": "Asia/Tokyo",
    }

    response = requests.get(
        URL,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()["daily"]

    df = pd.DataFrame({
        "date": pd.to_datetime(data["time"]),
        "temperature": data["temperature_2m_mean"],
    })

    save_temperature_to_db(df)

    return df

init_db()

weather_1 = get_temperature(
    args.year1,
    args.month,
)

weather_2 = get_temperature(
    args.year2,
    args.month,
)

weather_1["date_key"] = weather_1["date"].dt.strftime("%m-%d")
weather_2["date_key"] = weather_2["date"].dt.strftime("%m-%d")

comparison = pd.merge(
    weather_1[["date_key", "temperature"]],
    weather_2[["date_key", "temperature"]],
    on="date_key",
    how="inner",
    suffixes=(
        f"_{args.year1}",
        f"_{args.year2}",
    ),
)

comparison = comparison.rename(columns={
    "date_key": "date",
    f"temperature_{args.year1}": str(args.year1),
    f"temperature_{args.year2}": str(args.year2),
})

comparison["difference"] = (
    comparison[str(args.year2)]
    - comparison[str(args.year1)]
)


x = np.arange(len(comparison))


if args.month is None:
    tick_positions = comparison[
        comparison["date"].str.endswith("-01")
    ].index

    tick_labels = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec",
    ]

    title_period = "Full Year"

else:
    tick_positions = x
    tick_labels = np.arange(1, len(comparison) + 1)

    title_period = calendar.month_name[args.month]


print(comparison)

print()
print(
    f"{args.year1} mean:",
    comparison[str(args.year1)].mean(),
)

print(
    f"{args.year2} mean:",
    comparison[str(args.year2)].mean(),
)

print(
    "difference:",
    comparison["difference"].mean(),
)


plt.figure(figsize=(12, 5))

plt.xticks(
    tick_positions,
    tick_labels,
)

plt.plot(
    x,
    comparison[str(args.year1)],
    label=str(args.year1),
    color="#00205B",
)

plt.plot(
    x,
    comparison[str(args.year2)],
    label=str(args.year2),
    color="#0B8BEE",
)

plt.xlabel(
    "Month" if args.month is None else "Day"
)

plt.ylabel("Mean temperature (°C)")

plt.title(
    f"Shizuoka — {title_period} Mean Temperature"
)

plt.legend()
plt.grid()


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


if args.month is None:
    period_name = "year"
else:
    period_name = f"{args.month:02d}"


output_file = (
    OUTPUT_DIR
    / f"temperature-{args.year1}-{args.year2}-{period_name}.png"
)

plt.savefig(
    output_file,
    dpi=150,
    bbox_inches="tight",
)

plt.close()

print(f"saved: {output_file}")
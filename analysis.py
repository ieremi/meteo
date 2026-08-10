import argparse
import calendar
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


def get_temperature(year, month=None):
    if month is None:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    else:
        last_day = calendar.monthrange(year, month)[1]

        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day:02d}"

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

    return pd.DataFrame({
        "date": pd.to_datetime(data["time"]),
        "temperature": data["temperature_2m_mean"],
    })


weather_1 = get_temperature(
    args.year1,
    args.month,
)

weather_2 = get_temperature(
    args.year2,
    args.month,
)


comparison = pd.DataFrame({
    "date": weather_1["date"].dt.strftime("%m-%d"),
    str(args.year1): weather_1["temperature"].to_numpy(),
    str(args.year2): weather_2["temperature"].to_numpy(),
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
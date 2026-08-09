import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


URL = "https://archive-api.open-meteo.com/v1/archive"

LATITUDE = 34.98
LONGITUDE = 138.38


def get_temperature(year):
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": f"{year}-08-01",
        "end_date": f"{year}-08-31",
        "daily": "temperature_2m_max",
        "timezone": "Asia/Tokyo",
    }

    response = requests.get(URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()["daily"]

    return pd.DataFrame({
        "date": pd.to_datetime(data["time"]),
        "temperature": data["temperature_2m_max"],
    })


weather_1997 = get_temperature(1997)
weather_2025 = get_temperature(2025)

comparison = pd.DataFrame({
    "day": np.arange(1, 32),
    "1997": weather_1997["temperature"].to_numpy(),
    "2025": weather_2025["temperature"].to_numpy(),
})

comparison["difference"] = (
    comparison["2025"] - comparison["1997"]
)

print(comparison)

print()
print("1997 mean:", comparison["1997"].mean())
print("2025 mean:", comparison["2025"].mean())
print("difference:", comparison["difference"].mean())

plt.figure(figsize=(10, 5))

plt.plot(
    comparison["day"],
    comparison["1997"],
    label="1997",
    color="#00205B"
)

plt.plot(
    comparison["day"],
    comparison["2025"],
    label="2025",
    color="#0B8BEE"
)

plt.xlabel("Day")
plt.ylabel("Max temperature (°C)")
plt.title("Shizuoka — August Max Temperature")
plt.legend()
plt.grid()

from pathlib import Path

output_dir = Path("/app/output")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "temperature.png"

plt.savefig(output_file)

print(f"saved: {output_file}")
import requests
import os
import math

# ── Route coordinates ──────────────────────────────────────────────────────────
# Dover Blk 28:  1.3115, 103.7784
# Fairfield Methodist Primary: 1.3075, 103.7798
# Galaxis (one-north):         1.2993, 103.7877
#
# We check all 3 points and alert if ANY of them expects rain.
ROUTE_POINTS = [
    ("Dover Blk 28",             1.3115, 103.7784),
    ("Fairfield Methodist area", 1.3075, 103.7798),
    ("Galaxis / one-north",      1.2993, 103.7877),
]

RAIN_KEYWORDS = [
    "Thundery Showers",
    "Heavy Thundery Showers",
    "Heavy Rain",
    "Moderate Rain",
    "Light Rain",
    "Showers",
    "Passing Showers",
    "Heavy Showers",
]

def haversine(lat1, lon1, lat2, lon2):
    """Straight-line distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def nearest_area(lat, lon, area_metadata):
    """Return the NEA area name closest to the given coordinates."""
    return min(
        area_metadata,
        key=lambda a: haversine(lat, lon, a['label_location']['latitude'], a['label_location']['longitude'])
    )['name']

def classify_rain(forecast: str) -> str | None:
    """Return a severity label, or None if no rain expected."""
    f = forecast.lower()
    if "heavy thundery" in f:
        return "⛈️ HEAVY THUNDERY SHOWERS"
    if "thundery" in f:
        return "⛈️ Thundery Showers"
    if "heavy rain" in f or "heavy shower" in f:
        return "🌧️ Heavy Rain"
    if "moderate rain" in f:
        return "🌧️ Moderate Rain"
    if "light rain" in f:
        return "🌦️ Light Rain"
    if "shower" in f or "rain" in f:
        return "🌦️ Showers"
    return None  # no rain

def check_weather():
    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    data = requests.get(url, timeout=10).json()

    area_metadata = data['area_metadata']
    forecasts_by_area = {
        f['area']: f['forecast']
        for f in data['items'][0]['forecasts']
    }

    rain_alerts = []

    for point_name, lat, lon in ROUTE_POINTS:
        area = nearest_area(lat, lon, area_metadata)
        forecast = forecasts_by_area.get(area, "Unknown")
        severity = classify_rain(forecast)

        if severity:
            rain_alerts.append(f"  • {point_name} ({area}): {severity}")

    if rain_alerts:
        alert_lines = "\n".join(rain_alerts)
        msg = (
            f"🌧️ Rain Alert for your 10pm walk!\n"
            f"Dover Blk 28 → Galaxis via Fairfield Methodist\n\n"
            f"{alert_lines}\n\n"
            f"Bring your umbrella! ☂️"
        )
    else:
        msg = (
            f"✅ All clear for your 10pm walk!\n"
            f"Dover Blk 28 → Galaxis via Fairfield Methodist\n"
            f"No rain expected along the route."
        )

    send_telegram(msg)

def send_telegram(message):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)

if __name__ == "__main__":
    check_weather()

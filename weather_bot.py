import requests
import os
import math
import sys
from datetime import datetime, timezone, timedelta

SGT = timezone(timedelta(hours=8))

ROUTE_POINTS = [
    ("Dover Blk 28",             1.3115, 103.7784),
    ("Fairfield Methodist area", 1.3075, 103.7798),
    ("Galaxis / one-north",      1.2993, 103.7877),
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def nearest_area(lat, lon, area_metadata):
    return min(
        area_metadata,
        key=lambda a: haversine(lat, lon,
                                a['label_location']['latitude'],
                                a['label_location']['longitude'])
    )['name']

def classify_rain(forecast: str) -> str | None:
    f = forecast.lower()
    if "heavy thundery" in f:        return "⛈️ Heavy Thundery Showers"
    if "thundery" in f:              return "⛈️ Thundery Showers"
    if "heavy rain" in f:            return "🌧️ Heavy Rain"
    if "heavy shower" in f:          return "🌧️ Heavy Showers"
    if "moderate rain" in f:         return "🌧️ Moderate Rain"
    if "light rain" in f:            return "🌦️ Light Rain"
    if "shower" in f or "rain" in f: return "🌦️ Showers"
    return None

def fetch_2hr_forecast_at(dt_sgt: datetime) -> dict:
    dt_str = dt_sgt.strftime("%Y-%m-%dT%H:%M:%S")
    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    resp = requests.get(url, params={"date_time": dt_str}, timeout=10).json()
    return {
        "area_metadata": resp['area_metadata'],
        "forecasts": {f['area']: f['forecast'] for f in resp['items'][0]['forecasts']},
    }

def fetch_24hr_forecast() -> dict:
    """Returns the general and period forecasts from the 24-hour API."""
    url = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
    resp = requests.get(url, timeout=10).json()
    return resp['items'][0]

def check_slot_2hr(dt_sgt: datetime) -> list[str]:
    data = fetch_2hr_forecast_at(dt_sgt)
    lines = []
    for point_name, lat, lon in ROUTE_POINTS:
        area = nearest_area(lat, lon, data['area_metadata'])
        forecast = data['forecasts'].get(area, "Unknown")
        severity = classify_rain(forecast)
        if severity:
            lines.append(f"  • {point_name}: {severity}")
    return lines

def check_evening_24hr() -> list[str]:
    """
    Uses the 24-hour forecast and finds the period covering 6:30pm.
    The 24hr API returns periods like 'afternoon' (12pm-6pm) and 'night' (6pm-midnight).
    We pick whichever period covers 18:30.
    """
    data = fetch_24hr_forecast()
    lines = []

    # Find the period that covers 6:30pm (18:30)
    target_hour = 18
    best_period = None
    for period in data.get('periods', []):
        start = int(period['time']['start'][11:13])
        end   = int(period['time']['end'][11:13])
        # handle overnight periods (e.g. end=00 means midnight)
        end = end if end != 0 else 24
        if start <= target_hour < end:
            best_period = period
            break

    if not best_period:
        # fallback: just use general forecast
        general = data.get('general', {})
        forecast_text = general.get('forecast', '')
        severity = classify_rain(forecast_text)
        if severity:
            lines.append(f"  • Along route: {severity}")
        return lines

    # The 24hr API gives forecasts per region (west, east, central, etc.)
    # Your route is in the WEST region
    regions = best_period.get('regions', {})
    west_forecast = regions.get('west', '')
    severity = classify_rain(west_forecast)
    if severity:
        lines.append(f"  • West region (your route): {severity}")

    return lines

def send_telegram(message: str):
    token   = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": message},
        timeout=10,
    )

def run_morning():
    today = datetime.now(SGT).date()
    slot_930am = datetime(today.year, today.month, today.day, 9, 30, tzinfo=SGT)

    morning_alerts = check_slot_2hr(slot_930am)
    evening_alerts = check_evening_24hr()

    # --- Morning section ---
    if morning_alerts:
        morning_section = (
            "🌅 Morning Walk (9:30–10am)\n"
            "Dover Blk 28 → Galaxis via Fairfield Methodist\n"
            + "\n".join(morning_alerts)
            + "\n☂️ Bring your umbrella!"
        )
    else:
        morning_section = (
            "🌅 Morning Walk (9:30–10am)\n"
            "Dover Blk 28 → Galaxis via Fairfield Methodist\n"
            "✅ All clear, no rain expected."
        )

    # --- Evening section ---
    if evening_alerts:
        evening_section = (
            "🌆 Evening Walk (6:30–7pm)\n"
            "Galaxis → Dover Blk 28 via Fairfield Methodist\n"
            + "\n".join(evening_alerts)
            + "\n☂️ Bring your umbrella!"
        )
    else:
        evening_section = (
            "🌆 Evening Walk (6:30–7pm)\n"
            "Galaxis → Dover Blk 28 via Fairfield Methodist\n"
            "✅ All clear, no rain expected."
        )

    msg = f"☀️ Good morning! Here's your walk forecast:\n\n{morning_section}\n\n{evening_section}"
    send_telegram(msg)

if __name__ == "__main__":
    run_morning()

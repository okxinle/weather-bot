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
    if "heavy thundery" in f:       return "⛈️ Heavy Thundery Showers"
    if "thundery" in f:             return "⛈️ Thundery Showers"
    if "heavy rain" in f:           return "🌧️ Heavy Rain"
    if "heavy shower" in f:         return "🌧️ Heavy Showers"
    if "moderate rain" in f:        return "🌧️ Moderate Rain"
    if "light rain" in f:           return "🌦️ Light Rain"
    if "shower" in f or "rain" in f: return "🌦️ Showers"
    return None

def fetch_forecast_at(dt_sgt: datetime) -> dict:
    dt_str = dt_sgt.strftime("%Y-%m-%dT%H:%M:%S")
    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    resp = requests.get(url, params={"date_time": dt_str}, timeout=10).json()
    area_metadata = resp['area_metadata']
    forecasts_by_area = {f['area']: f['forecast'] for f in resp['items'][0]['forecasts']}
    valid_start = resp['items'][0]['valid_period']['start'][11:16]
    valid_end   = resp['items'][0]['valid_period']['end'][11:16]
    return {
        "area_metadata": area_metadata,
        "forecasts": forecasts_by_area,
        "window": f"{valid_start}–{valid_end}",
    }

def check_slot(label: str, dt_sgt: datetime) -> list[str]:
    data = fetch_forecast_at(dt_sgt)
    lines = []
    for point_name, lat, lon in ROUTE_POINTS:
        area = nearest_area(lat, lon, data['area_metadata'])
        forecast = data['forecasts'].get(area, "Unknown")
        severity = classify_rain(forecast)
        if severity:
            lines.append(f"  • {point_name}: {severity}")
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
    alerts = check_slot("9:30–10am", slot_930am)

    if alerts:
        msg = (
            "🌧️ Morning Walk Alert!\n"
            "Dover Blk 28 → Galaxis via Fairfield Methodist\n\n"
            "🕘 9:30–10am window:\n"
            + "\n".join(alerts)
            + "\n\nBring your umbrella! ☂️"
        )
    else:
        msg = (
            "✅ Morning walk looks clear!\n"
            "Dover Blk 28 → Galaxis via Fairfield Methodist\n"
            "No rain expected at 9:30am. 🌤️"
        )
    send_telegram(msg)

def run_evening():
    today = datetime.now(SGT).date()
    slot_630pm = datetime(today.year, today.month, today.day, 18, 30, tzinfo=SGT)
    alerts = check_slot("6:30–7pm", slot_630pm)

    if alerts:
        msg = (
            "🌧️ Evening Walk Alert!\n"
            "Galaxis → Dover Blk 28 via Fairfield Methodist\n\n"
            "🕡 6:30–7pm window:\n"
            + "\n".join(alerts)
            + "\n\nBring your umbrella! ☂️"
        )
    else:
        msg = (
            "✅ Evening walk looks clear!\n"
            "Galaxis → Dover Blk 28 via Fairfield Methodist\n"
            "No rain expected at 6:30pm. 🌤️"
        )
    send_telegram(msg)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if mode == "evening":
        run_evening()
    else:
        run_morning()

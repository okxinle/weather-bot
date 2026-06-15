import requests
import os

def check_weather():
    # NEA API endpoint
    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    response = requests.get(url).json()
    
    # NEA data is grouped by area. 
    # 'Clementi' is a good proxy for the Dover-Galaxis route.
    target_area = "Clementi"
    forecast = ""
    
    for item in response['items'][0]['forecasts']:
        if item['area'] == target_area:
            forecast = item['forecast']
            break
            
    # Trigger Alert
    heavy_rain_keywords = ["Heavy Rain", "Thundery Showers", "Showers"]
    if any(k in forecast for k in heavy_rain_keywords):
        send_telegram(f"⚠️ Alert: {forecast} in {target_area}! Pack your umbrella.")

def send_telegram(message):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

if __name__ == "__main__":
    check_weather()

import requests

TOKEN = "8939493222:AAHH6icfdeq3oLYDYoIX2ZWdmaoayjWHP9s" 
CHAT_ID = "451385860" 

def check_weather():
    # NEA API for 2-hour forecast
    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    response = requests.get(url).json()
    
    # Check Clementi area
    for item in response['items'][0]['forecasts']:
        if item['area'] == 'Clementi':
            forecast = item['forecast']
            # Alert for heavy rain
            if "Heavy Rain" in forecast or "Thundery Showers" in forecast:
                send_msg(f"⚠️ {forecast} in Clementi! Leave for office earlier.")

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

if __name__ == "__main__":
    check_weather()
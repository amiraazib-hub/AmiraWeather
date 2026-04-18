import requests

class WeatherEngine:
    def __init__(self):
        self.base_url = "http://wttr.in/"

    def get_weather(self, city):
        try:
            # We add format=j1 to get detailed JSON data
            response = requests.get(f"{self.base_url}{city}?format=j1")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "City not found"}
        except Exception as e:
            return {"error": str(e)}

import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed; set env vars manually

API_KEY = os.getenv("OPENWEATHER_API_KEY", "REMOVED_SECRET")
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def fetch_weather_data(city_name):
    """
    Fetch real-time weather data for a given city or district using OpenWeather API.

    Args:
        city_name (str): The name of the city or district.

    Returns:
        dict: A dictionary containing temperature, humidity, and rainfall_estimate.
              rainfall_estimate is converted from 1h reading to a monthly approximation
              using: rainfall_estimate = rainfall_1h * 24 * 30
              If an error occurs, returns a dictionary with an 'error' key.
    """
    if not city_name:
        return {"error": "City or district name is required."}

    params = {
        "q": city_name,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            temperature = data.get("main", {}).get("temp")
            humidity = data.get("main", {}).get("humidity")

            # OpenWeather returns 1-hour rainfall in mm — convert to a monthly
            # rainfall estimate so the ML model receives a realistic annual-scale value.
            # Formula: rainfall_1h * 24 hours * 30 days = monthly approximation
            rain_data = data.get("rain", {})
            rainfall_1h = rain_data.get("1h", 0.0) if rain_data else 0.0
            rainfall_estimate = rainfall_1h * 24 * 30  # mm/month approximation

            return {
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall_estimate  # Callers use this as monthly/annual proxy
            }
        else:
            return {
                "error": f"API request failed with status code {response.status_code}",
                "message": response.json().get("message", "Unknown error")
            }

    except requests.exceptions.Timeout:
        return {"error": "Connection to the weather API timed out."}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to the weather API. Check your internet connection."}
    except requests.exceptions.RequestException as e:
        return {"error": f"An unexpected error occurred during the API request: {e}"}

if __name__ == "__main__":
    city = "Thanjavur"
    print(f"Fetching weather for: {city}...")
    result = fetch_weather_data(city)
    print("Result:", result)

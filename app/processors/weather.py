import requests
from datetime import datetime, timedelta
from typing import Dict, List

WEATHER_CACHE = {}

def convert_date_format(date_str, from_fmt, to_fmt):
    """Convert date format"""
    return datetime.strptime(date_str, from_fmt).strftime(to_fmt)

def fetch_weather(dates: List[str], lat: float, lon: float):
    """Fetch weather data from Open-Meteo API"""
    try:
        if not dates:
            return {}
        
        date_objs = [datetime.strptime(d, "%m/%d/%Y") for d in dates]
        start_date = min(date_objs).strftime("%Y-%m-%d")
        end_date = max(date_objs).strftime("%Y-%m-%d")
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,cloudcover,shortwave_radiation_sum",
            "timezone": "America/New_York"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        weather_data = {}
        if "daily" in data:
            for i, date_str in enumerate(data["daily"]["time"]):
                mdy_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
                if mdy_date in dates:
                    weather_data[mdy_date] = {
                        "high": data["daily"]["temperature_2m_max"][i],
                        "low": data["daily"]["temperature_2m_min"][i],
                        "rain": data["daily"]["precipitation_sum"][i] / 25.4,  # mm to inches
                        "cloud": data["daily"]["cloudcover"][i],
                        "solar": data["daily"]["shortwave_radiation_sum"][i]
                    }
        
        return weather_data
    except Exception as e:
        print(f"Weather API error: {e}")
        return {}

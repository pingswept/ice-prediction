import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
	"latitude": 43.732,
	"longitude": -71.5884,
	"start_date": "2024-11-01",
	"end_date": "2025-01-15",
	"hourly": ["temperature_2m", "snow_depth"],
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_snow_depth = hourly.Variables(1).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

def stefan(row):
    if row["degree_days"] > 0:
        return 0
    else:
        return 0.035 * (-1 * row["degree_days"]) ** 0.5

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["snow_depth"] = hourly_snow_depth

hourly_data["degree_days"] = (hourly_data["temperature_2m"]/24).cumsum()

hourly_dataframe = pd.DataFrame(data = hourly_data)
hourly_dataframe["ice_thickness_m"] = hourly_dataframe.apply(stefan, axis=1)
hourly_dataframe["ice_thickness_in"] = hourly_dataframe["ice_thickness_m"] * 39.37008

print("\nHourly data\n", hourly_dataframe)

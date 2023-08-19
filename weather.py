import json
import sys
import time
from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
from datetime import datetime
from pprint import pp
from urllib import error, parse, request

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
PADDING = 20


def parse_args() -> Namespace:
    """Handle CLI arguments."""
    parser = ArgumentParser(
        description='Gets weather forcast and temperature for a given city.'
    )
    parser.add_argument(
        'city', nargs='+', type=str,
        help='Name of the CITY to check for'
    )
    parser.add_argument(
        '-F', action='store_true',
        help='Display temperatures in F units'
    )
    parser.add_argument('--version', action='version', version='0.0')
    return parser.parse_args()


def _get_api_key() -> str:
    """Return the api_key for openweather from the configuration file.

    Expects configuration file named 'secrets.ini'
    """
    config = ConfigParser()
    config.read('secrets.ini')
    return config['openweather']['api_key']


def build_weather_query(city_input: list[str], fahrenheit=False) -> str:
    """Builds the URL for an API request to OpenWeather's weather API."""
    city_name = ' '.join(city_input)
    encoded_city_name = parse.quote_plus(city_name)
    units = 'imperial' if fahrenheit else 'metric'
    api_key = _get_api_key()
    return f"{BASE_URL}?q={encoded_city_name}&units={units}&appid={api_key}"


def get_weather_data(query_url: str) -> dict:
    """Makes the API request."""
    try:
        with request.urlopen(query_url) as response:
            data = response.read()
    except error.HTTPError as http_error:
        if http_error.code == 401:  # Unauthorized
            sys.exit("Access denied. Check API key.")
        elif http_error.code == 404:  # Not found
            sys.exit("No weather data for this city.")
        else:
            sys.exit(http_error.reason)
    except error.URLError as url_error:
        sys.exit(url_error.reason)
    try:
        json_data = json.loads(data)
    except json.JSONDecodeError:
        sys.exit("Couldn't read server response.")
    if json_data['sys']['country'] == 'PS':
        json_data['sys']['country'] = 'IL'
    return json_data


def display(weather_data: dict, metric=True) -> None:
    """Displays the city name, current temperature in either C or F, 
    the general weather description, latitude and longitude, humidity, 
    cloud cover, the min and max temperatures, and the sunrise and 
    sunset times.
    """
    city = f"{weather_data['name']}, {weather_data['sys']['country']}"
    weather_description = weather_data['weather'][0]['description']

    temp_current = weather_data['main']['temp']
    temp_min = weather_data['main']['temp_min']
    temp_max = weather_data['main']['temp_max']
    feels_like = weather_data['main']['feels_like']
    deg = '°C' if metric else '°F'

    raw_latitude = weather_data['coord']['lat']
    raw_longitude = weather_data['coord']['lon']
    longitude = long_str(raw_longitude)
    latitude = lat_str(raw_latitude)

    raw_wind_speed = weather_data['wind']['speed']
    wind_degrees = weather_data['wind']['deg']
    raw_wind_gust = weather_data['wind'].get('gust')
    wind_speed = speed_str(raw_wind_speed, metric)
    direction = direction_str(wind_degrees)
    gust_speed = speed_str(raw_wind_gust, metric) if raw_wind_gust else None
    
    humidity = weather_data['main']['humidity']
    clouds = weather_data['clouds']['all']
    pressure = weather_data['main']['pressure']
    visibility = weather_data['visibility']

    sunrise_utc = weather_data['sys']['sunrise']
    sunset_utc = weather_data['sys']['sunset']
    timezone = weather_data['timezone']
    sunrise = local_time(sunrise_utc, timezone)
    sunset = local_time(sunset_utc, timezone)

    print(f"{city:^{PADDING}} {temp_current:.0f}{deg}",
          weather_description.capitalize())
    print(f"{latitude + ' ' + longitude:^{PADDING}} {humidity}% humidity")
    print(" "*PADDING, f"Feels like: {feels_like:.0f}{deg}")
    print(" "*PADDING, f"{clouds}% cloud cover")
    print(f"Wind: {wind_speed} {direction}", 
          f"Gusts: {gust_speed}" if gust_speed else "")
    print(f"Temperature range: {temp_min:.0f}-{temp_max:.0f}{deg}",
          f"Pressure: {pressure} mb")
    print(f"Sunrise: {time12hr(sunrise)} Sunset: {time12hr(sunset)}",
          f"Visibility: {visibility/1000:.0f}km")


def long_str(longitude: float) -> str:
    """Converts longitude as degree measure into degrees and minutes 
    with direction.
    """
    minutes = longitude % 1 * 60
    longitude = int(longitude)
    return (f"{abs(longitude):.0f}°{minutes:02.0f}'"
            f"{'E' if longitude > 0 else 'W'}")


def lat_str(latitude: float) -> str:
    """Converts latitude as degree measure into degrees and minutes 
    with direction.
    """
    minutes = latitude % 1 * 60
    latitude = int(latitude)
    return (f"{abs(latitude):.0f}°{minutes:02.0f}'"
            f"{'N' if latitude > 0 else 'S'}")


def speed_str(speed: float, metric=True) -> str:
    """Converts m/s to km/h, and attaches a label of 'km/h' or 'mph'."""
    if metric:
        speed *= 3.6
        return f"{speed:.1f} km/h"
    else:
        return f"{speed} mph"


def direction_str(degrees: int) -> str:
    """Gives a cardinal direction from a degrees measure (east of North)."""
    if degrees < 11.25:
        return 'N'
    elif degrees < 33.75:
        return 'NNE'
    elif degrees < 56.25:
        return 'NE'
    elif degrees < 78.75:
        return 'ENE'
    elif degrees < 101.25:
        return 'E'
    elif degrees < 123.75:
        return 'ESE'
    elif degrees < 146.25:
        return 'SE'
    elif degrees < 168.75:
        return 'SSE'
    elif degrees < 191.25:
        return 'S'
    elif degrees < 213.75:
        return 'SSW'
    elif degrees < 236.25:
        return 'SW'
    elif degrees < 258.75:
        return 'WSW'
    elif degrees < 281.25:
        return 'W'
    elif degrees < 303.75:
        return 'WNW'
    elif degrees < 326.25:
        return 'NW'
    elif degrees < 348.75:
        return 'NNW'
    else:
        return 'N'


def local_time(utc_time: int, timezone_delta: int) -> int:
    """Converts a UTC timestamp into a local timestamp given the 
    timedelta of the local time.
    """
    local_offset = time.timezone if not time.daylight else time.altzone
    # Since the API gives the times in the local time for the client,
    # not the local time for the city in the query
    return utc_time + timezone_delta + local_offset


def time12hr(timestamp: int) -> str:
    """Convert a Unix timestamp into a 12 hour time of day."""
    date_format = datetime.fromtimestamp(timestamp)
    hour = date_format.hour
    minute = date_format.minute
    if hour > 12:
        hour -= 12
    if hour == 0:
        hour = 12
    return f"{hour}:{minute:02}"


if __name__ == '__main__':
    args = parse_args()
    query_url = build_weather_query(args.city, args.F)
    weather_data = get_weather_data(query_url)
    display(weather_data, not args.F)
    #pp(weather_data)

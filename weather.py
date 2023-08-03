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
        if   http_error.code == 401:  # Unauthorized
            sys.exit("Access denied. Check API key.")
        elif http_error.code == 404:  # Not found
            sys.exit("No weather data for this city.")
        else:
            sys.exit(http_error.reason)
    except error.URLError as url_error:
        sys.exit(url_error.reason)
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        sys.exit("Couldn't read server response.")


def display(weather_data: dict, fahrenheit=False) -> None:
    """Displays the city name, current temperature in either C or F, 
    the general weather description, lattitude and longitude, humidity, 
    cloud cover, the min and max temperatures, and the sunrise and 
    sunset times.
    """
    city = f"{weather_data['name']}, {weather_data['sys']['country']}:"
    temp_current = weather_data['main']['temp']
    weather_description = weather_data['weather'][0]['description']
    raw_lattitude = weather_data['coord']['lat']
    raw_longitude = weather_data['coord']['lon']
    longitude = long_str(raw_longitude)
    lattitude = lat_str(raw_lattitude)
    humidity = weather_data['main']['humidity']
    clouds = weather_data['clouds']['all']
    temp_min = weather_data['main']['temp_min']
    temp_max = weather_data['main']['temp_max']
    deg = '°F' if fahrenheit else '°C'
    sunrise_utc = weather_data['sys']['sunrise']
    sunset_utc = weather_data['sys']['sunset']
    timezone = weather_data['timezone']
    sunrise = local_time(sunrise_utc, timezone)
    sunset = local_time(sunset_utc, timezone)

    print(f"{city:^{PADDING}} {temp_current:.0f}{deg}", end=' ')
    print(weather_description.capitalize())
    print(f"{lattitude + ' ' + longitude:^{PADDING}} {humidity}% humidity")
    print(" "*PADDING, f"{clouds}% cloud cover")
    print(" "*PADDING, f"Low: {temp_min:.0f}{deg} High:{temp_max:.0f}{deg}")
    print(f"Sunrise: {time12hr(sunrise)} Sunset: {time12hr(sunset)}")


def long_str(longitude: float) -> str:
    """Converts longitude as degree measure into degrees and minutes 
    with direction.
    """
    minutes = longitude % 1 * 60
    return f"{abs(longitude):.0f}°{minutes:02.0f}'{'E' if longitude > 0 else 'W'}"


def lat_str(lattitude: float) -> str:
    """Converts lattitude as degree measure into degrees and minutes 
    with direction.
    """
    minutes = lattitude % 1 * 60
    return f"{abs(lattitude):.0f}°{minutes:02.0f}'{'N' if lattitude > 0 else 'S'}"


def local_time(utc_time: int, timezone_delta: int) -> int:
    """Converts a UTC timestamp into a local timestamp given the timedelta of the local time"""
    local_offset = time.timezone if not time.daylight else time.altzone
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
    display(weather_data, args.F)
    #pp(weather_data)

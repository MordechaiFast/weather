from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
import json
from urllib import parse, request


BASE_URL = "http://api.openweathermap.org/data/2.5/weather"


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

def build_weather_query(city_input: list[str], fahrenheit = False) -> str:
    """Builds the URL for an API request to OpenWeather's weather API."""
    city_name = " ".join(city_input)
    encoded_city_name = parse.quote_plus(city_name)
    units = 'imperial' if fahrenheit else 'metric'
    api_key = _get_api_key()
    return f"{BASE_URL}?q={encoded_city_name}&units={units}&appid={api_key}"

def get_weather_data(query_url: str) -> dict:
    """Makes the API request."""
    with request.urlopen(query_url) as response:
        data = response.read()
    return json.loads(data)


if __name__ == '__main__':
    args = parse_args()
    query_url = build_weather_query(args.city, args.F)
    print(get_weather_data(query_url))

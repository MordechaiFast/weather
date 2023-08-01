from argparse import ArgumentParser, Namespace
from configparser import ConfigParser


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


if __name__ == '__main__':
    parse_args()

from configparser import ConfigParser


def _get_api_key():
    """Return the api_key for openweather from the configuration file.
    
    Expects configuration file named 'secrets.ini'
    """
    config = ConfigParser()
    config.read('secrets.ini')
    return config['openweather']['api_key']


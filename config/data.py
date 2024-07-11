import configparser
from pathlib import Path


# Absolut path
dir_path = Path.cwd()
path = Path(dir_path, 'config', 'config.ini')
config = configparser.ConfigParser()
config.read(path)

# Constants
DB_PASSWORD = config['Database']['db_password']
DB_LOGIN = config['Database']['db_login']
DB_NAME = config['Database']['db_name']

SLEEP = 600  # How often will be check website (sec)

import configparser
import os



ADMIN_ID = 1816182296

FOLDER = os.path.dirname(__file__)
PARAMS = os.path.join(FOLDER, "token.ini")


config = configparser.ConfigParser()
config.read(PARAMS)


API_ID = config["DEFAULT"]["API_ID"]
API_HASH = config["DEFAULT"]["API_HASH"]
TOKEN = config["DEFAULT"]["TOKEN"]
DATABASE_URL = config["DEFAULT"]["DATABASE_URL"]


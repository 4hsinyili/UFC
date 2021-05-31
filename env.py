import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_PWD = os.getenv("MYSQL_PWD")
MYSQL_ACCOUNT = os.getenv("MYSQL_ACCOUNT")
MYSQL_ROUTE = os.getenv("MYSQL_ROUTE")
MYSQL_PORT = os.getenv("MYSQL_PORT")


MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_ADMIN_USERNAME = os.getenv("MONGO_ADMIN_USERNAME")
MONGO_ADMIN_PASSWORD = os.getenv("MONGO_ADMIN_PASSWORD")
driver_path = os.getenv('DRIVER_PATH')
SECRET_KEY = os.getenv('SECRET_KEY')
PLACE_API_KEY = os.getenv("PLACE_API_KEY")

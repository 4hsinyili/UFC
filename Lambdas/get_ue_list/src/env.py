import os
from dotenv import load_dotenv

load_dotenv()
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_ADMIN_USERNAME = os.getenv("MONGO_ADMIN_USERNAME")
MONGO_ADMIN_PASSWORD = os.getenv("MONGO_ADMIN_PASSWORD")
driver_path = os.getenv('DRIVER_PATH')
SECRET_KEY = os.getenv('SECRET_KEY')
PLACE_API_KEY = os.getenv("PLACE_API_KEY")

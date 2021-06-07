import os
from dotenv import load_dotenv

load_dotenv()
MONGO_ATLAS_URI = os.getenv('MONGO_ATLAS_URI')
driver_path = os.getenv('DRIVER_PATH')
SECRET_KEY = os.getenv('SECRET_KEY')
PLACE_API_KEY = os.getenv("PLACE_API_KEY")

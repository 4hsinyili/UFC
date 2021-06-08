import os
from dotenv import load_dotenv

load_dotenv()
MONGO_HOST_EC2 = os.getenv("MONGO_HOST_EC2")
MONGO_PORT_EC2 = int(os.getenv("MONGO_PORT_EC2"))
MONGO_ADMIN_USERNAME_EC2 = os.getenv("MONGO_ADMIN_USERNAME_EC2")
MONGO_ADMIN_PASSWORD_EC2 = os.getenv("MONGO_ADMIN_PASSWORD_EC2")

MONGO_EC2_URI = f"mongodb://{MONGO_ADMIN_USERNAME_EC2}:{MONGO_ADMIN_PASSWORD_EC2}@{MONGO_HOST_EC2 }"
driver_path = os.getenv('DRIVER_PATH')
PLACE_API_KEY = os.getenv("PLACE_API_KEY")
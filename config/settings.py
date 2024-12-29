import os
import pyaudio

# Google Cloud credentials
GOOGLE_CREDENTIALS_PATH = r"C:\Users\Dhruv\Desktop\translator\sa_translator.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 1
BUFFER_SIZE = 2048

# Speech recognition settings
ENERGY_THRESHOLD = 300
DYNAMIC_ENERGY = True
PAUSE_THRESHOLD = 0.8

# Default language
DEFAULT_LANGUAGE = 'en' 
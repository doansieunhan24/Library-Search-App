"""
Configuration file for Library Search App
"""

import os

# Database configuration
DATABASE_PATH = r"C:\Users\LOQ\OneDrive\Tài liệu\Visual Studio 2022\NewUI\data_fix"

# Whisper model configuration
WHISPER_MODEL_NAME = "openai/whisper-small"
WHISPER_MODEL_PATH = None  # Set to None to use default model

# OpenAI configuration
OPENAI_API_KEY = ""  # Replace with your OpenAI API key

# Audio recording configuration
AUDIO_CHUNK = 1024
AUDIO_FORMAT = "paInt16"  # pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_RATE = 44100
AUDIO_RECORD_SECONDS = 30  # Maximum recording time

# UI configuration
WINDOW_TITLE = "📚 Tìm Kiếm Thư Viện Bằng Giọng Nói"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Text processing configuration
MAX_TEXT_LENGTH = 500
MIN_TEXT_LENGTH = 3

# Database schema (for reference)
DATABASE_SCHEMA = {
    "table_name": "books",
    "columns": [
        "id",
        "title", 
        "author",
        "publisher",
        "publication_year",
        "pages",
        "dimensions",
        "registration_number",
        "price",
        "storage_location",
        "document_type",
        "availability",
        "keywords",
        "subject",
        "department",
        "summary",
        "url"
    ]
}

# Search configuration
MAX_SEARCH_RESULTS = 20
SEARCH_TIMEOUT = 30  # seconds

# File paths
TEMP_AUDIO_DIR = "temp_audio"
LOG_DIR = "logs"

# Create directories if they don't exist
for directory in [TEMP_AUDIO_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

"""
Centralized configuration management for the Weather Report Video Generator.
This file loads settings from environment variables and provides default values.
Includes development features like configuration hot-reloading.
"""

import os
import sys
import time
import json
import threading
import importlib
from datetime import timedelta
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Callable

# Load environment variables from .env file
load_dotenv()


LANGUAGE = "Filipino"

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'generated')
MULTIMEDIA_DIR = os.path.join(DATA_DIR, 'multimedia')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
CACHE_DIR = os.path.join(DATA_DIR, 'weather', 'cache')

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
print(f"OpenAI API key: {OPENAI_API_KEY}")
TTS_API_KEY = os.getenv('TTS_API_KEY')

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Database Configuration
DATABASE_URI = os.getenv('DATABASE_URI', f"sqlite:///{os.path.join(BASE_DIR, 'weather_reports.db')}")

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_ROTATION = os.getenv('LOG_ROTATION', '500 MB')
LOG_RETENTION = os.getenv('LOG_RETENTION', '10 days')
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"

# Video Output Configuration
VIDEO_OUTPUT_WIDTH = int(os.getenv('VIDEO_OUTPUT_WIDTH', '1920'))
VIDEO_OUTPUT_HEIGHT = int(os.getenv('VIDEO_OUTPUT_HEIGHT', '1080'))
VIDEO_OUTPUT_FPS = int(os.getenv('VIDEO_OUTPUT_FPS', '30'))
VIDEO_OUTPUT_QUALITY = int(os.getenv('VIDEO_OUTPUT_QUALITY', '95'))

# General Application Settings
APP_NAME = "Weather Report Video Generator"
MAX_VIDEOS_STORED = int(os.getenv('MAX_VIDEOS_STORED', '50'))
CLEANUP_OLD_VIDEOS = os.getenv('CLEANUP_OLD_VIDEOS', 'True').lower() == 'true'
VIDEO_RETENTION_DAYS = int(os.getenv('VIDEO_RETENTION_DAYS', '30'))

# Scraping Configuration
SCRAPING = {
    "default_source": os.getenv('DEFAULT_SCRAPING_SOURCE', 'worldweatheronline'),
    "sources": {
        "worldweatheronline": {
            "base_url": "https://www.worldweatheronline.com/{location}-weather/{region}/{country_code}.aspx",
            "timeout": int(os.getenv('SCRAPING_TIMEOUT', '30')),
        },
    },
    "playwright": {
        "headless": os.getenv('PLAYWRIGHT_HEADLESS', 'True').lower() == 'true',
        "browser": os.getenv('PLAYWRIGHT_BROWSER', 'chromium'),
        "viewport": {
            "width": VIDEO_OUTPUT_WIDTH,
            "height": VIDEO_OUTPUT_HEIGHT
        },
        "user_agent": os.getenv('PLAYWRIGHT_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
        "screenshot_on_error": os.getenv('SCREENSHOT_ON_ERROR', 'True').lower() == 'true',
        "screenshot_dir": os.path.join(LOGS_DIR, 'screenshots'),
        "proxy": os.getenv('PLAYWRIGHT_PROXY'),
        "timeout": int(os.getenv('PLAYWRIGHT_TIMEOUT', '30000')),
        "retry": {
            "attempts": int(os.getenv('PLAYWRIGHT_RETRY_ATTEMPTS', '3')),
            "delay": int(os.getenv('PLAYWRIGHT_RETRY_DELAY', '1000')),
        }
    },
    "cache": {
        "enabled": os.getenv('SCRAPING_CACHE_ENABLED', 'True').lower() == 'true',
        "timeout": int(os.getenv('SCRAPING_CACHE_TIMEOUT', '3600')),
        "backend": os.getenv('SCRAPING_CACHE_BACKEND', 'filesystem'),
        "directory": CACHE_DIR
    },
    "logging": {
        "level": os.getenv('SCRAPING_LOG_LEVEL', 'INFO'),
        "file": os.path.join(LOGS_DIR, 'scraper.log'),
        "format": LOG_FORMAT
    },
    # Weather Scraping Defaults
    "weather_defaults": {
        "url": os.getenv('DEFAULT_WEATHER_URL', 'https://www.msn.com/en-ph/weather/forecast/in-Pulilan,Central-Luzon'),
        "location": {
            "municipality": os.getenv('DEFAULT_MUNICIPALITY', 'Pulilan'),
            "region": os.getenv('DEFAULT_REGION', 'Bulacan'),
            "country": os.getenv('DEFAULT_COUNTRY', 'Philippines')
        },
        "timeout": int(os.getenv('DEFAULT_WEATHER_TIMEOUT', '60000')),
        "headless": os.getenv('DEFAULT_WEATHER_HEADLESS', 'True').lower() == 'true',
        "slowmo": int(os.getenv('DEFAULT_WEATHER_SLOWMO', '100')),
        "description": "Default weather scraping configuration for Pulilan, Central Luzon weather data"
    },
    # Segment Generation Defaults
    "segment_defaults": {
        "input_file": os.getenv('DEFAULT_SEGMENT_INPUT', 'data/latest/weather_data.json'),
        "output_dir": os.getenv('DEFAULT_SEGMENT_OUTPUT_DIR', 'data/latest/'),
        "model": os.getenv('DEFAULT_SEGMENT_MODEL', 'gpt-4o'),
        "temperature": float(os.getenv('DEFAULT_SEGMENT_TEMPERATURE', '0.7')),
        "max_tokens": int(os.getenv('DEFAULT_SEGMENT_MAX_TOKENS', '1500')),
        "total_target_duration": float(os.getenv('DEFAULT_TOTAL_DURATION', '190.0')),
        "segment_types": [
            {
                'name': 'opening_greeting',
                'display_name': 'Opening Greeting',
                'display_order': 0,
                'target_duration': float(os.getenv('OPENING_DURATION', '15.0')),
                'prompt_focus': 'Professional introduction with current conditions and location'
            },
            {
                'name': 'current_weather_conditions_spotlight',
                'display_name': 'Current Weather Conditions Spotlight',
                'display_order': 1,
                'target_duration': float(os.getenv('CONDITIONS_DURATION', '45.0')),
                'prompt_focus': 'Detailed current conditions report with temperature, wind, humidity, and UV index'
            },
            {
                'name': 'atmospheric_weather_storytelling',
                'display_name': 'Weather Pattern Analysis',
                'display_order': 2,
                'target_duration': float(os.getenv('ANALYSIS_DURATION', '30.0')),
                'prompt_focus': 'Professional weather pattern analysis with seasonal context and air quality'
            },
            {
                'name': 'today_weather_journey',
                'display_name': 'Today\'s Hourly Forecast',
                'display_order': 3,
                'target_duration': float(os.getenv('HOURLY_DURATION', '40.0')),
                'prompt_focus': 'Hour-by-hour forecast with temperature progression and timing'
            },
            {
                'name': 'tomorrow_weather_preview',
                'display_name': 'Tomorrow\'s Weather Outlook',
                'display_order': 4,
                'target_duration': float(os.getenv('TOMORROW_DURATION', '20.0')),
                'prompt_focus': 'Tomorrow\'s forecast with temperature range and condition comparison'
            },
            {
                'name': 'municipal_weather_impact',
                'display_name': 'Local Weather Impact',
                'display_order': 5,
                'target_duration': float(os.getenv('IMPACT_DURATION', '25.0')),
                'prompt_focus': 'Local weather advisories, community impact, and safety information'
            },
            {
                'name': 'closing_summary',
                'display_name': 'Weather Summary',
                'display_order': 6,
                'target_duration': float(os.getenv('CLOSING_DURATION', '15.0')),
                'prompt_focus': 'Professional summary of key weather points and sign-off'
            }
        ],
        "description": "Default segment generation configuration for municipal weather reports"
    },
    # TTS Generation Defaults
    "tts_defaults": {
        "input_file": os.getenv('DEFAULT_TTS_INPUT', 'data/latest/weather_data_scripts.json'),
        "output_dir": os.getenv('DEFAULT_TTS_OUTPUT_DIR', 'data/latest/'),
        "voice": os.getenv('DEFAULT_TTS_VOICE', 'nova'),
        "model": os.getenv('DEFAULT_TTS_MODEL', 'tts-1'),
        "response_format": os.getenv('DEFAULT_TTS_FORMAT', 'mp3'),
        "combine_audio": os.getenv('DEFAULT_TTS_COMBINE', 'True').lower() == 'true',
        "silence_duration": float(os.getenv('DEFAULT_TTS_SILENCE', '0.5')),
        "available_voices": {
            'alloy': 'Neutral, balanced voice',
            'echo': 'Male voice, clear and articulate', 
            'fable': 'British accent, warm tone',
            'onyx': 'Deep male voice, authoritative',
            'nova': 'Female voice, friendly and warm',
            'shimmer': 'Female voice, soft and gentle'
        },
        "audio_settings": {
            "bitrate": os.getenv('TTS_AUDIO_BITRATE', '128k'),
            "sample_rate": int(os.getenv('TTS_AUDIO_SAMPLE_RATE', '24000')),
            "channels": int(os.getenv('TTS_AUDIO_CHANNELS', '1'))
        },
        "description": "Default TTS generation configuration for weather report audio"
    },
    # Subtitle generation settings with environment variable support
    "subtitle_defaults": {
        "input_file": os.getenv('DEFAULT_SUBTITLE_INPUT', 'data/latest/audio/weather_data_combined_weather_report.mp3'),
        "output_dir": os.getenv('DEFAULT_SUBTITLE_OUTPUT_DIR', 'data/latest/'),
        "output_file": os.getenv('DEFAULT_SUBTITLE_OUTPUT_FILE', 'manifest.json'),
        
        # AI Models
        "whisper_model": os.getenv('DEFAULT_WHISPER_MODEL', 'whisper-1'),
        "segmentation_model": os.getenv('DEFAULT_SEGMENTATION_MODEL', 'gpt-4'),
        
        # Transcription Settings
        "response_format": os.getenv('DEFAULT_WHISPER_FORMAT', 'verbose_json'),
        "timestamp_granularities": ["word", "segment"],
        
        # Segmentation
        "segment_duration": {
            "min": int(os.getenv('DEFAULT_MIN_SEGMENT_DURATION', '15')),
            "max": int(os.getenv('DEFAULT_MAX_SEGMENT_DURATION', '30')),
            "target": int(os.getenv('DEFAULT_TARGET_SEGMENT_COUNT', '17'))
        },
        
        # Intro/Outro Settings  
        "intro_outro": {
            "intro_duration": float(os.getenv('DEFAULT_INTRO_DURATION', '6.0')),
            "outro_duration": float(os.getenv('DEFAULT_OUTRO_DURATION', '6.6')),
            "intro_media": os.getenv('DEFAULT_INTRO_MEDIA', 'intro.mp4'),
            "outro_media": os.getenv('DEFAULT_OUTRO_MEDIA', 'outro.mp4')
        },
        
        # AI Settings for segmentation
        "ai_settings": {
            "temperature": float(os.getenv('DEFAULT_SUBTITLE_TEMPERATURE', '0.2')),
            "confidence_threshold": float(os.getenv('DEFAULT_CONFIDENCE_THRESHOLD', '0.8'))
        }
        },
        # Card recorder settings for Flask weather cards capture
        "card_defaults": {
            "flask_url": os.getenv('DEFAULT_FLASK_URL', 'http://localhost:5001'),
            "viewport": {
                "width": int(os.getenv('DEFAULT_CARD_VIEWPORT_WIDTH', '1200')),
                "height": int(os.getenv('DEFAULT_CARD_VIEWPORT_HEIGHT', '800'))
            },
            "video_fps": int(os.getenv('DEFAULT_CARD_FPS', '30')),
            "output_dir": os.getenv('DEFAULT_CARD_OUTPUT_DIR', 'data/latest/multimedia'),
            
            # Card-specific durations (in seconds)
            "card_durations": {
                "card-temperature": int(os.getenv('CARD_TEMPERATURE_DURATION', '6')),
                "card-feels-like": int(os.getenv('CARD_FEELS_LIKE_DURATION', '5')),
                "card-cloud-cover": int(os.getenv('CARD_CLOUD_COVER_DURATION', '5')),
                "card-precipitation": int(os.getenv('CARD_PRECIPITATION_DURATION', '7')),
                "card-wind": int(os.getenv('CARD_WIND_DURATION', '6')),
                "card-humidity": int(os.getenv('CARD_HUMIDITY_DURATION', '6')),
                "card-uv": int(os.getenv('CARD_UV_DURATION', '5')),
                "card-aqi": int(os.getenv('CARD_AQI_DURATION', '5')),
                "card-visibility": int(os.getenv('CARD_VISIBILITY_DURATION', '5')),
                "card-pressure": int(os.getenv('CARD_PRESSURE_DURATION', '6')),
                "card-sun": int(os.getenv('CARD_SUN_DURATION', '6')),
                "card-moon": int(os.getenv('CARD_MOON_DURATION', '5')),
                "card-current": int(os.getenv('CARD_CURRENT_DURATION', '8')),
                "card-hourly": int(os.getenv('CARD_HOURLY_DURATION', '10'))
        },
        "description": "Default card recorder configuration for Flask weather cards capture"
    },
        # Weather recorder settings for provincial weather capture  
        "weather_recorder_defaults": {
            "video_duration": int(os.getenv('DEFAULT_WEATHER_VIDEO_DURATION', '15')),
            "video_fps": int(os.getenv('DEFAULT_WEATHER_VIDEO_FPS', '1')),
            "viewport": {
                "width": int(os.getenv('DEFAULT_WEATHER_VIEWPORT_WIDTH', '1200')),
                "height": int(os.getenv('DEFAULT_WEATHER_VIEWPORT_HEIGHT', '800'))
            },
        "output_dir": os.getenv('DEFAULT_WEATHER_RECORDER_OUTPUT', 'data/latest/multimedia'),
        "description": "Default weather recorder configuration for provincial weather capture"
        }
}

# Weather Scraping Defaults - Direct Access Variables
DEFAULT_WEATHER_URL = SCRAPING["weather_defaults"]["url"]
DEFAULT_MUNICIPALITY = SCRAPING["weather_defaults"]["location"]["municipality"]
DEFAULT_REGION = SCRAPING["weather_defaults"]["location"]["region"]
DEFAULT_COUNTRY = SCRAPING["weather_defaults"]["location"]["country"]
DEFAULT_WEATHER_TIMEOUT = SCRAPING["weather_defaults"]["timeout"]
DEFAULT_WEATHER_HEADLESS = SCRAPING["weather_defaults"]["headless"]
DEFAULT_WEATHER_SLOWMO = SCRAPING["weather_defaults"]["slowmo"]

# Segment Generation Defaults - Direct Access Variables
DEFAULT_SEGMENT_INPUT = SCRAPING["segment_defaults"]["input_file"]
DEFAULT_SEGMENT_OUTPUT_DIR = SCRAPING["segment_defaults"]["output_dir"]
DEFAULT_SEGMENT_MODEL = SCRAPING["segment_defaults"]["model"]
DEFAULT_SEGMENT_TEMPERATURE = SCRAPING["segment_defaults"]["temperature"]
DEFAULT_SEGMENT_MAX_TOKENS = SCRAPING["segment_defaults"]["max_tokens"]
DEFAULT_TOTAL_DURATION = SCRAPING["segment_defaults"]["total_target_duration"]
DEFAULT_SEGMENT_TYPES = SCRAPING["segment_defaults"]["segment_types"]

# TTS Generation Defaults - Direct Access Variables
DEFAULT_TTS_INPUT = SCRAPING["tts_defaults"]["input_file"]
DEFAULT_TTS_OUTPUT_DIR = SCRAPING["tts_defaults"]["output_dir"]
DEFAULT_TTS_VOICE = SCRAPING["tts_defaults"]["voice"]
DEFAULT_TTS_MODEL = SCRAPING["tts_defaults"]["model"]
DEFAULT_TTS_FORMAT = SCRAPING["tts_defaults"]["response_format"]
DEFAULT_TTS_COMBINE = SCRAPING["tts_defaults"]["combine_audio"]
DEFAULT_TTS_SILENCE = SCRAPING["tts_defaults"]["silence_duration"]
DEFAULT_TTS_VOICES = SCRAPING["tts_defaults"]["available_voices"]
DEFAULT_TTS_AUDIO_SETTINGS = SCRAPING["tts_defaults"]["audio_settings"]

# Subtitle Generation Defaults - Direct Access Variables
DEFAULT_SUBTITLE_INPUT = SCRAPING["subtitle_defaults"]["input_file"]
DEFAULT_SUBTITLE_OUTPUT_DIR = SCRAPING["subtitle_defaults"]["output_dir"]
DEFAULT_SUBTITLE_OUTPUT_FILE = SCRAPING["subtitle_defaults"]["output_file"]
DEFAULT_WHISPER_MODEL = SCRAPING["subtitle_defaults"]["whisper_model"]
DEFAULT_SEGMENTATION_MODEL = SCRAPING["subtitle_defaults"]["segmentation_model"]
DEFAULT_WHISPER_FORMAT = SCRAPING["subtitle_defaults"]["response_format"]
DEFAULT_TIMESTAMP_GRANULARITIES = SCRAPING["subtitle_defaults"]["timestamp_granularities"]
DEFAULT_SEGMENT_DURATION = SCRAPING["subtitle_defaults"]["segment_duration"]
DEFAULT_INTRO_OUTRO = SCRAPING["subtitle_defaults"]["intro_outro"]
DEFAULT_SUBTITLE_AI_SETTINGS = SCRAPING["subtitle_defaults"]["ai_settings"]

# AI Model Configuration
AI_CONFIG = {
    "openai": {
        "default_model": os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4-turbo-preview"),
        "vision_model": os.getenv("OPENAI_VISION_MODEL", "gpt-4-vision-preview"),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
        "top_p": float(os.getenv("OPENAI_TOP_P", "1.0")),
        "frequency_penalty": float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.0")),
        "presence_penalty": float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.0")),
    }
}

# Text-to-Speech Configuration (Enhanced with news-style options)
TTS_CONFIG = {
    "provider": os.getenv("TTS_PROVIDER", "openai"),  # Options: "openai", "elevenlabs", "google"
    "openai": {
        "voice": os.getenv("TTS_OPENAI_VOICE", "alloy"),  # alloy works well with Filipino
        "speed": float(os.getenv("TTS_OPENAI_SPEED", "0.9")),  # Slightly slower for Filipino clarity
        "model": os.getenv("TTS_OPENAI_MODEL", "tts-1-hd"),  # Higher quality model
        "output_format": "mp3",
    },
    "elevenlabs": {
        "voice_id": os.getenv("TTS_ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),  # Bella (female voice)
        "model_id": os.getenv("TTS_ELEVENLABS_MODEL_ID", "eleven_flash_v2_5"),  # Supports Filipino and English
        "voice_settings": {
            "stability": float(os.getenv("TTS_ELEVENLABS_STABILITY", "0.75")),  # How stable the voice is
            "similarity_boost": float(os.getenv("TTS_ELEVENLABS_SIMILARITY_BOOST", "0.8")),  # Voice similarity
            "style": float(os.getenv("TTS_ELEVENLABS_STYLE", "0.5")),  # Style exaggeration
            "use_speaker_boost": os.getenv("TTS_ELEVENLABS_SPEAKER_BOOST", "True").lower() == 'true'
        },
        "output_format": os.getenv("TTS_ELEVENLABS_FORMAT", "mp3_44100_128"),  # High quality mp3
        "chunk_length_schedule": [120, 160, 250, 370],  # Text chunk sizes for longer texts
    },
    "google": {
        "language_code": os.getenv("TTS_GOOGLE_LANG", "en-US"),  # fil-PH for Filipino
        "voice_name": os.getenv("TTS_GOOGLE_VOICE", "en-US-Chirp3-HD-Achernar"),  # fil-PH-Standard-A for Filipino
        "voice_gender": os.getenv("TTS_GOOGLE_GENDER", "FEMALE"),
        "speaking_rate": float(os.getenv("TTS_GOOGLE_RATE", "0.9")),  # Slightly slower for clarity
        "pitch": float(os.getenv("TTS_GOOGLE_PITCH", "0.0")),  # Normal pitch
        "output_format": "mp3",
        "audio_encoding": "MP3",
    },
    "audio_format": os.getenv("TTS_AUDIO_FORMAT", "mp3"),
    "sample_rate": int(os.getenv("TTS_SAMPLE_RATE", "24000")),
    "use_replacements": os.getenv("TTS_USE_REPLACEMENTS", "True").lower() == 'true',
}

# Visual Assets Configuration
VISUAL_CONFIG = {
    "sources": ["local"],  # Can add: "pexels", "unsplash"
    "pexels": {
        "api_key": os.getenv("PEXELS_API_KEY"),
    },
    "unsplash": {
        "api_key": os.getenv("UNSPLASH_API_KEY"),
    },
    "local": {
        "directory": os.path.join(BASE_DIR, "assets", "images"),
    },
    "video_priority": os.getenv('VIDEO_PRIORITY', 'True').lower() == 'true',
    "fallback_directory": os.path.join(BASE_DIR, "assets", "default"),
    "max_assets_per_segment": int(os.getenv("MAX_ASSETS_PER_SEGMENT", "3")),
}

# Video Assembly Configuration
VIDEO_CONFIG = {
    "resolution": os.getenv("VIDEO_RESOLUTION", "1080p"),
    "fps": VIDEO_OUTPUT_FPS,
    "format": os.getenv("VIDEO_FORMAT", "mp4"),
    "codec": os.getenv("VIDEO_CODEC", "h264"),
    "bitrate": os.getenv("VIDEO_BITRATE", "5M"),
    "add_watermark": os.getenv("ADD_WATERMARK", "False").lower() == 'true',
    "watermark_path": os.path.join(BASE_DIR, "assets", "logo.png"),
    "watermark_position": os.getenv("WATERMARK_POSITION", "bottom-right"),
    "intro_path": os.path.join(BASE_DIR, "assets", "intro.mp4"),
    "outro_path": os.path.join(BASE_DIR, "assets", "outro.mp4"),
    "background_music": os.path.join(BASE_DIR, "assets", "background.mp3"),
    "background_volume": float(os.getenv("BACKGROUND_MUSIC_VOLUME", "0.1")),
    "transitions": {
        "type": os.getenv("TRANSITION_TYPE", "fade"),
        "duration": float(os.getenv("TRANSITION_DURATION", "0.5")),
    },
}

# Storage Configuration
STORAGE_CONFIG = {
    "type": os.getenv("STORAGE_TYPE", "json"),
    "json": {
        "base_dir": DATA_DIR
    },
    "sqlite": {
        "db_path": os.path.join(BASE_DIR, "weather_reports.db")
    }
}

# Job Queue Configuration
JOB_QUEUE_CONFIG = {
    "broker": REDIS_URL,
    "result_backend": REDIS_URL,
    "task_track_started": True,
    "task_time_limit": 3600,  # 1 hour
    "worker_concurrency": int(os.getenv("WORKER_CONCURRENCY", "2")),
    "worker_prefetch_multiplier": 1,
    "beat_schedule": {
        "cleanup_old_videos": {
            "task": "tasks.maintenance.cleanup_old_videos",
            "schedule": timedelta(days=1),
            "options": {"expires": 3600}
        }
    }
}

# Web Interface Configuration
WEB_CONFIG = {
    "enable_user_registration": os.getenv("ENABLE_USER_REGISTRATION", "False").lower() == 'true',
    "enable_social_sharing": os.getenv("ENABLE_SOCIAL_SHARING", "True").lower() == 'true',
    "theme": os.getenv("WEB_THEME", "light"),
    "page_size": int(os.getenv("WEB_PAGE_SIZE", "10")),
    "thumbnail_size": (320, 180),
}

# Segment Types Configuration
SEGMENT_TYPES = [
    {
        "name": "intro",
        "display_name": "Introduction",
        "required": True,
        "position": "beginning",
        "description": "An introduction to the weather report",
    },
    {
        "name": "current_conditions",
        "display_name": "Current Conditions",
        "required": True,
        "position": "middle",
        "description": "Current weather conditions",
    },
    {
        "name": "forecast",
        "display_name": "Forecast",
        "required": True,
        "position": "middle",
        "description": "Weather forecast for coming days",
    },
    {
        "name": "radar",
        "display_name": "Radar Images",
        "required": False,
        "position": "middle",
        "description": "Weather radar images showing precipitation",
    },
    {
        "name": "outro",
        "display_name": "Conclusion",
        "required": True,
        "position": "end",
        "description": "Conclusion of the weather report",
    },
]

# Function to validate the configuration
def validate_config() -> List[str]:
    """Validate configuration and return a list of warnings/errors"""
    warnings = []
    
    # Check required API keys
    if not OPENAI_API_KEY:
        warnings.append("OpenAI API key is missing")
    
    if not TTS_API_KEY:
        warnings.append("TTS API key is missing")
    
    # Check directories
    for path in [DATA_DIR, MULTIMEDIA_DIR, OUTPUT_DIR, LOGS_DIR, CACHE_DIR]:
        os.makedirs(path, exist_ok=True)
        if not os.access(path, os.W_OK):
            warnings.append(f"No write access to directory: {path}")
    
    return warnings

# Get all config as a dictionary for export
def get_all_config() -> Dict[str, Any]:
    """Return all configuration as a dictionary"""
    return {
        "APP_NAME": APP_NAME,
        "BASE_DIR": BASE_DIR,
        "DATA_DIR": DATA_DIR,
        "MULTIMEDIA_DIR": MULTIMEDIA_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "LOGS_DIR": LOGS_DIR,
        "CACHE_DIR": CACHE_DIR,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "TTS_API_KEY": TTS_API_KEY,
        "REDIS_URL": REDIS_URL,
        "DATABASE_URI": DATABASE_URI,
        "LOG_LEVEL": LOG_LEVEL,
        "LOG_ROTATION": LOG_ROTATION,
        "LOG_RETENTION": LOG_RETENTION,
        "VIDEO_OUTPUT_WIDTH": VIDEO_OUTPUT_WIDTH,
        "VIDEO_OUTPUT_HEIGHT": VIDEO_OUTPUT_HEIGHT,
        "VIDEO_OUTPUT_FPS": VIDEO_OUTPUT_FPS,
        "VIDEO_OUTPUT_QUALITY": VIDEO_OUTPUT_QUALITY,
        "MAX_VIDEOS_STORED": MAX_VIDEOS_STORED,
        "CLEANUP_OLD_VIDEOS": CLEANUP_OLD_VIDEOS,
        "VIDEO_RETENTION_DAYS": VIDEO_RETENTION_DAYS,
        "SCRAPING": SCRAPING,
        "AI_CONFIG": AI_CONFIG,
        "TTS_CONFIG": TTS_CONFIG,
        "VISUAL_CONFIG": VISUAL_CONFIG,
        "VIDEO_CONFIG": VIDEO_CONFIG,
        "STORAGE_CONFIG": STORAGE_CONFIG,
        "JOB_QUEUE_CONFIG": JOB_QUEUE_CONFIG,
        "WEB_CONFIG": WEB_CONFIG,
        "SEGMENT_TYPES": SEGMENT_TYPES,
        # Weather Scraping Defaults for direct access
        "DEFAULT_WEATHER_URL": SCRAPING["weather_defaults"]["url"],
        "DEFAULT_MUNICIPALITY": SCRAPING["weather_defaults"]["location"]["municipality"],
        "DEFAULT_REGION": SCRAPING["weather_defaults"]["location"]["region"],
        "DEFAULT_COUNTRY": SCRAPING["weather_defaults"]["location"]["country"],
        "DEFAULT_WEATHER_TIMEOUT": SCRAPING["weather_defaults"]["timeout"],
        "DEFAULT_WEATHER_HEADLESS": SCRAPING["weather_defaults"]["headless"],
        "DEFAULT_WEATHER_SLOWMO": SCRAPING["weather_defaults"]["slowmo"],
        # Segment Generation Defaults for direct access
        "DEFAULT_SEGMENT_INPUT": SCRAPING["segment_defaults"]["input_file"],
        "DEFAULT_SEGMENT_OUTPUT_DIR": SCRAPING["segment_defaults"]["output_dir"],
        "DEFAULT_SEGMENT_MODEL": SCRAPING["segment_defaults"]["model"],
        "DEFAULT_SEGMENT_TEMPERATURE": SCRAPING["segment_defaults"]["temperature"],
        "DEFAULT_SEGMENT_MAX_TOKENS": SCRAPING["segment_defaults"]["max_tokens"],
        "DEFAULT_TOTAL_DURATION": SCRAPING["segment_defaults"]["total_target_duration"],
        "DEFAULT_SEGMENT_TYPES": SCRAPING["segment_defaults"]["segment_types"],
        # TTS Generation Defaults for direct access
        "DEFAULT_TTS_INPUT": SCRAPING["tts_defaults"]["input_file"],
        "DEFAULT_TTS_OUTPUT_DIR": SCRAPING["tts_defaults"]["output_dir"],
        "DEFAULT_TTS_VOICE": SCRAPING["tts_defaults"]["voice"],
        "DEFAULT_TTS_MODEL": SCRAPING["tts_defaults"]["model"],
        "DEFAULT_TTS_FORMAT": SCRAPING["tts_defaults"]["response_format"],
        "DEFAULT_TTS_COMBINE": SCRAPING["tts_defaults"]["combine_audio"],
        "DEFAULT_TTS_SILENCE": SCRAPING["tts_defaults"]["silence_duration"],
        "DEFAULT_TTS_VOICES": SCRAPING["tts_defaults"]["available_voices"],
        "DEFAULT_TTS_AUDIO_SETTINGS": SCRAPING["tts_defaults"]["audio_settings"],
        # Subtitle Generation Defaults for direct access
        "DEFAULT_SUBTITLE_INPUT": SCRAPING["subtitle_defaults"]["input_file"],
        "DEFAULT_SUBTITLE_OUTPUT_DIR": SCRAPING["subtitle_defaults"]["output_dir"],
        "DEFAULT_SUBTITLE_OUTPUT_FILE": SCRAPING["subtitle_defaults"]["output_file"],
        "DEFAULT_WHISPER_MODEL": SCRAPING["subtitle_defaults"]["whisper_model"],
        "DEFAULT_SEGMENTATION_MODEL": SCRAPING["subtitle_defaults"]["segmentation_model"],
        "DEFAULT_WHISPER_FORMAT": SCRAPING["subtitle_defaults"]["response_format"],
        "DEFAULT_TIMESTAMP_GRANULARITIES": SCRAPING["subtitle_defaults"]["timestamp_granularities"],
        "DEFAULT_SEGMENT_DURATION": SCRAPING["subtitle_defaults"]["segment_duration"],
        "DEFAULT_INTRO_OUTRO": SCRAPING["subtitle_defaults"]["intro_outro"],
        "DEFAULT_SUBTITLE_AI_SETTINGS": SCRAPING["subtitle_defaults"]["ai_settings"],
        # Card Recorder Defaults for direct access
        "DEFAULT_FLASK_URL": SCRAPING["card_defaults"]["flask_url"],
        "DEFAULT_CARD_VIEWPORT": (SCRAPING["card_defaults"]["viewport"]["width"], SCRAPING["card_defaults"]["viewport"]["height"]),
        "DEFAULT_CARD_FPS": SCRAPING["card_defaults"]["video_fps"],
        "DEFAULT_CARD_OUTPUT_DIR": SCRAPING["card_defaults"]["output_dir"],
        "DEFAULT_CARD_DURATIONS": SCRAPING["card_defaults"]["card_durations"],
        # Weather Recorder Defaults for direct access
        "DEFAULT_WEATHER_VIDEO_DURATION": SCRAPING["weather_recorder_defaults"]["video_duration"],
        "DEFAULT_WEATHER_VIDEO_FPS": SCRAPING["weather_recorder_defaults"]["video_fps"],
        "DEFAULT_WEATHER_VIEWPORT": (SCRAPING["weather_recorder_defaults"]["viewport"]["width"], SCRAPING["weather_recorder_defaults"]["viewport"]["height"]),
        "DEFAULT_WEATHER_RECORDER_OUTPUT": SCRAPING["weather_recorder_defaults"]["output_dir"],
    }

# Export all configuration 
config = get_all_config()

# Development mode with hot-reloading functionality
# ----------------------------------------------

# Flag to enable/disable auto reloading
auto_reload_enabled = True

# Time between file checks (in seconds)
reload_interval = 2.0

# Callbacks to notify on config changes
_reload_callbacks = []

def register_reload_callback(callback: Callable[[Dict[str, Any], Dict[str, Any]], None]):
    """Register a callback to be called when configuration is reloaded.
    
    Args:
        callback: Function to call with (old_config, new_config) as arguments
    """
    _reload_callbacks.append(callback)

def _notify_callbacks(old_config: Dict[str, Any], new_config: Dict[str, Any]):
    """Notify all callbacks about config changes"""
    for callback in _reload_callbacks:
        try:
            callback(old_config, new_config)
        except Exception as e:
            print(f"Error in config reload callback: {e}")

def start_auto_reload_thread():
    """Start a background thread that checks for config changes periodically"""
    def _reload_worker():
        # Store the last modification time of this file
        last_modified = os.path.getmtime(__file__)
        
        while auto_reload_enabled:
            try:
                current_mtime = os.path.getmtime(__file__)
                
                if current_mtime > last_modified:
                    # Config file has changed, reload it
                    old_config = config.copy()
                    
                    print("Configuration file changed, reloading...")
                    
                    # Use importlib to reload this module
                    import config as config_module
                    importlib.reload(config_module)
                    
                    # Update timestamp
                    last_modified = current_mtime
                    
                    print("Configuration reloaded.")
                    _notify_callbacks(old_config, config_module.config)
                    
            except Exception as e:
                print(f"Error checking/reloading config: {e}")
                
            time.sleep(reload_interval)
    
    thread = threading.Thread(target=_reload_worker, daemon=True)
    thread.start()
    return thread

def stop_auto_reload():
    """Stop the auto-reload functionality"""
    global auto_reload_enabled
    auto_reload_enabled = False

def print_masked_config():
    """Print the current configuration with sensitive values masked"""
    masked_config = config.copy()
    # Mask sensitive values
    for key in ['OPENAI_API_KEY', 'TTS_API_KEY']:
        if key in masked_config and masked_config[key]:
            masked_config[key] = 'xxxx' + masked_config[key][-4:] if len(masked_config[key]) > 4 else '****'
    
    print(json.dumps(masked_config, indent=2, default=str))

# Print warnings if running this file directly
if __name__ == "__main__":
    warnings = validate_config()
    if warnings:
        print("Configuration warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Configuration is valid.")
        
    # Example of running with auto-reload in development
    if os.getenv('DEV_AUTO_RELOAD', 'False').lower() == 'true':
        reload_thread = start_auto_reload_thread()
        
        # Example callback
        def config_changed(old_config, new_config):
            print("Configuration changed!")
            # You could check for specific changes:
            for key in old_config:
                if key in new_config and old_config[key] != new_config[key]:
                    print(f"  - {key} changed")
        
        # Register callback
        register_reload_callback(config_changed)
        
        print("Config auto-reload running. Edit config.py to test.")
        print("Press Ctrl+C to exit.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping auto-reload.")
            stop_auto_reload()
    else:
        # Just print the config
        print("\nCurrent configuration:")
        print_masked_config() 
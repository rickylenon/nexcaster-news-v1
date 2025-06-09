# Configuration for Nexcaster News Report Generator

LANGUAGE = "Filipino"

# News segment types and their properties
SEGMENT_TYPES = {
    "opening": {
        "display_name": "Opening Greeting",
        "description": "Introduction and greeting to viewers with time, date, and location",
        "default_duration": 15.0,
        "template": "Good morning/afternoon/evening, [Location]. It's [Time] on this [Day], [Date], here in [Region]."
    },
    "summary": {
        "display_name": "News Summary",
        "description": "Brief overview of today's top stories",
        "default_duration": 20.0,
        "template": "Here are today's top stories..."
    },
    "headline": {
        "display_name": "Breaking News Headline",
        "description": "Important breaking news announcement",
        "default_duration": 10.0,
        "template": "Breaking news..."
    },
    "news": {
        "display_name": "News Report",
        "description": "Individual news story with details",
        "default_duration": 30.0,
        "template": "In other news..."
    },
    "closing": {
        "display_name": "Closing Remarks",
        "description": "Closing statements and sign-off",
        "default_duration": 15.0,
        "template": "That's all for now. Thank you for watching [Station]. I'm [Anchor], and we'll see you next time."
    }
}

# Default news report structure
DEFAULT_SEGMENT_ORDER = [
    "opening",
    "summary", 
    "news",
    "closing"
]

# Location and station information
STATION_INFO = {
    "station_name": "Nexcaster News",
    "location": "Pulilan",
    "region": "Bulacan",
    "anchor_name": "News Anchor",
    "timezone": "Asia/Manila"
}

# LLM Configuration for script generation
LLM_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": """You are a professional news script writer for Nexcaster News, a local TV news station in Pulilan, Bulacan. 
    
Your task is to generate engaging, professional, and informative news scripts based on provided news content. 

Guidelines:
1. Use a conversational but authoritative tone
2. Include relevant local context when applicable
3. Keep segments within the specified duration
4. Ensure smooth transitions between segments - NO repetitive greetings
5. Use clear, concise language appropriate for television
6. Include time references and location mentions when relevant
7. Make the content engaging for local viewers
8. Maintain broadcast continuity - avoid starting each segment with greetings
9. Use natural transitions like "Sa iba pang balita..." or "Samantala..."
10. Focus on delivering news content, not introductory pleasantries"""
}

# Audio/TTS Configuration
TTS_USE = "GOOGLE"
TTS_CONFIG_OPENAI = {
    "voice": "alloy",  # OpenAI TTS voice (works well with Filipino)
    "speed": 0.9,      # Slightly slower for Filipino pronunciation clarity
    "output_format": "mp3",
    "model": "tts-1-hd"  # Higher quality model
}
TTS_CONFIG_GOOGLE = {
    "voice": "alloy",  # OpenAI TTS voice (works well with Filipino)
    "speed": 0.9,      # Slightly slower for Filipino pronunciation clarity
    "output_format": "mp3",
    "model": "tts-1-hd"  # Higher quality model
}

# Subtitle/Timing Configuration
SUBTITLE_CONFIG = {
    "words_per_minute": 150,  # Average speaking rate
    "pause_duration": 0.5,    # Pause between sentences
    "segment_gap": 1.0        # Gap between segments
}

print("Configuration loaded successfully")
print(f"Available segment types: {list(SEGMENT_TYPES.keys())}")
print(f"Station: {STATION_INFO['station_name']} - {STATION_INFO['location']}, {STATION_INFO['region']}") 
# Configuration for Nexcaster News Report Generator

LANGUAGE = "Filipino"

# News segment types and their properties
SEGMENT_TYPES = {
    "opening": {
        "display_name": "Opening Greeting",
        "description": "Introduction and greeting to viewers with time, date, and location",
        "default_duration": 15.0,
        "template": "Good morning/afternoon/evening, [Location]. It is now [Time] on this [Day], [Date], here in [Municipality]."
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


# Location and station information
STATION_INFO = {
    "station_name": "Nexcaster News",
    "location": "Pulilan",
    "region": "Bulacan",
    "anchor_name": "Matilde",
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
9. Focus on delivering news content, not introductory pleasantries"""
}

# Audio/TTS Configuration
TTS_USE = "ELEVENLABS"  # Options: "GOOGLE", "OPENAI", "ELEVENLABS"
TTS_CONFIG_OPENAI = {
    "voice": "alloy",  # OpenAI TTS voice (works well with Filipino)
    "speed": 0.9,      # Slightly slower for Filipino pronunciation clarity
    "output_format": "mp3",
    "model": "tts-1-hd",  # Higher quality model
}
TTS_CONFIG_GOOGLE = {
    "language_code": "en-US",  # Filipino (Philippines), en-US, fil-PH
    "voice_name": "en-US-Chirp3-HD-Achernar",  # Filipino female voice, en-US-Chirp3-HD-Achernar, fil-PH-Standard-A
    "voice_gender": "FEMALE",
    "speaking_rate": 0.9,  # Slightly slower for clarity
    "pitch": 0.0,  # Normal pitch
    "output_format": "mp3",
    "audio_encoding": "MP3",
}
TTS_CONFIG_ELEVENLABS = {
    "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Adam voice (good for news), use "EXAVITQu4vr4xnSDxMaL" for Bella (female), use pNInz6obpgDQGcFmaJgB for Adam (male)
    "model_id": "eleven_flash_v2_5",  # Supports Filipino and English
    "voice_settings": {
        "stability": 0.75,    # How stable the voice is (0.0-1.0)
        "similarity_boost": 0.8,  # How similar to the original voice (0.0-1.0)  
        "style": 0.5,         # Style exaggeration (0.0-1.0)
        "use_speaker_boost": True  # Enhance speaker similarity
    },
    "output_format": "mp3_44100_128",  # mp3_22050_32, mp3_44100_64, mp3_44100_128, mp3_44100_192
    "chunk_length_schedule": [120, 160, 250, 370],  # Text chunk sizes for longer texts
}

USE_REPLACEMENTS = True
# Filipino Text Processing Configuration
FILIPINO_TEXT_PROCESSING = {
    # Common pronunciation improvements for Filipino TTS
    "replacements": {
        "Pulilan, Bulacan": "Pulilan",
        # # Basic Filipino pronunciation improvements
        "Brgy.": "Barangay",
        "Barangay.": "Barangay",
        "Brgy": "Barangay",
        
        # # Title and name abbreviations (should come before street abbreviations)
        "Ms.": "Miss",
        "Mr.": "Mister", 
        "Mrs.": "Missis",
        "Dr.": "Doctor",
        "Prof.": "Professor",
        "Atty.": "Attorney",
        "Engr.": "Engineer",
        "Hon.": "Honorable",
        "Rev.": "Reverend",
        "Fr.": "Father",
        "Sr.": "Sister",
        "Br.": "Brother",
        
        # # Saints and religious abbreviations (more specific first)
        "Sto. Cristo": "Santo Cristo",
        "Sto.": "Santo",
        "Sta.": "Santa",
        
        # # Street and location abbreviations
        "St.": "Street",
        "Ave.": "Avenue",
        "Rd.": "Road",
        "Blvd.": "Boulevard",
        
        # # Government abbreviations to full words
        "LGU": "Local Government Unit",
        "DOH": "Department of Health", 
        "DILG": "Department of the Interior and Local Government",
        "PNP": "Philippine National Police",
        "DPWH": "Department of Public Works and Highways",
        "DepEd": "Department of Education",
        "DTI": "Department of Trade and Industry",
        "DOT": "Department of Tourism",
        "DA": "Department of Agriculture",
        "DSWD": "Department of Social Welfare and Development",
        "BFP": "Bureau of Fire Protection",
        "MMDA": "Metropolitan Manila Development Authority",
        "DOTr": "Department of Transportation",
        
        # # Common institutional abbreviations
        "NGO": "non-government organization",
        "CEO": "chief executive officer",
        "COO": "chief operating officer", 
        "CFO": "chief financial officer",
        "HR": "human resources",
        "IT": "information technology",
        "PR": "public relations",
        "GPS": "global positioning system",
        "SMS": "text message",
        "ATM": "automated teller machine",
        "PWD": "person with disability",
        "OFW": "overseas Filipino worker",
        
        # # Time and date abbreviations
        "AM": "ng umaga",
        "PM": "ng hapon",
        "Mon.": "Lunes",
        "Tue.": "Martes", 
        "Wed.": "Miyerkules",
        "Thu.": "Huwebes",
        "Fri.": "Biyernes",
        "Sat.": "Sabado",
        "Sun.": "Linggo",
        "Jan.": "Enero",
        "Feb.": "Pebrero",
        "Mar.": "Marso", 
        "Apr.": "Abril",
        "May": "Mayo",
        "Jun.": "Hunyo",
        "Jul.": "Hulyo",
        "Aug.": "Agosto",
        "Sep.": "Septembre",
        "Oct.": "Oktubre", 
        "Nov.": "Nobembre",
        "Dec.": "Disembre",
        
        # # Measurement units
        "km": "kilometro",
        "kg": "kilo",
        "lbs": "pounds",
        "ft": "feet",
        "sq.m.": "square meters",
        
        # # Currency
        "PHP": "peso",
        "USD": "US dollar",
        
        # # Common symbols to words
        # "&": "at",
        # "%": "porsyento",
        # "No.": "numero",
        # "#": "numero",
        # "@": "sa",
        # "hapon": "apon",
        # " ng ": " nang ",
        # "ñ":"n-y",
        # "hayop":"ha-yop",
        # "handa":"han-da",
        # "kinuha":"kinu-ha",
    },
    
    # Address formatting rules to make them sound less robotic
    "address_patterns": [
        # Pattern: "123 Street Name, Barangay Name, City Name"
        # Replace with: "Street Name sa Barangay Name, City Name"
        {
            "pattern": r"(\d+)\s+([^,]+),\s*(Brgy\.?\s*|Barangay\s*)([^,]+),\s*([^,]+)",
            "replacement": r"\2 sa Barangay \4, \5"
        },
        # Pattern: "Barangay Name, City Name, Province Name"  
        # Keep as is but ensure proper spacing
        {
            "pattern": r"(Barangay\s+[^,]+),\s*([^,]+),\s*([^,]+)",
            "replacement": r"\1, \2, \3"
        }
    ],
    
    # Words/phrases that should be spelled out for clarity
    "spell_out": {
        "COVID-19": "COVID nineteen",
        "2024": "dalawang libo't dalawampu't apat",
        "2023": "dalawang libo't dalawampu't tatlo", 
        "24/7": "dalawampu't apat na oras",
        "911": "nine-one-one",
        "8888": "citizen's complaint hotline",
    },
    
    # Special characters to remove or replace
    "special_chars": {
        """: '"',
        """: '"', 
        "'": "'",
        "'": "'",
        "…": "...",
        "–": "-",
        "—": "-",
        "°": " degrees",
        "₱": "piso ",
    }
}


print("Configuration loaded successfully")
print(f"Available segment types: {list(SEGMENT_TYPES.keys())}")
print(f"Station: {STATION_INFO['station_name']} - {STATION_INFO['location']}, {STATION_INFO['region']}") 
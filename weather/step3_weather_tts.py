#!/usr/bin/env python3
"""
Step 3: Weather TTS (Text-to-Speech) Generator
This script generates audio files from weather_scripts.json using configurable TTS providers
"""

import os
import json
import openai
from pathlib import Path
from datetime import datetime
from google.cloud import texttospeech
from pydub import AudioSegment
from dotenv import load_dotenv
from config import TTS_CONFIG, LANGUAGE, OPENAI_API_KEY

def get_media_files_for_segment(segment_type):
    """Get media files associated with a weather segment"""
    media_dir = os.path.join('generated', 'media')
    media_files = []
    
    if not os.path.exists(media_dir):
        return media_files
    
    # Map segment types to potential media file patterns
    segment_to_media_map = {
        'weather_map1': ['weather_map1.webm'],
        'weather_map2': ['weather_map2.webm'],
        'card_temperature': ['card-temperature.webm'],
        'card_feels_like': ['card-feels-like.webm'],
        'card_cloud_cover': ['card-cloud-cover.webm'],
        'card_precipitation': ['card-precipitation.webm'],
        'card_wind': ['card-wind.webm'],
        'card_humidity': ['card-humidity.webm'],
        'card_uv': ['card-uv.webm'],
        'card_aqi': ['card-aqi.webm'],
        'card_visibility': ['card-visibility.webm'],
        'card_pressure': ['card-pressure.webm'],
        'card_sun': ['card-sun.webm'],
        'card_moon': ['card-moon.webm'],
        'card_current': ['card-current.webm'],
        'card_hourly': ['card-hourly.webm'],
        'weather_overview': ['weather_overview.webm'],
        'weather_current_overview': ['weather_current_overview.webm']
    }
    
    # Get potential file names for this segment
    potential_files = segment_to_media_map.get(segment_type, [])
    
    for media_filename in potential_files:
        media_path = os.path.join(media_dir, media_filename)
        if os.path.exists(media_path):
            try:
                # Get file size in MB
                file_size_bytes = os.path.getsize(media_path)
                file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
                
                media_info = {
                    "video": media_filename,
                    "path": os.path.join("media", media_filename).replace("\\", "/"),
                    "type": f"{segment_type}_video",
                    "original_name": media_filename,
                    "size_mb": file_size_mb
                }
                media_files.append(media_info)
                
                print(f"    📹 Found media: {media_filename} ({file_size_mb} MB)")
                
            except Exception as e:
                print(f"    ⚠️  Warning: Could not process media file {media_filename}: {e}")
    
    return media_files

# Load environment variables from .env file
load_dotenv()
print(f"Loaded environment variables from .env file")

# Fix PATH to include ffmpeg location
if "/opt/homebrew/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '')}"
    print(f"Added Homebrew paths to PATH for ffmpeg access")

# Print TTS configuration
print(f"TTS Provider: {TTS_CONFIG['provider']}")
print(f"Language: {LANGUAGE}")

# Import and configure providers based on TTS_CONFIG
if TTS_CONFIG['provider'] == 'elevenlabs':
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        print(f"Using ElevenLabs Text-to-Speech API")
    except ImportError:
        print("Error: ElevenLabs library not installed. Install with: pip install elevenlabs")
        exit(1)
elif TTS_CONFIG['provider'] == 'openai':
    print(f"Using OpenAI Text-to-Speech API")
elif TTS_CONFIG['provider'] == 'google':
    print(f"Using Google Cloud Text-to-Speech API")
    
    # Set up Google Cloud credentials if needed
    credentials_file = "../promising-cairn-283201-f7bb9e4c5c4f.json"
    if os.path.exists(credentials_file):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(credentials_file)
        print(f"Google Cloud credentials set: {os.path.abspath(credentials_file)}")
    elif "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable not set!")
        print("Please set it manually or place the credentials file in the project directory.")
else:
    print(f"Error: Unsupported TTS provider: {TTS_CONFIG['provider']}")
    exit(1)

def load_weather_scripts():
    """Load weather scripts from generated/weather_scripts.json"""
    scripts_path = os.path.join('generated', 'weather_scripts.json')
    if not os.path.exists(scripts_path):
        print(f"Error: {scripts_path} not found!")
        print("Please run step2_weather_scripts.py first to generate weather scripts.")
        return None
    
    with open(scripts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract scripts array from the weather data structure
    scripts = data.get('scripts', [])
    print(f"Loaded {len(scripts)} weather script segments from {scripts_path}")
    return scripts

def preprocess_script_for_tts(script_text, language):
    """Preprocess script text for better TTS pronunciation using news-style processing"""
    import html
    import codecs
    import re
    
    # First, fix Unicode encoding issues
    processed_text = script_text.strip()
    
    # Fix Unicode escape sequences like \u00f1
    try:
        processed_text = codecs.decode(processed_text, 'unicode_escape')
    except:
        try:
            processed_text = processed_text.encode().decode('unicode_escape')
        except:
            pass  # Keep original if decoding fails
    
    # Also try HTML entity decoding
    try:
        processed_text = html.unescape(processed_text)
    except:
        pass
    
    if language.lower() == "filipino":
        print(f"Applying comprehensive Filipino text preprocessing for better TTS")
        
        # Enhanced Filipino text processing (from news config)
        filipino_replacements = {
            "Pulilan, Bulacan": "Pulilan",
            "Brgy.": "Barangay",
            "Brgy": "Barangay",
            "Ms.": "Miss",
            "Mr.": "Mister", 
            "Mrs.": "Missis",
            "Dr.": "Doctor",
            "Sto.": "Santo",
            "Sta.": "Santa",
            "St.": "Street",
            "Ave.": "Avenue",
            "AM": "ng umaga",
            "PM": "ng hapon",
            "km": "kilometro",
            "kg": "kilo",
            "PHP": "peso",
            "USD": "US dollar",
            "&": "at",
            "%": "porsyento",
            "No.": "numero",
            "°C": " degrees Celsius",
            "°F": " degrees Fahrenheit",
            "km/h": " kilometers per hour",
            "mph": " miles per hour",
            "UV": "U V",
            "COVID-19": "COVID nineteen",
            "24/7": "dalawampu't apat na oras",
            "911": "nine-one-one",
            """: '"',
            """: '"', 
            "'": "'",
            "'": "'",
            "…": "...",
            "–": "-",
            "—": "-",
            "₱": "piso ",
        }
        
        # Apply replacements in order (longer phrases first to avoid partial replacements)
        sorted_replacements = sorted(filipino_replacements.items(), key=lambda x: len(x[0]), reverse=True)
        for original, replacement in sorted_replacements:
            processed_text = processed_text.replace(original, replacement)
        
        # Enhanced pauses for better pacing
        processed_text = processed_text.replace(". ", ". ... ")
        processed_text = processed_text.replace("! ", "! ... ")
        processed_text = processed_text.replace("? ", "? ... ")
        processed_text = processed_text.replace(", ", ", .. ")
        processed_text = processed_text.replace("; ", "; .. ")
        processed_text = processed_text.replace("ng ", "ng .. ")
        
        # Address pattern improvements
        # Pattern: "123 Street Name, Barangay Name, City Name"
        # Replace with: "Street Name sa Barangay Name, City Name"
        processed_text = re.sub(
            r'(\d+)\s+([^,]+),\s*(Brgy\.?\s*|Barangay\s*)([^,]+),\s*([^,]+)',
            r'\2 sa Barangay \4, \5',
            processed_text
        )
    
    return processed_text

def generate_audio_with_elevenlabs_tts(segment, output_dir):
    """Generate audio file using ElevenLabs Text-to-Speech"""
    print(f"Generating audio with ElevenLabs TTS for: {segment['display_name']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename - use unique identifier to avoid overwriting
    segment_id = f"{segment['segment_type']}_{segment.get('display_order', 0)}"
    audio_filename = f"{segment_id}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Get API key
        api_key = os.environ.get("ELEVEN_API_KEY")
        if not api_key:
            raise Exception("ELEVEN_API_KEY environment variable not set!")
        
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE)
        print(f"Preprocessed script: {processed_script[:100]}..." if len(processed_script) > 100 else processed_script)
        
        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=api_key)
        
        # Configure voice settings
        voice_settings = VoiceSettings(
            stability=TTS_CONFIG["elevenlabs"]["voice_settings"]["stability"],
            similarity_boost=TTS_CONFIG["elevenlabs"]["voice_settings"]["similarity_boost"],
            style=TTS_CONFIG["elevenlabs"]["voice_settings"]["style"],
            use_speaker_boost=TTS_CONFIG["elevenlabs"]["voice_settings"]["use_speaker_boost"]
        )
        
        print(f"Using voice ID: {TTS_CONFIG['elevenlabs']['voice_id']}")
        print(f"Using model: {TTS_CONFIG['elevenlabs']['model_id']}")
        
        # Generate the speech using the correct API
        audio_data = client.text_to_speech.convert(
            text=processed_script,
            voice_id=TTS_CONFIG["elevenlabs"]["voice_id"],
            model_id=TTS_CONFIG["elevenlabs"]["model_id"],
            voice_settings=voice_settings,
            output_format=TTS_CONFIG["elevenlabs"]["output_format"]
        )
        
        # Save audio file
        with open(audio_path, "wb") as f:
            # audio_data is a generator, so we need to iterate through it
            for chunk in audio_data:
                f.write(chunk)
        
        print(f"Audio saved: {audio_path}")
        
        # Measure actual duration of generated audio file
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment['duration']}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment["duration"]  # Fallback to estimated
        
        # Get associated media files
        media_files = get_media_files_for_segment(segment["segment_type"])
        
        result = {
            "segment_type": segment["segment_type"],
            "display_name": segment["display_name"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "headline": segment.get("headline", ""),
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": TTS_CONFIG["elevenlabs"]["voice_id"],
            "tts_service": "ElevenLabs"
        }
        
        # Add media information if available
        if media_files:
            result["media"] = media_files
            
        return result
        
    except Exception as e:
        print(f"Error generating audio with ElevenLabs TTS for {segment['segment_type']}: {e}")
        return None

def generate_audio_with_google_tts(segment, output_dir):
    """Generate audio file using Google Cloud Text-to-Speech"""
    print(f"Generating audio with Google TTS for: {segment['display_name']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename - use unique identifier to avoid overwriting
    segment_id = f"{segment['segment_type']}_{segment.get('display_order', 0)}"
    audio_filename = f"{segment_id}.{TTS_CONFIG['google']['output_format']}"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE)
        print(f"Preprocessed script: {processed_script[:100]}..." if len(processed_script) > 100 else processed_script)
        
        # Initialize Google Cloud TTS client
        client = texttospeech.TextToSpeechClient()
        
        # Configure the text input
        synthesis_input = texttospeech.SynthesisInput(text=processed_script)
        
        # Configure the voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code=TTS_CONFIG["google"]["language_code"],
            name=TTS_CONFIG["google"]["voice_name"],
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, TTS_CONFIG["google"]["voice_gender"])
        )
        
        # Configure the audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=getattr(texttospeech.AudioEncoding, TTS_CONFIG["google"]["audio_encoding"]),
            speaking_rate=TTS_CONFIG["google"]["speaking_rate"],
            pitch=TTS_CONFIG["google"]["pitch"]
        )
        
        # Generate the speech
        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        # Save audio file
        with open(audio_path, "wb") as out:
            out.write(response.audio_content)
        
        print(f"Audio saved: {audio_path}")
        
        # Measure actual duration of generated audio file
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment['duration']}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment["duration"]  # Fallback to estimated
        
        # Get associated media files
        media_files = get_media_files_for_segment(segment["segment_type"])
        
        result = {
            "segment_type": segment["segment_type"],
            "display_name": segment["display_name"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "headline": segment.get("headline", ""),
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": TTS_CONFIG["google"]["voice_name"],
            "tts_service": "Google Cloud"
        }
        
        # Add media information if available
        if media_files:
            result["media"] = media_files
            
        return result
        
    except Exception as e:
        print(f"Error generating audio with Google TTS for {segment['segment_type']}: {e}")
        return None

def generate_audio_with_openai_tts(segment, output_dir):
    """Generate audio file using OpenAI Text-to-Speech"""
    print(f"Generating audio with OpenAI TTS for: {segment['display_name']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename - use unique identifier to avoid overwriting
    segment_id = f"{segment['segment_type']}_{segment.get('display_order', 0)}"
    audio_filename = f"{segment_id}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Select appropriate voice for language
        voice = TTS_CONFIG["openai"]["voice"]
        if LANGUAGE.lower() == "filipino":
            # Use alloy voice which works well with Filipino
            # OpenAI TTS doesn't have specific Filipino voices yet, but alloy handles it reasonably
            voice = "alloy"
            print(f"Using voice '{voice}' for Filipino language")
        
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE)
        print(f"Preprocessed script: {processed_script[:100]}..." if len(processed_script) > 100 else processed_script)
        
        # OpenAI TTS API call
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model=TTS_CONFIG["openai"]["model"],
            voice=voice,
            input=processed_script,
            speed=TTS_CONFIG["openai"]["speed"]
        )
        
        # Save audio file
        response.stream_to_file(audio_path)
        print(f"Audio saved: {audio_path}")
        
        # Measure actual duration of generated audio file
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment['duration']}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment["duration"]  # Fallback to estimated
        
        # Get associated media files
        media_files = get_media_files_for_segment(segment["segment_type"])
        
        result = {
            "segment_type": segment["segment_type"],
            "display_name": segment["display_name"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "headline": segment.get("headline", ""),
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": voice,
            "tts_service": "OpenAI"
        }
        
        # Add media information if available
        if media_files:
            result["media"] = media_files
            
        return result
        
    except Exception as e:
        print(f"Error generating audio with OpenAI TTS for {segment['segment_type']}: {e}")
        return None

def generate_audio_segment(segment, output_dir):
    """Generate audio segment using the configured TTS provider"""
    if TTS_CONFIG['provider'] == 'elevenlabs':
        return generate_audio_with_elevenlabs_tts(segment, output_dir)
    elif TTS_CONFIG['provider'] == 'openai':
        return generate_audio_with_openai_tts(segment, output_dir)
    elif TTS_CONFIG['provider'] == 'google':
        return generate_audio_with_google_tts(segment, output_dir)
    else:
        print(f"Error: Unsupported TTS provider: {TTS_CONFIG['provider']}")
        return None

def combine_audio_segments(audio_results, output_dir):
    """Combine all audio segments into a single combined_weather.mp3 file"""
    print("\n=== Combining Weather Audio Segments ===")
    
    if not audio_results:
        print("No audio files to combine!")
        return None
    
    # Load the original scripts to get display_order
    scripts = load_weather_scripts()
    if not scripts:
        print("Error: Could not load scripts to determine display order!")
        return None
    
    # Create a mapping of segment_type to display_order
    display_order_map = {}
    for script in scripts:
        display_order_map[script['segment_type']] = script.get('display_order', 999)
    
    # Sort audio results by display_order using the mapping
    segment_order = []
    for result in audio_results:
        segment_type = result['segment_type']
        display_order = display_order_map.get(segment_type, 999)
        segment_order.append((display_order, result))
        print(f"  Found segment: {segment_type} with display_order: {display_order}")
    
    # Sort by display_order
    segment_order.sort(key=lambda x: x[0])
    
    print(f"Weather segments will be combined in this order:")
    for order, result in segment_order:
        print(f"  {order}: {result['display_name']} ({result['segment_type']})")
    
    try:
        combined_audio = AudioSegment.empty()
        total_duration = 0
        
        print("Combining weather segments in order:")
        for order, result in segment_order:
            audio_path = result['audio_path']
            display_name = result['display_name']
            
            if os.path.exists(audio_path):
                print(f"  {order}: {display_name} - {audio_path}")
                
                # Load audio segment
                audio_segment = AudioSegment.from_mp3(audio_path)
                
                # Add a small pause between segments (1 second)
                if len(combined_audio) > 0:
                    pause = AudioSegment.silent(duration=1000)  # 1 second pause
                    combined_audio += pause
                
                # Add the audio segment
                combined_audio += audio_segment
                total_duration += len(audio_segment) / 1000.0  # Convert to seconds
                
            else:
                print(f"  WARNING: Audio file not found: {audio_path}")
        
        # Export combined audio
        combined_path = os.path.join(output_dir, "combined_weather.mp3")
        combined_audio.export(combined_path, format="mp3")
        
        # Measure actual combined duration
        actual_combined_duration = len(combined_audio) / 1000.0  # Convert to seconds
        
        print(f"\n✅ Combined weather audio created: {combined_path}")
        print(f"📊 Measured combined duration: {actual_combined_duration:.3f} seconds ({actual_combined_duration/60:.2f} minutes)")
        print(f"📊 Sum of segments: {total_duration:.3f} seconds (difference: {actual_combined_duration - total_duration:.3f}s)")
        print(f"🎵 Total segments: {len(segment_order)}")
        
        return {
            "combined_file": "combined_weather.mp3",
            "combined_path": combined_path,
            "total_duration": round(actual_combined_duration, 3),
            "segment_count": len(segment_order),
            "segments_included": [result['display_name'] for _, result in segment_order]
        }
        
    except Exception as e:
        print(f"❌ Error combining weather audio segments: {e}")
        return None

def main():
    """Main function to generate weather TTS audio"""
    import sys
    
    # Check for combine-only flag
    combine_only = "--combine-only" in sys.argv or "-c" in sys.argv
    
    print("=== Nexcaster Weather TTS Generator ===")
    if combine_only:
        print("Step 3: Combining existing weather audio files (SKIP GENERATION)")
    else:
        print("Step 3: Generating audio from weather scripts")
    print(f"TTS Service: {TTS_CONFIG['provider']}")
    print(f"Language: {LANGUAGE}")
    print(f"Voice: {TTS_CONFIG['openai']['voice'] if TTS_CONFIG['provider'] == 'openai' else TTS_CONFIG['elevenlabs']['voice_id']}")
    print(f"Speed: {TTS_CONFIG['openai']['speed'] if TTS_CONFIG['provider'] == 'openai' else TTS_CONFIG['elevenlabs']['voice_settings']['similarity_boost']}")
    print(f"Output format: mp3")
    print()
    
    # Load weather scripts
    scripts = load_weather_scripts()
    if not scripts:
        return
    
    # Create audio output directory
    audio_dir = os.path.join('generated', 'audio')
    
    # Generate audio for each segment (or skip if combine-only)
    audio_results = []
    if combine_only:
        print("🔄 Skipping generation - looking for existing weather audio files...")
        # Create audio_results from existing files
        for segment in scripts:
            segment_id = f"{segment['segment_type']}_{segment.get('display_order', 0)}"
            audio_filename = f"{segment_id}.mp3"
            audio_path = os.path.join(audio_dir, audio_filename)
            
            if os.path.exists(audio_path):
                print(f"  ✅ Found: {audio_filename}")
                
                # Measure actual duration of existing audio file
                try:
                    audio_segment = AudioSegment.from_file(audio_path)
                    actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
                    print(f"    📏 Measured duration: {actual_duration:.3f}s (estimated was: {segment.get('duration', 0)}s)")
                except Exception as e:
                    print(f"    ⚠️  Warning: Could not measure audio duration: {e}")
                    actual_duration = segment.get("duration", 0)  # Fallback to estimated
                
                # Get associated media files
                media_files = get_media_files_for_segment(segment["segment_type"])
                
                result = {
                    "segment_type": segment["segment_type"],
                    "display_name": segment["display_name"],
                    "audio_file": audio_filename,
                    "audio_path": audio_path,
                    "script": segment["script"],
                    "headline": segment.get("headline", ""),
                    "duration": round(actual_duration, 3),
                    "language": LANGUAGE,
                    "voice_used": TTS_CONFIG['openai']['voice'] if TTS_CONFIG['provider'] == 'openai' else TTS_CONFIG['elevenlabs']['voice_id'],
                    "tts_service": TTS_CONFIG['provider']
                }
                
                # Add media information if available
                if media_files:
                    result["media"] = media_files
                    
                audio_results.append(result)
            else:
                print(f"  ❌ Missing: {audio_filename}")
    else:
        for segment in scripts:
            result = generate_audio_segment(segment, audio_dir)
            if result:
                audio_results.append(result)
    
    # Combine all audio segments into one file
    combined_result = combine_audio_segments(audio_results, audio_dir)
    
    # Calculate start and end times for each segment
    cumulative_time = 0
    updated_audio_results = []
    
    print("\n=== Calculating Weather Segment Timing (with 1s pauses) ===")
    for i, result in enumerate(audio_results):
        start_time = cumulative_time
        end_time = start_time + result['duration']
        
        # Add timing information to the segment
        updated_result = result.copy()
        updated_result['start_time'] = round(start_time, 3)
        updated_result['end_time'] = round(end_time, 3)
        
        print(f"  {result['display_name']}: {start_time:.3f}s - {end_time:.3f}s (duration: {result['duration']:.3f}s)")
        
        updated_audio_results.append(updated_result)
        cumulative_time = end_time
        
        # Add 1-second pause after each segment (except the last one)
        if i < len(audio_results) - 1:
            cumulative_time += 1.0  # Add 1-second pause
            print(f"    + 1.0s pause → next starts at {cumulative_time:.3f}s")
    
    print(f"Total manifest duration with pauses: {cumulative_time:.3f}s ({cumulative_time/60:.2f} minutes)")
    if combined_result:
        print(f"Combined audio duration: {combined_result['total_duration']:.3f}s")
        print(f"Timing match: {abs(cumulative_time - combined_result['total_duration']):.3f}s difference")
    
    # Update metadata to include combined file info and timing
    final_metadata = {
        "individual_segments": updated_audio_results,
        "combined_audio": combined_result,
        "generation_info": {
            "tts_service": TTS_CONFIG['provider'],
            "language": LANGUAGE,
            "total_segments": len(updated_audio_results),
            "total_duration": round(cumulative_time, 3),
            "timestamp": datetime.now().isoformat(),
            "content_type": "weather_forecast",
            "voice_used": TTS_CONFIG['openai']['voice'] if TTS_CONFIG['provider'] == 'openai' else TTS_CONFIG['elevenlabs']['voice_id'],
            "speed": TTS_CONFIG['openai']['speed'] if TTS_CONFIG['provider'] == 'openai' else TTS_CONFIG['elevenlabs']['voice_settings']['similarity_boost']
        }
    }
    
    # Save weather audio metadata
    weather_manifest_path = os.path.join('generated', 'weather_manifest.json')
    with open(weather_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎯 Weather audio generation complete!")
    print(f"Generated {len(updated_audio_results)} individual weather audio files in {LANGUAGE}")
    print(f"Audio files saved in: {audio_dir}")
    print(f"Manifest saved to: {weather_manifest_path}")
    
    if combined_result:
        print(f"\n🎵 Combined Weather Audio:")
        print(f"  File: {combined_result['combined_file']}")
        print(f"  Duration: {combined_result['total_duration']:.1f}s ({combined_result['total_duration']/60:.1f} minutes)")
        print(f"  Segments: {combined_result['segment_count']}")
    
    # Display summary of generated files with timing
    print(f"\n📁 Generated weather audio segments with timing:")
    for result in updated_audio_results:
        service_info = f"({result['tts_service']}: {result['voice_used']})"
        timing_info = f"[{result['start_time']:.1f}s - {result['end_time']:.1f}s]"
        headline_info = f"- \"{result['headline'][:50]}...\""
        print(f"  - {result['display_name']}: {result['audio_file']} {timing_info} {service_info} {headline_info}")

if __name__ == "__main__":
    main()

# Note: This script uses OpenAI TTS for weather content
# To use this script, you'll need to:
# 1. Set up OpenAI API key in environment variables: OPENAI_API_KEY
# 2. Install required dependencies: pip install openai pydub
# 3. Run: python step3_weather_tts.py 
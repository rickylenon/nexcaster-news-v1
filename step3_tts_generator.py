#!/usr/bin/env python3
"""
Step 3: TTS (Text-to-Speech) Generator
This script generates audio files from news_scripts.json using OpenAI TTS

python step3_tts_generator.py # will regenerate audio files
python step3_tts_generator.py --update-manifest # will only update manifest from existing audio files
"""

import os
import json
import openai
from pathlib import Path
from datetime import datetime
from google.cloud import texttospeech
from pydub import AudioSegment
from dotenv import load_dotenv
try:
    from elevenlabs import ElevenLabs, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs package not installed. ElevenLabs TTS will not be available.")
from config import TTS_USE, TTS_CONFIG_OPENAI, TTS_CONFIG_GOOGLE, TTS_CONFIG_ELEVENLABS, LANGUAGE, FILIPINO_TEXT_PROCESSING, USE_REPLACEMENTS

# Load environment variables from .env file
load_dotenv()
print(f"Loaded environment variables from .env file")

# Fix PATH to include ffmpeg location
if "/opt/homebrew/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '')}"
    print(f"Added Homebrew paths to PATH for ffmpeg access")

# Select TTS configuration based on TTS_USE setting
if TTS_USE.upper() == "GOOGLE":
    TTS_CONFIG = TTS_CONFIG_GOOGLE
    print(f"Using Google Cloud Text-to-Speech API")
    
    # Set up Google Cloud credentials if needed
    credentials_file = "promising-cairn-283201-f7bb9e4c5c4f.json"
    if os.path.exists(credentials_file):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
        print(f"Google Cloud credentials set: {credentials_file}")
    elif "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable not set!")
        print("Please set it manually or place the credentials file in the project directory.")
elif TTS_USE.upper() == "ELEVENLABS":
    TTS_CONFIG = TTS_CONFIG_ELEVENLABS
    print(f"Using ElevenLabs Text-to-Speech API")
    
    if not ELEVENLABS_AVAILABLE:
        print("Error: ElevenLabs package not installed!")
        print("Please install it using: pip install elevenlabs")
        exit(1)
    
    print(f"Using ElevenLabs API key: {os.environ.get('ELEVEN_API_KEY')}")
    # Check for ElevenLabs API key
    if not os.environ.get("ELEVEN_API_KEY"):
        print("Warning: ELEVEN_API_KEY environment variable not set!")
        print("Please set your ElevenLabs API key as an environment variable.")
else:
    TTS_CONFIG = TTS_CONFIG_OPENAI
    print(f"Using OpenAI Text-to-Speech API")

def load_news_scripts():
    """Load news scripts from generated/news_scripts.json"""
    scripts_path = os.path.join('generated', 'news_scripts.json')
    if not os.path.exists(scripts_path):
        print(f"Error: {scripts_path} not found!")
        print("Please run step 2 first to generate news scripts.")
        return None
    
    with open(scripts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} script segments from {scripts_path}")
    return data

def preprocess_script_for_tts(script_text, language, use_replacements=USE_REPLACEMENTS):
    """Preprocess script text for better TTS pronunciation"""
    import html
    import codecs
    
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
    
    if language.lower() == "filipino" and use_replacements:
        print(f"Applying Filipino text replacements for better TTS pronunciation")
        # Use centralized Filipino text processing from config
        replacements = FILIPINO_TEXT_PROCESSING["replacements"]
        
        # Apply replacements in order (longer phrases first to avoid partial replacements)
        sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        for original, replacement in sorted_replacements:
            processed_text = processed_text.replace(original, replacement)
        
        # Add brief pauses for better pacing
        processed_text = processed_text.replace(". ", ". ... ")
        processed_text = processed_text.replace("! ", "! ... ")
        processed_text = processed_text.replace("? ", "? ... ")
        processed_text = processed_text.replace(", ", ", .. ")
    elif language.lower() == "filipino" and not use_replacements:
        print(f"Skipping Filipino text replacements (disabled for this TTS service)")
    
    return processed_text

def generate_audio_with_google_tts(segment, output_dir):
    """Generate audio file using Google Cloud Text-to-Speech"""
    print(f"Generating audio with Google TTS for: {segment['segment_index']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename - use segment_index
    audio_filename = f"{segment['segment_index']}.{TTS_CONFIG['output_format']}"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE, USE_REPLACEMENTS)
        print(f"Preprocessed script: {processed_script[:100]}..." if len(processed_script) > 100 else processed_script)
        
        # Initialize Google Cloud TTS client
        client = texttospeech.TextToSpeechClient()
        
        # Configure the text input
        synthesis_input = texttospeech.SynthesisInput(text=processed_script)
        
        # Configure the voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code=TTS_CONFIG["language_code"],
            name=TTS_CONFIG["voice_name"],
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, TTS_CONFIG["voice_gender"])
        )
        
        # Configure the audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=getattr(texttospeech.AudioEncoding, TTS_CONFIG["audio_encoding"]),
            speaking_rate=TTS_CONFIG["speaking_rate"],
            pitch=TTS_CONFIG["pitch"]
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
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment.get('duration', 0)}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment.get("duration", 0)  # Fallback to 0 if not present
        
        return {
            "segment_type": segment["segment_type"],
            "segment_index": segment["segment_index"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": TTS_CONFIG["voice_name"],
            "tts_service": "Google Cloud"
        }
        
    except Exception as e:
        print(f"Error generating audio with Google TTS for {segment['segment_type']}: {e}")
        return None

def generate_audio_with_openai_tts(segment, output_dir):
    """Generate audio file using OpenAI Text-to-Speech"""
    print(f"Generating audio with OpenAI TTS for: {segment['segment_index']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename - use segment_index
    audio_filename = f"{segment['segment_index']}.{TTS_CONFIG['output_format']}"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Select appropriate voice for language
        voice = TTS_CONFIG["voice"]
        if LANGUAGE.lower() == "filipino":
            voice = "alloy"
            print(f"Using voice '{voice}' for Filipino language")
        
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE, USE_REPLACEMENTS)
        print(f"Preprocessed script: {processed_script[:100]}..." if len(processed_script) > 100 else processed_script)
        
        # OpenAI TTS API call
        client = openai.OpenAI()
        tts_model = TTS_CONFIG.get("model", "tts-1-hd")
        response = client.audio.speech.create(
            model=tts_model,
            voice=voice,
            input=processed_script,
            speed=TTS_CONFIG["speed"]
        )
        
        # Save audio file
        response.stream_to_file(audio_path)
        print(f"Audio saved: {audio_path}")
        
        # Measure actual duration of generated audio file
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment.get('duration', 0)}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment.get("duration", 0)  # Fallback to 0 if not present
        
        return {
            "segment_type": segment["segment_type"],
            "segment_index": segment["segment_index"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": voice,
            "tts_service": "OpenAI"
        }
        
    except Exception as e:
        print(f"Error generating audio with OpenAI TTS for {segment['segment_type']}: {e}")
        return None

def generate_audio_with_elevenlabs_tts(segment, output_dir):
    """Generate audio file using ElevenLabs Text-to-Speech"""
    print(f"Generating audio with ElevenLabs TTS for: {segment['segment_index']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename (ElevenLabs returns mp3) - use segment_index
    audio_filename = f"{segment['segment_index']}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE, USE_REPLACEMENTS)
        print(f"Preprocessed script: {processed_script[:100]}..." if len(processed_script) > 100 else processed_script)
        
        # Get API key
        api_key = os.environ.get("ELEVEN_API_KEY")
        if not api_key:
            raise Exception("ELEVEN_API_KEY environment variable not set!")
        
        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=api_key)
        
        # Configure voice settings
        voice_settings = VoiceSettings(
            stability=TTS_CONFIG["voice_settings"]["stability"],
            similarity_boost=TTS_CONFIG["voice_settings"]["similarity_boost"],
            style=TTS_CONFIG["voice_settings"]["style"],
            use_speaker_boost=TTS_CONFIG["voice_settings"]["use_speaker_boost"]
        )
        
        print(f"Using voice ID: {TTS_CONFIG['voice_id']}")
        print(f"Using model: {TTS_CONFIG['model_id']}")
        
        # Generate the speech using the new API
        audio_data = client.text_to_speech.convert(
            text=processed_script,
            voice_id=TTS_CONFIG["voice_id"],
            model_id=TTS_CONFIG["model_id"],
            voice_settings=voice_settings,
            output_format=TTS_CONFIG["output_format"]
        )
        
        # Save audio file
        with open(audio_path, "wb") as f:
            for chunk in audio_data:
                f.write(chunk)
        
        print(f"Audio saved: {audio_path}")
        
        # Measure actual duration of generated audio file
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment.get('duration', 0)}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment.get("duration", 0)  # Fallback to 0 if not present
        
        return {
            "segment_type": segment["segment_type"],
            "segment_index": segment["segment_index"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": TTS_CONFIG["voice_id"],
            "tts_service": "ElevenLabs"
        }
        
    except Exception as e:
        print(f"Error generating audio with ElevenLabs TTS for {segment['segment_type']}: {e}")
        return None

def generate_audio_from_script(segment, output_dir):
    """Generate audio file from a script segment using configured TTS service"""
    if TTS_USE.upper() == "GOOGLE":
        return generate_audio_with_google_tts(segment, output_dir)
    elif TTS_USE.upper() == "ELEVENLABS":
        return generate_audio_with_elevenlabs_tts(segment, output_dir)
    else:
        return generate_audio_with_openai_tts(segment, output_dir)

def update_manifest_from_audio(scripts, audio_dir):
    """Update manifest based on existing audio files and measured durations."""
    from pydub import AudioSegment
    individual_segments = []
    for i, segment in enumerate(scripts):
        audio_filename = f"{segment['segment_index']}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        if os.path.exists(audio_path):
            try:
                audio_segment = AudioSegment.from_file(audio_path)
                actual_duration = len(audio_segment) / 1000.0
            except Exception as e:
                print(f"Warning: Could not measure audio duration: {e}")
                actual_duration = 0
            individual_segments.append({
                "segment_type": segment["segment_type"],
                "segment_index": segment["segment_index"],
                "audio_path": audio_path,
                "script": segment["script"],
                "duration": round(actual_duration, 3)
            })
        else:
            print(f"  ❌ Missing: {audio_filename}")
    return individual_segments

def main():
    """Main function to generate TTS audio or update manifest only"""
    import sys
    
    update_manifest_only = "--update-manifest" in sys.argv
    
    print("=== Nexcaster News TTS Generator ===")
    if update_manifest_only:
        print("Step 3: Updating manifest from existing audio files (NO GENERATION)")
    else:
        print("Step 3: Generating audio from news scripts if missing, then updating manifest")
    print(f"TTS Service: {TTS_USE}")
    print(f"Language: {LANGUAGE}")
    if TTS_USE.upper() == "GOOGLE":
        print(f"Voice: {TTS_CONFIG['voice_name']}")
        print(f"Language Code: {TTS_CONFIG['language_code']}")
    elif TTS_USE.upper() == "ELEVENLABS":
        print(f"Voice ID: {TTS_CONFIG['voice_id']}")
        print(f"Model: {TTS_CONFIG['model_id']}")
        print(f"Stability: {TTS_CONFIG['voice_settings']['stability']}")
        print(f"Similarity Boost: {TTS_CONFIG['voice_settings']['similarity_boost']}")
    else:
        print(f"Voice: {TTS_CONFIG['voice']}")
    if TTS_USE.upper() == "ELEVENLABS":
        print(f"Output format: mp3")
    else:
        print(f"Output format: {TTS_CONFIG['output_format']}")
    print()
    
    # Load scripts
    scripts = load_news_scripts()
    if not scripts:
        return
    
    # Create audio output directory
    audio_dir = os.path.join('generated', 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    # Empty the audio output directory if not just updating manifest
    if not update_manifest_only:
        print(f"Clearing audio output directory: {audio_dir}")
        for filename in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                    print(f"  Deleted: {file_path}")
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                    print(f"  Deleted directory: {file_path}")
            except Exception as e:
                print(f"  Failed to delete {file_path}: {e}")
    
    audio_results = []
    if update_manifest_only:
        print("🔄 Only updating manifest from existing audio files...")
        audio_results = update_manifest_from_audio(scripts, audio_dir)
    else:
        for segment in scripts:
            audio_filename = f"{segment['segment_index']}.mp3"
            audio_path = os.path.join(audio_dir, audio_filename)
            if os.path.exists(audio_path):
                print(f"  ✅ Found: {audio_filename}")
            else:
                result = generate_audio_from_script(segment, audio_dir)
                if result:
                    print(f"  ✅ Generated: {audio_filename}")
        # After generation, always update manifest from audio files
        audio_results = update_manifest_from_audio(scripts, audio_dir)
    
    # Save audio metadata (manifest)
    news_manifest_path = os.path.join('generated', 'news_manifest.json')
    with open(news_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(audio_results, f, indent=2, ensure_ascii=False)
    print(f"\n🎯 Manifest updated!")
    print(f"Manifest saved to: {news_manifest_path}")
    print(f"Total segments: {len(audio_results)}")
    print(f"\n📁 Generated audio segments with timing:")
    for result in audio_results:
        print(f"  - {result['segment_index']}: {result['audio_path']} (duration: {result['duration']:.2f}s)")

if __name__ == "__main__":
    main()

# Note: This script supports multiple TTS services
# To use this script, you'll need to:
# 1. Set up API keys in environment variables:
#    - OpenAI: OPENAI_API_KEY
#    - Google Cloud: GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)
#    - ElevenLabs: ELEVEN_API_KEY
# 2. Install required dependencies:
#    - pip install openai google-cloud-texttospeech pydub elevenlabs
# 3. Configure TTS_USE in config.py ("OPENAI", "GOOGLE", or "ELEVENLABS")
# 4. Run: python step3_tts_generator.py 
#!/usr/bin/env python3
"""
Step 3: TTS (Text-to-Speech) Generator
This script generates audio files from news_scripts.json using OpenAI TTS
"""

import os
import json
import openai
from pathlib import Path
from config import TTS_CONFIG_OPENAI as TTS_CONFIG, LANGUAGE

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

def preprocess_script_for_tts(script_text, language):
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
    
    if language.lower() == "filipino":
        # Common Filipino pronunciation improvements for TTS
        replacements = {
            # Time formats
            "AM": "ey-em",
            "PM": "pee-em",
            # Common abbreviations
            "LGU": "el-ji-yu", 
            "DOH": "di-oh-eytch",
            "DILG": "di-ay-el-ji",
            "PNP": "pee-en-pee",
            "S&T": "es-and-ti",
            "STCBF": "es-ti-si-bi-ef",
            # Location names that might be mispronounced
            "Bulacan": "Bu-la-kan",
            "Pulilan": "Pu-li-lan",
            "Peñabatan": "Pe-nya-ba-tan",
            # Common Filipino words that TTS mispronounces
            "mga": "ma-nga",
            "ng ": "nang ",  # Add space to avoid replacing within words
            "Ang ": "Ang ",   # Keep proper but ensure clear pronunciation
            "mga kababayan": "ma-nga ka-ba-ba-yan",
            "mga balita": "ma-nga ba-li-ta",
            "mga pangunahing": "ma-nga pa-ngu-na-hing",
            "mga proyekto": "ma-nga pro-yek-to",
            "mga miyembro": "ma-nga mi-yem-bro",
            "kababaihan": "ka-ba-ba-i-han",
            "pagsasanay": "pag-sa-sa-nay",
            "naghahatid": "nag-ha-ha-tid",
            "makikita": "ma-ki-ki-ta",
            "matagumpay": "ma-ta-gum-pay",
            "koordinasyon": "ko-or-di-nas-yon",
            "implementasyon": "im-ple-men-tas-yon",
            "sustainable": "sus-tey-na-bol",
            "integrated": "in-te-grey-ted",
            "agriculture": "ag-ri-kul-tur"
        }
        
        # Apply replacements in order (longer phrases first to avoid partial replacements)
        sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        for original, replacement in sorted_replacements:
            processed_text = processed_text.replace(original, replacement)
        
        # Add brief pauses for better pacing
        processed_text = processed_text.replace(". ", ". ... ")
        processed_text = processed_text.replace("! ", "! ... ")
        processed_text = processed_text.replace("? ", "? ... ")
        processed_text = processed_text.replace(", ", ", .. ")
    
    return processed_text

def generate_audio_from_script(segment, output_dir):
    """Generate audio file from a script segment using OpenAI TTS"""
    print(f"Generating audio for: {segment['display_name']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename
    audio_filename = f"{segment['segment_name']}.{TTS_CONFIG['output_format']}"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Select appropriate voice for language
        voice = TTS_CONFIG["voice"]
        if LANGUAGE.lower() == "filipino":
            # Use alloy voice which works well with Filipino
            # OpenAI TTS doesn't have specific Filipino voices yet, but alloy handles it reasonably
            voice = "alloy"
            print(f"Using voice '{voice}' for Filipino language")
        
        # Preprocess script for better TTS pronunciation
        processed_script = preprocess_script_for_tts(segment["script"], LANGUAGE)
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
        
        return {
            "segment_name": segment["segment_name"],
            "display_name": segment["display_name"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "duration": segment["duration"],
            "language": LANGUAGE,
            "voice_used": voice
        }
        
    except Exception as e:
        print(f"Error generating audio for {segment['segment_name']}: {e}")
        return None

def main():
    """Main function to generate TTS audio"""
    print("=== Nexcaster News TTS Generator ===")
    print("Step 3: Generating audio from news scripts")
    print(f"Language: {LANGUAGE}")
    print(f"Voice: {TTS_CONFIG['voice']}")
    print(f"Output format: {TTS_CONFIG['output_format']}")
    print()
    
    # Load scripts
    scripts = load_news_scripts()
    if not scripts:
        return
    
    # Create audio output directory
    audio_dir = os.path.join('generated', 'audio')
    
    # Generate audio for each segment
    audio_results = []
    for segment in scripts:
        result = generate_audio_from_script(segment, audio_dir)
        if result:
            audio_results.append(result)
    
    # Save audio metadata
    audio_metadata_path = os.path.join('generated', 'audio_metadata.json')
    with open(audio_metadata_path, 'w', encoding='utf-8') as f:
        json.dump(audio_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAudio generation complete!")
    print(f"Generated {len(audio_results)} audio files in {LANGUAGE}")
    print(f"Audio files saved in: {audio_dir}")
    print(f"Metadata saved to: {audio_metadata_path}")
    
    # Display summary of generated files
    print(f"\nGenerated audio segments:")
    for result in audio_results:
        print(f"  - {result['display_name']}: {result['audio_file']} (Voice: {result['voice_used']})")

if __name__ == "__main__":
    main()

# Note: This is a placeholder implementation for step 3
# To use this script, you'll need to:
# 1. Set up OpenAI API key in environment variables
# 2. Install required dependencies
# 3. Run: python step3_tts_generator.py 
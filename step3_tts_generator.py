#!/usr/bin/env python3
"""
Step 3: TTS (Text-to-Speech) Generator
This script generates audio files from news_scripts.json using OpenAI TTS
"""

import os
import json
import openai
from pathlib import Path
from datetime import datetime
from google.cloud import texttospeech
from pydub import AudioSegment
from config import TTS_USE, TTS_CONFIG_OPENAI, TTS_CONFIG_GOOGLE, LANGUAGE

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
            # "AM": "ey-em",
            # "PM": "pee-em",
            # Common abbreviations
            # "LGU": "el-ji-yu", 
            # "DOH": "di-oh-eytch",
            # "DILG": "di-ay-el-ji",
            # "PNP": "pee-en-pee",
            # "S&T": "es-and-ti",
            # "STCBF": "es-ti-si-bi-ef",
            # # Location names that might be mispronounced
            # "Bulacan": "Bu-la-kan",
            # "Pulilan": "Pu-li-lan",
            # "Peñabatan": "Pe-nya-ba-tan",
            # Common Filipino words that TTS mispronounces
            "mga": "ma-nga",
            "araw": "a-raw",
            "upang": "u-pang",
            # "ng ": "nang ",  # Add space to avoid replacing within words
            # "Ang ": "Ang ",   # Keep proper but ensure clear pronunciation
            # "mga kababayan": "ma-nga ka-ba-ba-yan",
            # "mga balita": "ma-nga ba-li-ta",
            # "mga pangunahing": "ma-nga pa-ngu-na-hing",
            # "mga proyekto": "ma-nga pro-yek-to",
            # "mga miyembro": "ma-nga mi-yem-bro",
            # "kababaihan": "ka-ba-ba-i-han",
            # "pagsasanay": "pag-sa-sa-nay",
            # "naghahatid": "nag-ha-ha-tid",
            # "makikita": "ma-ki-ki-ta",
            # "matagumpay": "ma-ta-gum-pay",
            # "koordinasyon": "ko-or-di-nas-yon",
            # "implementasyon": "im-ple-men-tas-yon",
            # "sustainable": "sus-tey-na-bol",
            # "integrated": "in-te-grey-ted",
            # "agriculture": "ag-ri-kul-tur",
            "Brgy.": "Barangay",
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

def generate_audio_with_google_tts(segment, output_dir):
    """Generate audio file using Google Cloud Text-to-Speech"""
    print(f"Generating audio with Google TTS for: {segment['display_name']}")
    print(f"Language: {LANGUAGE}")
    print(f"Script length: {len(segment['script'])} characters")
    
    # Create audio output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename
    audio_filename = f"{segment['segment_name']}.{TTS_CONFIG['output_format']}"
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
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment['duration']}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment["duration"]  # Fallback to estimated
        
        return {
            "segment_name": segment["segment_name"],
            "display_name": segment["display_name"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": TTS_CONFIG["voice_name"],
            "tts_service": "Google Cloud"
        }
        
    except Exception as e:
        print(f"Error generating audio with Google TTS for {segment['segment_name']}: {e}")
        return None

def generate_audio_with_openai_tts(segment, output_dir):
    """Generate audio file using OpenAI Text-to-Speech"""
    print(f"Generating audio with OpenAI TTS for: {segment['display_name']}")
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
        
        # Measure actual duration of generated audio file
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            actual_duration = len(audio_segment) / 1000.0  # Convert to seconds
            print(f"Measured actual duration: {actual_duration:.3f}s (estimated: {segment['duration']}s)")
        except Exception as e:
            print(f"Warning: Could not measure audio duration: {e}")
            actual_duration = segment["duration"]  # Fallback to estimated
        
        return {
            "segment_name": segment["segment_name"],
            "display_name": segment["display_name"],
            "audio_file": audio_filename,
            "audio_path": audio_path,
            "script": segment["script"],
            "duration": round(actual_duration, 3),
            "language": LANGUAGE,
            "voice_used": voice,
            "tts_service": "OpenAI"
        }
        
    except Exception as e:
        print(f"Error generating audio with OpenAI TTS for {segment['segment_name']}: {e}")
        return None

def generate_audio_from_script(segment, output_dir):
    """Generate audio file from a script segment using configured TTS service"""
    if TTS_USE.upper() == "GOOGLE":
        return generate_audio_with_google_tts(segment, output_dir)
    else:
        return generate_audio_with_openai_tts(segment, output_dir)

def combine_audio_segments(audio_results, output_dir):
    """Combine all audio segments into a single combined.mp3 file"""
    print("\n=== Combining Audio Segments ===")
    
    if not audio_results:
        print("No audio files to combine!")
        return None
    
    # Sort by display_order to ensure correct sequence
    sorted_results = sorted(audio_results, key=lambda x: x.get('segment_name', ''))
    
    # Find the segments by their order (opening, summary, news1, news2, etc., closing)
    segment_order = []
    for result in sorted_results:
        segment_name = result['segment_name']
        if segment_name == 'opening_greeting':
            segment_order.append((0, result))
        elif segment_name == 'news_summary':
            segment_order.append((1, result))
        elif segment_name.startswith('news'):
            # Extract number from news1, news2, etc.
            try:
                num = int(segment_name.replace('news', ''))
                segment_order.append((num + 1, result))
            except:
                segment_order.append((99, result))  # fallback
        elif segment_name == 'closing_remarks':
            segment_order.append((999, result))
        else:
            segment_order.append((50, result))  # other segments in middle
    
    # Sort by order
    segment_order.sort(key=lambda x: x[0])
    
    try:
        combined_audio = AudioSegment.empty()
        total_duration = 0
        
        print("Combining segments in order:")
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
        combined_path = os.path.join(output_dir, "combined.mp3")
        combined_audio.export(combined_path, format="mp3")
        
        # Measure actual combined duration
        actual_combined_duration = len(combined_audio) / 1000.0  # Convert to seconds
        
        print(f"\n✅ Combined audio created: {combined_path}")
        print(f"📊 Measured combined duration: {actual_combined_duration:.3f} seconds ({actual_combined_duration/60:.2f} minutes)")
        print(f"📊 Sum of segments: {total_duration:.3f} seconds (difference: {actual_combined_duration - total_duration:.3f}s)")
        print(f"🎵 Total segments: {len(segment_order)}")
        
        return {
            "combined_file": "combined.mp3",
            "combined_path": combined_path,
            "total_duration": round(actual_combined_duration, 3),
            "segment_count": len(segment_order),
            "segments_included": [result['display_name'] for _, result in segment_order]
        }
        
    except Exception as e:
        print(f"❌ Error combining audio segments: {e}")
        return None

def main():
    """Main function to generate TTS audio"""
    print("=== Nexcaster News TTS Generator ===")
    print("Step 3: Generating audio from news scripts")
    print(f"TTS Service: {TTS_USE}")
    print(f"Language: {LANGUAGE}")
    
    if TTS_USE.upper() == "GOOGLE":
        print(f"Voice: {TTS_CONFIG['voice_name']}")
        print(f"Language Code: {TTS_CONFIG['language_code']}")
    else:
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
    
    # Combine all audio segments into one file
    combined_result = combine_audio_segments(audio_results, audio_dir)
    
    # Update metadata to include combined file info
    final_metadata = {
        "individual_segments": audio_results,
        "combined_audio": combined_result,
        "generation_info": {
            "tts_service": TTS_USE,
            "language": LANGUAGE,
            "total_segments": len(audio_results),
            "timestamp": datetime.now().isoformat() if 'datetime' in globals() else None
        }
    }
    
    # Save audio metadata
    news_manifest_path = os.path.join('generated', 'news_manifest.json')
    with open(news_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎯 Audio generation complete!")
    print(f"Generated {len(audio_results)} individual audio files in {LANGUAGE}")
    print(f"Audio files saved in: {audio_dir}")
    print(f"Manifest saved to: {news_manifest_path}")
    
    if combined_result:
        print(f"\n🎵 Combined Audio:")
        print(f"  File: {combined_result['combined_file']}")
        print(f"  Duration: {combined_result['total_duration']:.1f}s ({combined_result['total_duration']/60:.1f} minutes)")
        print(f"  Segments: {combined_result['segment_count']}")
    
    # Display summary of generated files
    print(f"\n📁 Generated audio segments:")
    for result in audio_results:
        service_info = f"({result['tts_service']}: {result['voice_used']})"
        print(f"  - {result['display_name']}: {result['audio_file']} {service_info}")

if __name__ == "__main__":
    main()

# Note: This is a placeholder implementation for step 3
# To use this script, you'll need to:
# 1. Set up OpenAI API key in environment variables
# 2. Install required dependencies
# 3. Run: python step3_tts_generator.py 
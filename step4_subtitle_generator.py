#!/usr/bin/env python3
"""
Step 4: Subtitle Generator
This script transcribes audio to get precise timing and generates subtitles with media mapping
"""

import os
import json
import openai
from pydub import AudioSegment
from config import SUBTITLE_CONFIG

def load_audio_metadata():
    """Load audio metadata from generated/audio_metadata.json"""
    metadata_path = os.path.join('generated', 'audio_metadata.json')
    if not os.path.exists(metadata_path):
        print(f"Error: {metadata_path} not found!")
        print("Please run step 3 first to generate audio files.")
        return None
    
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} audio segments from {metadata_path}")
    return data

def transcribe_audio_with_timing(audio_path):
    """Transcribe audio file and get word-level timing using OpenAI Whisper"""
    print(f"Transcribing audio: {audio_path}")
    
    try:
        client = openai.OpenAI()
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        
        print(f"Transcription complete for {audio_path}")
        return transcript
        
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        return None

def generate_subtitle_segments(audio_metadata):
    """Generate subtitle segments with precise timing"""
    subtitles = []
    current_time = 0.0
    
    for segment_data in audio_metadata:
        print(f"Processing subtitle for: {segment_data['segment_name']}")
        
        # Get audio duration (actual timing)
        try:
            audio = AudioSegment.from_file(segment_data['audio_path'])
            actual_duration = len(audio) / 1000.0  # Convert to seconds
        except Exception as e:
            print(f"Error reading audio file {segment_data['audio_path']}: {e}")
            actual_duration = segment_data['duration']  # Fallback to estimated duration
        
        # Transcribe for precise word timing (if available)
        transcript = transcribe_audio_with_timing(segment_data['audio_path'])
        
        if transcript and hasattr(transcript, 'words'):
            # Use word-level timing from Whisper
            segment_start = current_time
            
            for word_data in transcript.words:
                word_start = segment_start + word_data['start']
                word_end = segment_start + word_data['end']
                
                subtitle_segment = {
                    "start_time": word_start,
                    "end_time": word_end,
                    "text": word_data['word'],
                    "segment_name": segment_data['segment_name'],
                    "media": []  # To be populated later with media mapping
                }
                subtitles.append(subtitle_segment)
        else:
            # Fallback: create single subtitle for entire segment
            subtitle_segment = {
                "start_time": current_time,
                "end_time": current_time + actual_duration,
                "text": segment_data['script'],
                "segment_name": segment_data['segment_name'],
                "media": []
            }
            subtitles.append(subtitle_segment)
        
        # Update current time
        current_time += actual_duration + SUBTITLE_CONFIG['segment_gap']
    
    return subtitles

def map_media_to_subtitles(subtitles):
    """Map media content to subtitle segments using LLM"""
    print("Mapping media to subtitle segments...")
    
    # Load original news data to get media information
    news_data_path = os.path.join('generated', 'news_data.json')
    if not os.path.exists(news_data_path):
        print("Warning: No news data found for media mapping")
        return subtitles
    
    with open(news_data_path, 'r') as f:
        news_data = json.load(f)
    
    # For now, this is a placeholder for media mapping logic
    # In a full implementation, you would use LLM to intelligently
    # map media assets to appropriate subtitle timing
    
    print("Media mapping complete (placeholder implementation)")
    return subtitles

def save_subtitles(subtitles):
    """Save subtitles to subtitle_data.json"""
    output_path = os.path.join('generated', 'subtitle_data.json')
    
    subtitle_data = {
        "subtitles": subtitles,
        "total_duration": subtitles[-1]["end_time"] if subtitles else 0,
        "total_segments": len(subtitles)
    }
    
    with open(output_path, 'w') as f:
        json.dump(subtitle_data, f, indent=2)
    
    print(f"Subtitles saved to {output_path}")
    print(f"Generated {len(subtitles)} subtitle segments")

def main():
    """Main function to generate subtitles"""
    print("=== Nexcaster News Subtitle Generator ===")
    print("Step 4: Generating subtitles with precise timing")
    print()
    
    # Load audio metadata
    audio_metadata = load_audio_metadata()
    if not audio_metadata:
        return
    
    # Generate subtitle segments
    print("Generating subtitle segments...")
    subtitles = generate_subtitle_segments(audio_metadata)
    
    # Map media to subtitles
    subtitles = map_media_to_subtitles(subtitles)
    
    # Save results
    save_subtitles(subtitles)
    
    print("\n=== Subtitle Generation Complete ===")
    print(f"Total subtitle segments: {len(subtitles)}")
    if subtitles:
        total_duration = subtitles[-1]["end_time"]
        print(f"Total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")

if __name__ == "__main__":
    main()

# Note: This is a placeholder implementation for step 4
# To use this script, you'll need to:
# 1. Set up OpenAI API key in environment variables
# 2. Install pydub: pip install pydub
# 3. Install ffmpeg for audio processing
# 4. Run: python step4_subtitle_generator.py 
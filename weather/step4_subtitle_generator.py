#!/usr/bin/env python3
"""
Weather Subtitle Generator

This script transcribes the combined weather audio using OpenAI Whisper
and intelligently segments the subtitles based on weather media contexts.

FEATURES:
=========
• Audio transcription using OpenAI Whisper
• Intelligent segmentation using LLM based on weather media contexts
• Simple manifest.json output with timing and media associations
• Centralized configuration via config.py

USAGE:
======
Basic usage (uses config defaults):
    python step4_subtitle_generator.py

Custom audio file:
    python step4_subtitle_generator.py -f path/to/audio.mp3

Debug mode:
    python step4_subtitle_generator.py --debug

CONFIGURATION:
=============
All defaults are now centralized in config.py and can be overridden via environment variables:
- DEFAULT_SUBTITLE_INPUT: Input audio file path
- DEFAULT_SUBTITLE_OUTPUT_DIR: Output directory for manifest.json
- DEFAULT_SUBTITLE_OUTPUT_FILE: Output file name for manifest.json
- DEFAULT_WHISPER_MODEL: OpenAI Whisper model to use
- DEFAULT_SEGMENTATION_MODEL: OpenAI model for transcript segmentation
- DEFAULT_WHISPER_FORMAT: Whisper response format
- DEFAULT_TIMESTAMP_GRANULARITIES: Timestamp granularities for transcription
- DEFAULT_SEGMENT_DURATION: Segment duration constraints
- DEFAULT_INTRO_OUTRO: Intro/outro settings
- DEFAULT_SUBTITLE_AI_SETTINGS: AI settings for segmentation

REQUIREMENTS:
============
- OpenAI API key (for Whisper transcription and GPT segmentation)
- Combined audio file from step3_tts_generator.py
- Python 3.7+
"""

import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
from datetime import datetime
from openai import OpenAI

class WeatherSubtitleGenerator:
    """Generate subtitles from weather audio using AI transcription and segmentation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Set up OpenAI client
        openai_key = config.get('OPENAI_API_KEY')
        if not openai_key:
            try:
                import config as project_config
                openai_key = project_config.OPENAI_API_KEY
            except (ImportError, AttributeError):
                pass
        
        if openai_key:
            self.client = OpenAI(api_key=openai_key)
            logger.info("Initialized OpenAI client for transcription and segmentation")
        else:
            logger.error("No OpenAI API key found")
            raise ValueError("OpenAI API key required for transcription and segmentation")
        
        # Load configuration settings
        self.whisper_model = config.get('WHISPER_MODEL', 'whisper-1')
        self.segmentation_model = config.get('SEGMENTATION_MODEL', 'gpt-4')
        self.whisper_format = config.get('WHISPER_FORMAT', 'verbose_json')
        self.timestamp_granularities = config.get('TIMESTAMP_GRANULARITIES', ['word'])
        self.segment_duration = config.get('SEGMENT_DURATION', {})
        self.intro_outro = config.get('INTRO_OUTRO', {})
        self.ai_settings = config.get('AI_SETTINGS', {})
        
        # Load weather media descriptions
        self.media_descriptions = self._load_media_descriptions()
        
        logger.info(f"Initialized WeatherSubtitleGenerator with Whisper model: {self.whisper_model}")
        logger.info(f"Segmentation model: {self.segmentation_model}, Format: {self.whisper_format}")
    
    def _load_media_descriptions(self) -> Dict[str, str]:
        """Load weather media descriptions from constants.py"""
        try:
            import constants
            return constants.WEATHER_MEDIA_DESCRIPTIONS
        except ImportError:
            logger.warning("Could not import constants.py, using fallback media descriptions")
            return self._get_fallback_media_descriptions()
    
    def _get_fallback_media_descriptions(self) -> Dict[str, str]:
        """Fallback media descriptions if constants.py is not available"""
        return {
            "weather_map1": "Weather map showing current conditions",
            "weather_map2": "Weather map with forecast data",
            "card-temperature": "Temperature display card",
            "card-wind": "Wind conditions display card",
            "card-humidity": "Humidity levels display card",
            "card-uv": "UV index display card",
            "card-precipitation": "Precipitation forecast card",
            "weather_background1": "General weather background visual",
            "weather_background2": "Alternative weather background visual"
        }
    
    def generate_subtitles(self, audio_file: str) -> str:
        """Generate subtitles from audio file"""
        try:
            logger.info(f"Generating subtitles from audio file: {audio_file}")
            print(f"🎙️  Transcribing audio: {audio_file}")
            
            # Check if audio file exists
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            # Step 1: Transcribe audio using Whisper
            print("🔊 Transcribing audio with Whisper...")
            transcript_data = self._transcribe_audio(audio_file)
            
            # Step 2: Segment transcript using LLM
            print("🧠 Segmenting transcript with AI...")
            segmented_data = self._segment_transcript(transcript_data)
            
            # Step 3: Generate manifest.json
            print("📄 Generating manifest.json...")
            manifest_file = self._generate_manifest(segmented_data, audio_file)
            
            print(f"✅ Subtitle generation completed!")
            print(f"📄 Generated: {manifest_file}")
            
            return manifest_file
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {str(e)}")
            raise
    
    def _transcribe_audio(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper"""
        try:
            with open(audio_file, 'rb') as f:
                transcript = self.client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=f,
                    response_format=self.whisper_format,
                    timestamp_granularities=self.timestamp_granularities
                )
            
            logger.info(f"Transcribed {transcript.duration:.1f}s of audio")
            print(f"📊 Transcribed {transcript.duration:.1f}s of audio")
            
            return {
                'text': transcript.text,
                'duration': transcript.duration,
                'words': transcript.words if hasattr(transcript, 'words') else [],
                'segments': transcript.segments if hasattr(transcript, 'segments') else []
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise
    
    def _segment_transcript(self, transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Segment transcript based on weather media contexts using LLM"""
        try:
            # Create media context for LLM
            media_context = "\n".join([
                f"- {media}: {desc}" 
                for media, desc in self.media_descriptions.items()
            ])
            
            # Create prompt for LLM segmentation
            prompt = f"""
You are an AI assistant that segments weather forecast transcripts into very granular parts for precise visual cueing.

AVAILABLE WEATHER MEDIA:
{media_context}

TRANSCRIPT TO SEGMENT:
"{transcript_data['text']}"

TASK: Analyze this weather forecast transcript and segment it into VERY GRANULAR parts ({self.segment_duration.get('min', 15)}-{self.segment_duration.get('max', 30)} second segments) that correspond to the weather media above. Each segment should have:
1. start_time (in seconds)
2. end_time (in seconds) 
3. text (the portion of transcript)
4. media_type (which weather media this segment relates to)
5. confidence (0.0-1.0 how confident you are about the media mapping)

SPECIAL RULES:
- The total duration is {transcript_data['duration']:.1f} seconds
- Create approximately {self.segment_duration.get('target_count', 17)} segments for maximum granularity
- Segments should be {self.segment_duration.get('min', 15)}-{self.segment_duration.get('max', 30)} seconds each for precise visual timing
- Segments should not overlap
- DO NOT use "{self.intro_outro.get('intro_media', 'intro.mp4')}" or "{self.intro_outro.get('outro_media', 'outro.mp4')}" - these are excluded from weather visuals
- For opening weather content, prioritize "weather_map2"
- For closing weather content, prioritize "weather_map1" 
- Use specific weather cards (card-temperature, card-wind, card-humidity, etc.) when content matches
- If unsure between options, prefer weather maps over generic cards
- Return valid JSON array format

Return only the JSON array of segments, no other text.
"""
            
            response = self.client.chat.completions.create(
                model=self.segmentation_model,
                messages=[
                    {"role": "system", "content": "You are a precise AI that returns only valid JSON and creates very granular segments for accurate video timing."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.ai_settings.get('temperature', 0.2)
            )
            
            # Parse the response
            segments_text = response.choices[0].message.content.strip()
            
            # Remove any markdown formatting if present
            if segments_text.startswith('```json'):
                segments_text = segments_text[7:]
            if segments_text.endswith('```'):
                segments_text = segments_text[:-3]
            
            segments = json.loads(segments_text)
            
            logger.info(f"Generated {len(segments)} segments")
            print(f"📊 Generated {len(segments)} granular subtitle segments")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting transcript: {str(e)}")
            raise
    
    def _generate_manifest(self, segments: List[Dict[str, Any]], audio_file: str) -> str:
        """Generate manifest.json file with intro/outro timing"""
        try:
            # Get durations for intro, main audio, and outro
            intro_duration = self.intro_outro.get('intro_duration', 6.0)  # intro.mp3 duration
            outro_duration = self.intro_outro.get('outro_duration', 6.6)  # outro.mp3 duration
            main_audio_duration = max(seg.get('end_time', 0) for seg in segments) if segments else 0
            
            # Calculate total duration including intro and outro
            total_duration = intro_duration + main_audio_duration + outro_duration
            
            # Create intro segment
            intro_segment = {
                "start_time": 0,
                "end_time": intro_duration,
                "text": "Weather report introduction",
                "media_type": self.intro_outro.get('intro_media', 'intro.mp4'),
                "confidence": 1.0
            }
            
            # Adjust main segments timing to start after intro
            adjusted_segments = []
            for segment in segments:
                adjusted_segment = segment.copy()
                adjusted_segment['start_time'] = segment['start_time'] + intro_duration
                adjusted_segment['end_time'] = segment['end_time'] + intro_duration
                adjusted_segments.append(adjusted_segment)
            
            # Create outro segment
            outro_segment = {
                "start_time": intro_duration + main_audio_duration,
                "end_time": total_duration,
                "text": "Weather report conclusion",
                "media_type": self.intro_outro.get('outro_media', 'outro.mp4'), 
                "confidence": 1.0
            }
            
            # Combine all segments
            all_segments = [intro_segment] + adjusted_segments + [outro_segment]
            
            manifest_data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "source_audio": os.path.basename(audio_file),
                    "intro_duration": intro_duration,
                    "outro_duration": outro_duration,
                    "main_audio_duration": main_audio_duration,
                    "total_segments": len(all_segments),
                    "total_duration": total_duration,
                    "generator": "weather_subtitle_generator"
                },
                "subtitles": all_segments
            }
            
            # Save to data/latest/manifest.json
            manifest_path = os.path.join(self.config['DATA_DIR'], 'manifest.json')
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated manifest file with intro/outro timing: {manifest_path}")
            print(f"📊 Total duration: {total_duration:.1f}s (intro: {intro_duration}s + main: {main_audio_duration:.1f}s + outro: {outro_duration}s)")
            
            return 'manifest.json'
            
        except Exception as e:
            logger.error(f"Error generating manifest: {str(e)}")
            raise

def main():
    """Main function for command-line usage"""
    
    # Import defaults from config
    from config import (
        DEFAULT_SUBTITLE_INPUT,
        DEFAULT_SUBTITLE_OUTPUT_DIR,
        DEFAULT_SUBTITLE_OUTPUT_FILE,
        DEFAULT_WHISPER_MODEL,
        DEFAULT_SEGMENTATION_MODEL,
        DEFAULT_WHISPER_FORMAT,
        DEFAULT_TIMESTAMP_GRANULARITIES,
        DEFAULT_SEGMENT_DURATION,
        DEFAULT_INTRO_OUTRO,
        DEFAULT_SUBTITLE_AI_SETTINGS
    )
    
    parser = argparse.ArgumentParser(
        description='Generate subtitles from weather audio using AI transcription',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  Basic usage:
    python step4_subtitle_generator.py
    
  Custom audio file:
    python step4_subtitle_generator.py -f path/to/audio.mp3
    
  Debug mode:
    python step4_subtitle_generator.py --debug
        """
    )
    
    parser.add_argument(
        '-f', '--file', 
        default=DEFAULT_SUBTITLE_INPUT,
        help=f'Audio file to transcribe (default: {DEFAULT_SUBTITLE_INPUT})'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Enable debug logging'
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default=DEFAULT_SUBTITLE_OUTPUT_DIR,
        help=f'Output directory for manifest.json (default: {DEFAULT_SUBTITLE_OUTPUT_DIR})'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Check if audio file exists
        if not os.path.exists(args.file):
            if args.file == DEFAULT_SUBTITLE_INPUT:
                print(f"❌ Error: Default audio file not found: {args.file}")
                print("💡 Make sure you have run the TTS generator first to create the combined audio file.")
                print("   Run: python step3_tts_generator.py --combine")
            else:
                print(f"❌ Error: Audio file not found: {args.file}")
            return 1
        
        print(f"🚀 Starting subtitle generation...")
        print(f"📁 Audio file: {args.file}")
        print(f"📄 Output: {os.path.join(args.output_dir, DEFAULT_SUBTITLE_OUTPUT_FILE)}")
        print(f"🔊 Whisper model: {DEFAULT_WHISPER_MODEL}")
        print(f"🧠 Segmentation model: {DEFAULT_SEGMENTATION_MODEL}")
        print()
        
        # Initialize subtitle generator with config
        import config
        
        config_dict = {
            'OPENAI_API_KEY': config.OPENAI_API_KEY,
            'DATA_DIR': args.output_dir,
            'WHISPER_MODEL': DEFAULT_WHISPER_MODEL,
            'SEGMENTATION_MODEL': DEFAULT_SEGMENTATION_MODEL,
            'WHISPER_FORMAT': DEFAULT_WHISPER_FORMAT,
            'TIMESTAMP_GRANULARITIES': DEFAULT_TIMESTAMP_GRANULARITIES,
            'SEGMENT_DURATION': DEFAULT_SEGMENT_DURATION,
            'INTRO_OUTRO': DEFAULT_INTRO_OUTRO,
            'AI_SETTINGS': DEFAULT_SUBTITLE_AI_SETTINGS
        }
        
        generator = WeatherSubtitleGenerator(config_dict)
        
        # Generate subtitles
        manifest_file = generator.generate_subtitles(args.file)
        
        print()
        print(f"✅ Subtitle generation completed successfully!")
        print(f"📄 Generated: {manifest_file}")
        print(f"📁 Location: {os.path.join(args.output_dir, manifest_file)}")
        
        print()
        print("🎯 Next steps:")
        print("   • Use manifest.json for video production with timed media")
        print("   • Each segment includes timing and media type associations")
        
    except Exception as e:
        logger.error(f"Failed to generate subtitles: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Set up logging when running as a script
    import sys
    import os
    
    # Since we're now in the root directory, add current directory to path for config imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    import config
    
    # Configure loguru logger
    log_format = config.LOG_FORMAT if hasattr(config, 'LOG_FORMAT') else "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    logs_dir = config.LOGS_DIR if hasattr(config, 'LOGS_DIR') else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, format=log_format, level="INFO")
    logger.add(os.path.join(logs_dir, "subtitle_generator_cli.log"), rotation="500 MB", retention="10 days", format=log_format)
    
    logger.info("Starting step4_subtitle_generator.py as standalone script")
    
    # Run the main function
    sys.exit(main()) 
#!/usr/bin/env python3
"""
Municipal Weather Script Generator - Media-Based Simplified Format

Enhanced script generator that creates weather scripts based on media descriptions
with simplified output format including Filipino headlines.
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Try to import OpenAI - graceful fallback if not available
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI library not available. Script generation will be limited.")

# Set up logging
from loguru import logger

# Default values for script generation
DEFAULT_SEGMENT_MODEL = 'gpt-4o'
DEFAULT_SEGMENT_TEMPERATURE = 0.7
DEFAULT_SEGMENT_MAX_TOKENS = 1500

@dataclass
class Script:
    """Simplified script format"""
    segment_type: str
    display_name: str
    display_order: int
    duration: float
    headline: str
    script: str

class MunicipalWeatherScriptGenerator:
    """Enhanced script generator for municipal weather reports with media-based structure"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Set up OpenAI client (modern v1.0+ format)
        openai_key = config.get('OPENAI_API_KEY')
        if not openai_key:
            # Try to get from project config
            try:
                import config as project_config
                openai_key = project_config.OPENAI_API_KEY
            except (ImportError, AttributeError):
                pass
        
        if openai_key and HAS_OPENAI:
            self.client = OpenAI(api_key=openai_key)
            logger.info("Initialized OpenAI client for script generation")
        else:
            logger.warning("No OpenAI API key found for script generation")
            self.client = None
        
        # Save scripts to the generated directory
        self.scripts_dir = config.get('DATA_DIR', 'generated')
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Load media-based script types from constants
        self.script_types = self._get_media_based_script_types()
        
        # OpenAI settings from config
        self.openai_model = config.get('OPENAI_MODEL', DEFAULT_SEGMENT_MODEL)
        self.openai_temperature = config.get('OPENAI_TEMPERATURE', DEFAULT_SEGMENT_TEMPERATURE)
        self.openai_max_tokens = config.get('OPENAI_MAX_TOKENS', DEFAULT_SEGMENT_MAX_TOKENS)
        
        logger.info(f"Initialized MunicipalWeatherScriptGenerator with {len(self.script_types)} script types")

    def _get_media_based_script_types(self) -> List[Dict[str, Any]]:
        """Load script types from constants.py media descriptions"""
        try:
            from constants import MEDIA_BASED_SCRIPT_TYPES
            logger.info(f"Loaded {len(MEDIA_BASED_SCRIPT_TYPES)} media-based script types")
            return MEDIA_BASED_SCRIPT_TYPES
        except ImportError:
            logger.warning("Could not import constants.py, using fallback script types")
            return self._get_fallback_script_types()

    def _get_fallback_script_types(self) -> List[Dict[str, Any]]:
        """Fallback script types if constants.py is not available"""
        return [
            {
                'name': 'card_current',
                'display_name': 'Current Weather',
                'display_order': 100,
                'target_duration': 35.0,
                'prompt_focus': 'Current weather conditions overview with temperature and key metrics',
                'headline': 'Buong lagay ng panahon sa kasalukuyan.',
                'media_key': 'card-current'
            },
            {
                'name': 'card_temperature',
                'display_name': 'Temperature',
                'display_order': 102,
                'target_duration': 30.0,
                'prompt_focus': 'Temperature data including current, feels like, and daily range',
                'headline': 'Mataas na temperatura inaasahan ngayon.',
                'media_key': 'card-temperature'
            },
            {
                'name': 'card_hourly',
                'display_name': 'Hourly Forecast',
                'display_order': 115,
                'target_duration': 40.0,
                'prompt_focus': 'Comprehensive hourly weather forecast',
                'headline': 'Hourly forecast para sa susunod na mga araw.',
                'media_key': 'card-hourly'
            }
        ]

    async def generate_scripts(self, weather_data: Dict[str, Any]) -> List[Script]:
        """Generate enhanced municipal weather scripts from weather data"""
        try:
            logger.info("Generating municipal weather scripts from enhanced data")
            
            # Validate weather data
            if not self._validate_weather_data(weather_data):
                raise ValueError("Invalid or incomplete weather data")
            
            scripts = []
            
            # Generate each script type using media-based types
            for script_type in self.script_types:
                logger.info(f"Generating script: {script_type['display_name']}")
                
                script = await self._generate_single_script(
                    script_type=script_type,
                    weather_data=weather_data
                )
                
                if script:
                    scripts.append(script)
                    logger.debug(f"Generated script: {script.segment_type}")
            
            # Save all scripts
            scripts_file_path = self._save_scripts(scripts, weather_data.get('source_file_path'))
            
            logger.info(f"Successfully generated {len(scripts)} municipal weather scripts")
            return scripts
            
        except Exception as e:
            logger.error(f"Error generating municipal weather scripts: {str(e)}")
            raise

    async def _generate_single_script(self, script_type: Dict[str, Any], weather_data: Dict[str, Any]) -> Script:
        """Generate a single script with simplified format"""
        try:
            if not self.client:
                # Return dummy script if no OpenAI client
                return Script(
                    segment_type=script_type['name'],
                    display_name=script_type['display_name'],
                    display_order=script_type['display_order'],
                    duration=script_type['target_duration'],
                    headline=script_type['headline'],
                    script=f"Demo script for {script_type['display_name']} - Weather update in Filipino."
                )
            
            # Prepare enhanced prompt for this script type
            prompt = self._prepare_enhanced_script_prompt(script_type, weather_data)
            
            # Generate script using OpenAI with config settings
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.openai_temperature,
                max_tokens=self.openai_max_tokens
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            logger.debug(f"Raw OpenAI response for {script_type['name']}: {content[:200]}...")
            
            # Try to parse JSON response, fallback to plain text
            try:
                # Clean content first - remove markdown code blocks
                cleaned_content = content.strip()
                if cleaned_content.startswith('```'):
                    # Extract content from markdown code blocks
                    lines = cleaned_content.split('\n')
                    json_lines = []
                    in_code_block = False
                    for line in lines:
                        if line.startswith('```'):
                            in_code_block = not in_code_block
                            continue
                        if in_code_block:
                            json_lines.append(line)
                    cleaned_content = '\n'.join(json_lines).strip()
                
                parsed_data = json.loads(cleaned_content)
                script_text = parsed_data.get('script', cleaned_content)
                headline = parsed_data.get('headline', script_type['headline'])
            except json.JSONDecodeError:
                script_text = content
                headline = script_type['headline']
            
            # Create simplified script object
            script = Script(
                segment_type=script_type['name'],
                display_name=script_type['display_name'],
                display_order=script_type['display_order'],
                duration=script_type['target_duration'],
                headline=headline,
                script=script_text
            )
            
            logger.info(f"Generated script: {script.segment_type} - {len(script.script)} chars")
            return script
            
        except Exception as e:
            logger.error(f"Error generating script {script_type['name']}: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """System prompt for weather reporting"""
        language = self.config.get('LANGUAGE', 'English')
        
        if language.lower() == 'filipino':
            return f"""Ikaw ay isang propesyonal na TV weather reporter na nagbibigay ng malinaw at makabuluhang weather reports para sa lokal na audience.

Gumawa ng scripts sa Filipino na:
• Malinaw at madaling maintindihan
• Gumagamit ng natural na Filipino weather terms
• Professional ngunit friendly na tono
• Naaayon sa weather media visual na ipapakita
• May mga headline na nakakaakit ng pansin

Magbigay ng JSON response na may:
{{
    "headline": "Nakakaakit na Filipino headline",
    "script": "Detalyadong weather script sa Filipino"
}}

O kaya naman ay script text lang kung hindi kaya ang JSON format."""
        else:
            return f"""You are a professional TV weather reporter delivering clear, informative weather reports for local audiences in {language}.

Create scripts that are:
• Clear and easy to understand
• Using natural weather terminology in {language}
• Professional yet friendly tone
• Appropriate for the weather media visual being shown
• Include engaging headlines

Provide JSON response with:
{{
    "headline": "Engaging headline in {language}",
    "script": "Detailed weather script in {language}"
}}

Or just provide the script text if JSON formatting is difficult."""

    def _prepare_enhanced_script_prompt(self, script_type: Dict[str, Any], weather_data: Dict[str, Any]) -> str:
        """Prepare enhanced prompt for script generation"""
        
        # Extract key data elements
        text_data = weather_data.get('text_data', {})
        current_conditions = weather_data.get('current_conditions', {})
        forecast = weather_data.get('forecast', {})
        location_context = weather_data.get('location_context', {})
        
        # Build context based on script type
        weather_context = {
            'temperature': text_data.get('temperature', 'Unknown'),
            'conditions': text_data.get('conditions', 'Unknown'),
            'location': location_context.get('municipality', 'Unknown'),
            'region': location_context.get('region', 'Unknown'),
            'wind': text_data.get('wind', 'Unknown'),
            'humidity': text_data.get('humidity', 'Unknown'),
            'uv_index': text_data.get('uv_index', 'Unknown'),
            'heat_index': text_data.get('heat_index', 'Unknown'),
            'pressure': text_data.get('pressure', 'Unknown'),
            'visibility': text_data.get('visibility', 'Unknown'),
            'air_quality': text_data.get('air_quality', 'Unknown'),
            'sunrise': text_data.get('sunrise', 'Unknown'),
            'sunset': text_data.get('sunset', 'Unknown')
        }
        
        language = self.config.get('LANGUAGE', 'English')
        language_instruction = "Generate in Filipino" if language.lower() == 'filipino' else f"Generate in {language}"
        
        return f"""
Create a weather script for: {script_type['display_name']}

MEDIA FOCUS: {script_type['prompt_focus']}

WEATHER CONTEXT:
Location: {weather_context['location']}, {weather_context['region']}
Temperature: {weather_context['temperature']}
Conditions: {weather_context['conditions']}
Wind: {weather_context['wind']}
Humidity: {weather_context['humidity']}
UV Index: {weather_context['uv_index']}
Heat Index: {weather_context['heat_index']}
Pressure: {weather_context['pressure']}
Visibility: {weather_context['visibility']}
Air Quality: {weather_context['air_quality']}
Sunrise: {weather_context['sunrise']}
Sunset: {weather_context['sunset']}

DURATION: {script_type['target_duration']} seconds
SUGGESTED HEADLINE: {script_type['headline']}

{language_instruction}. Create a natural, conversational script that explains the weather information relevant to this media card/visual.

Focus on what viewers need to know about this specific weather aspect.
        """

    def _validate_weather_data(self, weather_data: Dict[str, Any]) -> bool:
        """Validate weather data completeness"""
        try:
            required_fields = ['text_data', 'location_context']
            for field in required_fields:
                if field not in weather_data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            text_data = weather_data['text_data']
            if not text_data.get('temperature') or not text_data.get('conditions'):
                logger.warning("Missing basic weather conditions")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating weather data: {str(e)}")
            return False

    def _save_scripts(self, scripts: List[Script], weather_data_file: str = None):
        """Save scripts to JSON file with simplified format"""
        try:
            # Create output structure
            output_data = {
                "metadata": {
                    "report_id": f"weather_scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "created_at": datetime.now().isoformat(),
                    "total_scripts": len(scripts),
                    "script_format": "simplified_media_based",
                    "version": "2.0"
                },
                "scripts": [asdict(script) for script in scripts]
            }
            
            # Save to file
            output_path = os.path.join(self.scripts_dir, 'weather_scripts.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(scripts)} scripts to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving scripts: {str(e)}")
            raise

async def main():
    """Main function for standalone script generation"""
    parser = argparse.ArgumentParser(description='Generate weather scripts from weather data')
    parser.add_argument('--input', '-i', default='generated/weather_data.json',
                       help='Input weather data file (default: generated/weather_data.json)')
    parser.add_argument('--output-dir', '-o', default='generated/',
                       help='Output directory for scripts (default: generated/)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    try:
        logger.info("Starting step2_weather_scripts.py as standalone script")
        
        # Load weather data
        print(f"📁 Loading weather data from: {args.input}")
        
        if not os.path.exists(args.input):
            print(f"❌ Weather data file not found: {args.input}")
            print("💡 Please run step1_weather_data.py first to generate weather data")
            return 1
        
        with open(args.input, 'r', encoding='utf-8') as f:
            weather_data = json.load(f)
        
        # Quick data quality check
        text_data = weather_data.get('text_data', {})
        print("📊 Data Quality Check:")
        print(f"   🌡️  Temperature: {text_data.get('temperature', 'Missing')}")
        print(f"   ☁️  Conditions: {text_data.get('conditions', 'Missing')}")
        print(f"   📍 Location: {weather_data.get('location_context', {}).get('municipality', 'Missing')}, {weather_data.get('location_context', {}).get('region', 'Missing')}")
        
        data_completeness = len([v for v in text_data.values() if v and v != 'Unknown']) / max(len(text_data), 1) * 100
        print(f"   ✅ Valid: {bool(text_data.get('temperature') and text_data.get('conditions'))}")
        print(f"   📈 Completeness: {data_completeness:.1f}%")
        print(f"   🎯 Script Ready: {data_completeness >= 50}")
        print()
        
        # Initialize script generator with config
        import config
        
        config_dict = {
            'OPENAI_API_KEY': config.OPENAI_API_KEY,
            'DATA_DIR': args.output_dir,
            'OPENAI_MODEL': DEFAULT_SEGMENT_MODEL,
            'OPENAI_TEMPERATURE': DEFAULT_SEGMENT_TEMPERATURE,
            'OPENAI_MAX_TOKENS': DEFAULT_SEGMENT_MAX_TOKENS,
            'LANGUAGE': getattr(config, 'LANGUAGE', 'English')
        }
        
        generator = MunicipalWeatherScriptGenerator(config_dict)
        
        # Generate scripts
        print(f"🚀 Generating municipal weather scripts using {generator.openai_model}...")
        scripts = await generator.generate_scripts(weather_data)
        
        if scripts:
            print("✅ Successfully generated scripts!")
            print()
            print("📺 Municipal Weather Scripts Summary:")
            print(f"   📊 Total Scripts: {len(scripts)}")
            total_duration = sum(script.duration for script in scripts)
            print(f"   ⏱️  Total Duration: {total_duration} seconds ({total_duration/60:.1f} minutes)")
            print(f"   🤖 AI Model: {generator.openai_model}")
            print(f"   🌡️  Temperature: {generator.openai_temperature}")
            print()
            print("🎬 Script Breakdown:")
            
            for i, script in enumerate(scripts, 1):
                print(f"   {i}. {script.display_name}")
                print(f"      📝 Type: {script.segment_type}")
                print(f"      ⏱️  Duration: {script.duration}s")
                print(f"      🎯 Order: {script.display_order}")
                print(f"      📰 Headline: \"{script.headline}\"")
                print(f"      📝 Script: \"{script.script[:100]}...\"")
                print()
            
            print(f"💾 Scripts saved to: generated/weather_scripts.json")
            return 0
        else:
            print("❌ No scripts were generated")
            return 1
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    # Run the async main function
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
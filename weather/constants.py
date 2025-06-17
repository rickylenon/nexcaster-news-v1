#!/usr/bin/env python3
"""
Weather Media Constants - Simple Descriptions

Simple lookup dictionary for what each weather media is about.
"""

# Weather media descriptions - simple lookup of what each media is about
WEATHER_MEDIA_DESCRIPTIONS = {
    'intro.mp4': 'This video serves as the opening sequence for the weather presentation. It provides an engaging introduction that sets the context and welcomes viewers to the weather forecast content.',
    
    
    'weather_map1': 'This visual shows the weather map for a specific location. It includes the temperature, weather condition, time of report, wind speed and direction, humidity, how hot it feels, visibility, UV index, atmospheric pressure, and dew point.',
    
    'weather_map2': 'This visual shows the weather map for a specific location. It includes the temperature, weather condition, time of report, wind speed and direction, humidity, how hot it feels, visibility, UV index, atmospheric pressure, and dew point.',
    
    'outro.mp4': 'This video serves as the closing sequence for the weather presentation. It provides a professional conclusion to the weather forecast, often including summary information or call-to-action elements.',
    
    'card-temperature': 'This visual presents temperature data for the day. It shows the current temperature, how hot it feels, the highest and lowest expected temperatures, and the time when the peak temperature will occur. It also includes a timeline graph of temperature changes throughout the day.',
    
    'card-feels-like': 'This visual presents the "feels like" temperature, explaining how it differs from the actual temperature due to factors such as humidity. It highlights the influence of environmental conditions on how hot or cold the weather feels to a person.',
    
    'card-cloud-cover': 'This visual presents information about cloud cover. It describes the current sky condition and indicates whether cloudiness is increasing or decreasing, helping to understand how clear or overcast the sky is expected to be.',
    
    'card-precipitation': 'This visual presents precipitation data. It shows the total expected rainfall over the next 24 hours, provides a timeline of projected precipitation levels by hour, and indicates whether any rainfall is currently expected.',
    
    'card-wind': 'This visual presents wind data. It shows the current wind speed and direction, the strongest wind gust expected, and a forecast of wind speeds over time. It also includes the wind\'s origin angle and its strength based on the Beaufort scale.',
    
    'card-humidity': 'This visual presents humidity data. It shows the current humidity level, the dew point temperature, and how humidity is expected to change over time. It also includes a general description of the humidity condition.',
    
    'card-uv': 'This visual presents ultraviolet (UV) index data. It shows the current UV level, its risk classification, and a timeline of how the UV index is expected to vary throughout the day.',
    
    'card-aqi': 'This visual presents air quality data. It shows the Air Quality Index (AQI) level, the status of air quality, the main pollutant contributing to the reading, and a short explanation of current pollution conditions.',
    
    'card-visibility': 'This visual presents visibility data. It shows the current visibility distance, a general assessment of its quality, and a timeline of how visibility is expected to change throughout the day.',
    
    'card-pressure': 'This visual presents atmospheric pressure data. It shows the current pressure reading, the time of observation, the trend over the next several hours, and whether the pressure is rising or falling.',
    
    'card-sun': 'This visual presents sun-related data. It shows the time of sunrise and sunset, as well as the total duration of daylight for the day.',
    
    'card-moon': 'This visual presents moon phase data. It shows the current moon phase, the percentage of moon illumination, and the expected date of the next full moon.',
    
    'card-current': 'This visual presents the current weather conditions overview. It shows the current temperature, weather condition, feels like temperature, and key weather metrics including wind, humidity, visibility, pressure, and dew point in a comprehensive dashboard format.',
    
    'card-hourly': 'This visual presents a comprehensive hourly weather forecast in a dashboard format. It features a 6-day tab navigation system, showing hourly temperature data, weather conditions, rain probability percentages, an animated temperature curve chart, and sunrise/sunset times. The layout is designed for wider displays (1000px) and includes interactive toggle switches and animated weather elements.',
    
    'weather_overview': 'This visual shows the weather forecast by day and hour. It includes daily high and low temperatures, weather conditions for each day, hourly temperature changes, chances of rain, expected rainfall times, and the current moon phase. It also shows when the sun will set.',
    
    'weather_current_overview': 'This visual shows the current weather for a specific location. It includes the temperature, weather condition, time of report, wind speed and direction, humidity, how hot it feels, visibility, UV index, atmospheric pressure, and dew point.',
}

# Simple helper function
def get_description(media_key: str) -> str:
    """Get description for a weather media"""
    return WEATHER_MEDIA_DESCRIPTIONS.get(media_key, f'Unknown weather media: {media_key}')

# List of available media
AVAILABLE_MEDIA = list(WEATHER_MEDIA_DESCRIPTIONS.keys())

# Generate script types from weather media descriptions
def generate_script_types_from_media(include_video_segments=False, brief_mode=False):
    """Generate simplified script types based on weather media descriptions
    
    Args:
        include_video_segments (bool): Whether to include intro.mp4 and outro.mp4
        brief_mode (bool): Whether to use shorter durations for brief scripts
    """
    script_types = []
    display_order = 100  # Start from 100 to allow insertions
    
    # Filipino headlines for different media types
    FILIPINO_HEADLINES = {
        'intro.mp4': 'Maligayang pagdating sa aming weather update!',
        'weather_map1': 'Tingnan natin ang kasalukuyang lagay ng panahon.',
        'weather_map2': 'Higit pang detalye ng weather conditions.',
        'outro.mp4': 'Salamat sa pakikinig at mag-ingat sa paglabas!',
        'card-temperature': 'Mataas na temperatura inaasahan ngayon.',
        'card-feels-like': 'Mas mainit pa sa pakiramdam dahil sa humidity.',
        'card-cloud-cover': 'Mga ulap ang nagdudulot ng maliliit na pagbabago.',
        'card-precipitation': 'Posibilidad ng ulan sa susunod na mga oras.',
        'card-wind': 'Malakas na hangin mula sa timog-kanluran.',
        'card-humidity': 'Mataas na humidity kaya mas mainit ang pakiramdam.',
        'card-uv': 'Mataas ang UV index, mag-ingat sa sikat ng araw.',
        'card-aqi': 'Kalidad ng hangin at mga pollutants sa kapaligiran.',
        'card-visibility': 'Malinaw ang paningin sa karamihan ng lugar.',
        'card-pressure': 'Atmospheric pressure ay tumutulong sa weather patterns.',
        'card-sun': 'Oras ng pagsikat at paglubog ng araw.',
        'card-moon': 'Kasalukuyang hugis ng buwan at impluwensya nito.',
        'card-current': 'Buong lagay ng panahon sa kasalukuyan.',
        'card-hourly': 'Hourly forecast para sa susunod na mga araw.',
        'weather_overview': 'Kabuuang weather forecast para sa linggo.',
        'weather_current_overview': 'Detalyadong current weather conditions.'
    }
    
    # Duration mapping based on content complexity
    DURATION_MAP = {
        'intro.mp4': 15.0,
        'weather_map1': 25.0,
        'weather_map2': 25.0,
        'outro.mp4': 15.0,
        'card-temperature': 30.0,
        'card-feels-like': 20.0,
        'card-cloud-cover': 20.0,
        'card-precipitation': 25.0,
        'card-wind': 20.0,
        'card-humidity': 20.0,
        'card-uv': 25.0,
        'card-aqi': 30.0,
        'card-visibility': 15.0,
        'card-pressure': 20.0,
        'card-sun': 15.0,
        'card-moon': 15.0,
        'card-current': 35.0,
        'card-hourly': 40.0,
        'weather_overview': 45.0,
        'weather_current_overview': 30.0
    }
    
    # Brief mode durations (shorter for quick updates)
    BRIEF_DURATION_MAP = {
        'intro.mp4': 8.0,
        'weather_map1': 15.0,
        'weather_map2': 15.0,
        'outro.mp4': 8.0,
        'card-temperature': 15.0,
        'card-feels-like': 12.0,
        'card-cloud-cover': 12.0,
        'card-precipitation': 15.0,
        'card-wind': 12.0,
        'card-humidity': 12.0,
        'card-uv': 15.0,
        'card-aqi': 18.0,
        'card-visibility': 10.0,
        'card-pressure': 12.0,
        'card-sun': 10.0,
        'card-moon': 10.0,
        'card-current': 20.0,
        'card-hourly': 25.0,
        'weather_overview': 30.0,
        'weather_current_overview': 18.0
    }
    
    for media_key, description in WEATHER_MEDIA_DESCRIPTIONS.items():
        # Skip .mp4 files unless specifically requested
        if media_key.endswith('.mp4') and not include_video_segments:
            continue
            
        # Create display name from media key
        display_name = media_key.replace('_', ' ').replace('-', ' ').title()
        if display_name.startswith('Card '):
            display_name = display_name.replace('Card ', '')
        
        # Choose duration map based on brief mode
        duration_map = BRIEF_DURATION_MAP if brief_mode else DURATION_MAP
        
        script_type = {
            'name': media_key.replace('-', '_'),
            'display_name': display_name,
            'display_order': display_order,
            'target_duration': duration_map.get(media_key, 15.0 if brief_mode else 25.0),
            'prompt_focus': description,
            'headline': FILIPINO_HEADLINES.get(media_key, 'Weather update para sa inyo.'),
            'media_key': media_key,
            'brief_mode': brief_mode
        }
        
        script_types.append(script_type)
        display_order += 1
    
    return script_types

# Generate the script types (default: no video segments, normal duration)
MEDIA_BASED_SCRIPT_TYPES = generate_script_types_from_media()

# Generate brief script types with video segments
BRIEF_SCRIPT_TYPES_WITH_VIDEO = generate_script_types_from_media(include_video_segments=True, brief_mode=True)

# Generate brief script types without video segments  
BRIEF_SCRIPT_TYPES = generate_script_types_from_media(include_video_segments=False, brief_mode=True)

if __name__ == "__main__":
    """Display all weather media descriptions and generated script types"""
    print("Weather Media Descriptions")
    print("=" * 50)
    
    for media_key, description in WEATHER_MEDIA_DESCRIPTIONS.items():
        print(f"\n{media_key.upper()}:")
        print(f"  {description}")
    
    print(f"\nTotal: {len(AVAILABLE_MEDIA)} media available")
    
    print("\n" + "=" * 50)
    print("Generated Script Types")
    print("=" * 50)
    
    for script_type in MEDIA_BASED_SCRIPT_TYPES:
        print(f"\n{script_type['name'].upper()}:")
        print(f"  Display Name: {script_type['display_name']}")
        print(f"  Order: {script_type['display_order']}")
        print(f"  Duration: {script_type['target_duration']}s")
        print(f"  Headline: {script_type['headline']}")
        print(f"  Focus: {script_type['prompt_focus'][:100]}...")
    
    print(f"\nTotal: {len(MEDIA_BASED_SCRIPT_TYPES)} script types generated") 
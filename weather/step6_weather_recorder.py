#!/usr/bin/env python3
"""
Provincial Weather Recorder - Step 6

Captures weather pages and saves multimedia to generated/media/ folder.

This script integrates with the centralized configuration system and can be used 
to capture weather data from various Philippine cities for multimedia composition.

Features:
- Captures screenshots or videos of weather pages
- Supports multiple Philippine cities
- Uses centralized configuration from config.py
- Saves to generated/media/ directory
- Comprehensive logging and error handling
- Supports configurable durations and quality settings

Usage Examples:

1. As a module:
    from step6_weather_recorder import ProvincialWeatherRecorder
    
    recorder = ProvincialWeatherRecorder()
    media_path = recorder.capture_weather(
        city_key="pulilan"
    )

2. Command line:
    python step6_weather_recorder.py --city=pulilan --type=screenshot
    python step6_weather_recorder.py --city=pulilan --type=video --duration=30
    python step6_weather_recorder.py --city=pulilan2 --type=video --duration=30
    python step6_weather_recorder.py --city=baguio --type=both

3. List available cities:
    python step6_weather_recorder.py --list-cities

File Structure Created:

    generated/media/
    ├── pulilan_weather_map1_20250525_143022.png
    ├── pulilan_weather_map2_20250525_143045.webm
    └── manila_weather_20250525_143102.png
    
python step6_weather_recorder.py --city=pulilan --type=video --duration=10 --output weather_map1
python step6_weather_recorder.py --city=pulilan2 --type=video --duration=10 --output weather_map2
"""

import os
import time
import cv2
import numpy as np
from datetime import datetime
from PIL import Image
import io
from loguru import logger
from playwright.sync_api import sync_playwright
from typing import Dict, Any, Optional, Union, List
import config

# Configuration for different cities - now stored in config system
DEFAULT_CITY_CONFIGS = {
    "pulilan": {
        "name": "Pulilan",
        "url": "https://www.windy.com/14.906/120.851?temp,14.903,120.852,14",
        "link_text": "Pulilan",
        "file_prefix": "pulilan_weather_map1"
    },
    "pulilan2": {
        "name": "Pulilan",
        "url": "https://www.ventusky.com/14.930;120.850",
        "link_text": "Pulilan",
        "file_prefix": "pulilan_weather_map2"
    },
    "calayan": {
        "name": "Calayan",
        "url": "https://www.ventusky.com/?p=19.22;121.38;8&l=feel",
        "link_text": "Calayan",
        "file_prefix": "calayan_weather"
    },
    "aparri": {
        "name": "Aparri",
        "url": "https://www.ventusky.com/?p=18.21;122.48;8&l=feel",
        "link_text": "Aparri",
        "file_prefix": "aparri_weather"
    },
    "baguio": {
        "name": "Baguio City",
        "url": "https://www.ventusky.com/?p=16.29;121.58;8&l=feel",
        "link_text": "Baguio City",
        "file_prefix": "baguio_weather"
    },
    "laoag": {
        "name": "Laoag City",
        "url": "https://www.ventusky.com/?p=18.27;121.35;8&l=feel",
        "link_text": "Laoag City",
        "file_prefix": "laoag_weather"
    },
    "manila": {
        "name": "Metro Manila",
        "url": "https://www.ventusky.com/?p=14.46;122.07;8&l=feel",
        "link_text": "Maynila",
        "file_prefix": "manila_weather"
    },
    "tuguegarao": {
        "name": "Tuguegarao City",
        "url": "https://www.ventusky.com/?p=17.37;122.45;8&l=feel",
        "link_text": "Tuguegarao City",
        "file_prefix": "tuguegarao_weather"
    },
    "santiago_isabela": {
        "name": "Santiago Isabela",
        "url": "https://www.ventusky.com/?p=16.98;122.21;8&l=feel",
        "link_text": "Santiago",
        "file_prefix": "santiago_weather"
    },
    "banaue_ifugao": {
        "name": "Banaue Ifugao",
        "url": "https://www.ventusky.com/?p=16.71;121.27;8&l=feel",
        "link_text": "Banaue",
        "file_prefix": "banaue_weather"
    },
    "vigan": {
        "name": "Vigan City",
        "url": "https://www.ventusky.com/?p=17.53;121.32;8&l=feel",
        "link_text": "Vigan City",
        "file_prefix": "vigan_weather"
    },
    "san_fernando_la_union": {
        "name": "San Fernando La Union",
        "url": "https://www.ventusky.com/?p=16.534;120.749;9&l=feel",
        "link_text": "San Fernando",
        "file_prefix": "san_fernando_la_union_weather"
    },
    "urdaneta": {
        "name": "Urdaneta",
        "url": "https://www.ventusky.com/?p=15.841;120.977;9&l=feel",
        "link_text": "Urdaneta",
        "file_prefix": "urdaneta_weather"
    }
}

# Load city configs from config or use defaults
CITY_CONFIGS = getattr(config, 'PROVINCIAL_WEATHER_CITIES', DEFAULT_CITY_CONFIGS)

print(f"[WEATHER_RECORDER] Loaded {len(CITY_CONFIGS)} city configurations from config")

class ProvincialWeatherRecorder:
    """Weather recorder that saves to generated/media/ folder with config integration"""
    
    def __init__(self):
        """Initialize the recorder with centralized configuration"""
        # Set up media directory
        self.media_dir = os.path.join(config.BASE_DIR, 'generated', 'media')
        
        # Video recording defaults from config
        self.default_duration = getattr(config, 'DEFAULT_WEATHER_VIDEO_DURATION', 15)
        self.default_fps = getattr(config, 'DEFAULT_WEATHER_VIDEO_FPS', 1)
        self.default_viewport = getattr(config, 'DEFAULT_WEATHER_VIEWPORT', (1200, 800))
        
        # Create media directory if it doesn't exist
        os.makedirs(self.media_dir, exist_ok=True)
        
        print(f"[WEATHER_RECORDER] Initialized with centralized configuration")
        print(f"[WEATHER_RECORDER] Media directory: {self.media_dir}")
        print(f"[WEATHER_RECORDER] Default duration: {self.default_duration}s")
        print(f"[WEATHER_RECORDER] Default FPS: {self.default_fps}")
        print(f"[WEATHER_RECORDER] Default viewport: {self.default_viewport}")
    
    def capture_weather(
        self, 
        city_key: str, 
        capture_type: str = "video",
        duration_seconds: int = None,
        fps: int = None,
        output_filename: Optional[str] = None
    ) -> Union[str, List[str]]:
        """
        Capture weather data for a city and save to generated/media/
        
        Args:
            city_key: Key for the city configuration
            capture_type: "video", "screenshot", or "both"
            duration_seconds: Duration for video capture (uses config default if None)
            fps: Frames per second for video (uses config default if None)
            output_filename: Custom filename (without extension). If None, auto-generates based on city and timestamp
            
        Returns:
            Path to the captured media file(s)
        """
        print(f"[WEATHER_RECORDER] Starting capture for {city_key}")
        
        if city_key not in CITY_CONFIGS:
            raise ValueError(f"City '{city_key}' not found in configurations. Available: {list(CITY_CONFIGS.keys())}")
        
        # Use config defaults if not specified
        duration_seconds = duration_seconds or self.default_duration
        fps = fps or self.default_fps
        
        city_config = CITY_CONFIGS[city_key]
        
        print(f"[WEATHER_RECORDER] Using media directory: {self.media_dir}")
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determine base filename
        if output_filename:
            base_filename = output_filename
            print(f"[WEATHER_RECORDER] Using custom filename: {base_filename}")
        else:
            base_filename = f"{city_config['file_prefix']}_{timestamp}"
            print(f"[WEATHER_RECORDER] Using auto-generated filename: {base_filename}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': self.default_viewport[0], 'height': self.default_viewport[1]}
                )
                page = context.new_page()
                
                print(f"[WEATHER_RECORDER] Loading {city_config['name']} weather page...")
                page.goto(city_config['url'])
                page.wait_for_load_state('networkidle')
                time.sleep(5)  # Allow page to fully load
                
                # Hide header element if it's a Ventusky site
                if 'ventusky.com' in city_config['url']:
                    try:
                        print(f"[WEATHER_RECORDER] Hiding Ventusky header for cleaner capture...")
                        page.evaluate("""
                            const header = document.querySelector('#header');
                            if (header) {
                                header.style.display = 'none';
                                console.log('Header hidden successfully');
                            }
                        """)
                        time.sleep(1)  # Give time for the change to take effect
                    except Exception as e:
                        print(f"[WEATHER_RECORDER] Could not hide header: {e}")
                
                # Try to click on city link if needed
                self._try_click_city_link(page, city_config)
                
                captured_files = []
                
                # Capture screenshot if requested
                if capture_type in ["screenshot", "both"]:
                    screenshot_path = self._capture_screenshot(
                        page, self.media_dir, base_filename
                    )
                    captured_files.append(screenshot_path)
                    print(f"[WEATHER_RECORDER] Screenshot saved: {screenshot_path}")
                
                # Capture video if requested
                if capture_type in ["video", "both"]:
                    video_path = self._capture_video(
                        page, self.media_dir, base_filename, duration_seconds, fps
                    )
                    captured_files.append(video_path)
                    print(f"[WEATHER_RECORDER] Video saved: {video_path}")
                
                browser.close()
                
                print(f"[WEATHER_RECORDER] Capture completed for {city_config['name']}")
                logger.info(f"Weather capture completed: {city_key} → {captured_files}")
                
                return captured_files[0] if len(captured_files) == 1 else captured_files
                
        except Exception as e:
            logger.error(f"[WEATHER_RECORDER] Error capturing weather for {city_key}: {str(e)}")
            raise
    
    def _try_click_city_link(self, page, city_config: Dict[str, Any]):
        """Try to click on the city link if it exists"""
        try:
            print(f"[WEATHER_RECORDER] Looking for {city_config['link_text']} link...")
            city_link = page.locator(f'a:has-text("{city_config["link_text"]}")')
            
            if city_link.count() > 0:
                city_link.first.click()
                print(f"[WEATHER_RECORDER] Successfully clicked on {city_config['link_text']}")
                page.wait_for_load_state('networkidle')
                time.sleep(3)
            else:
                print(f"[WEATHER_RECORDER] {city_config['link_text']} link not found, using current view")
                
        except Exception as e:
            print(f"[WEATHER_RECORDER] Could not click on {city_config['link_text']} link: {e}")
    
    def _capture_screenshot(
        self, 
        page, 
        media_dir: str, 
        base_filename: str
    ) -> str:
        """Capture a screenshot of the weather page"""
        filename = f"{base_filename}.png"
        screenshot_path = os.path.join(media_dir, filename)
        
        # Take screenshot
        screenshot = page.screenshot()
        
        # Save screenshot
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot)
        
        print(f"[WEATHER_RECORDER] Screenshot captured: {screenshot_path}")
        logger.info(f"Screenshot captured: {screenshot_path}")
        return screenshot_path
    
    def _capture_video(
        self, 
        page, 
        media_dir: str, 
        base_filename: str,
        duration_seconds: int,
        fps: int
    ) -> str:
        """Capture a video of the weather page"""
        filename = f"{base_filename}.webm"
        video_path = os.path.join(media_dir, filename)
        
        # Setup video writer for WebM format
        fourcc = cv2.VideoWriter_fourcc(*'VP80')  # VP8 codec for WebM
        out = cv2.VideoWriter(video_path, fourcc, fps, self.default_viewport)
        
        print(f"[WEATHER_RECORDER] Recording video for {duration_seconds} seconds at {fps} fps...")
        start_time = time.time()
        frame_count = 0
        
        try:
            while (time.time() - start_time) < duration_seconds:
                # Take screenshot and convert to video frame
                screenshot = page.screenshot()
                image = Image.open(io.BytesIO(screenshot))
                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                out.write(frame)
                frame_count += 1
                
                elapsed = time.time() - start_time
                print(f"[WEATHER_RECORDER] Recording: {elapsed:.1f}/{duration_seconds}s - Frames: {frame_count}")
                
                time.sleep(1/fps)
                
        except KeyboardInterrupt:
            print("[WEATHER_RECORDER] Recording stopped by user")
        finally:
            out.release()
            print(f"[WEATHER_RECORDER] Video recording completed: {video_path}")
            logger.info(f"Video recording completed: {video_path} ({frame_count} frames)")
        
        return video_path
    
    def list_available_cities(self) -> Dict[str, str]:
        """Get a list of available cities and their names"""
        return {key: config['name'] for key, config in CITY_CONFIGS.items()}
    
    def get_city_config(self, city_key: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific city"""
        return CITY_CONFIGS.get(city_key)
    
    def capture_multiple_cities(
        self, 
        city_keys: List[str], 
        capture_type: str = "screenshot"
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Capture weather data for multiple cities
        
        Args:
            city_keys: List of city keys to capture
            capture_type: "video", "screenshot", or "both"
            
        Returns:
            Dictionary mapping city keys to their captured file paths
        """
        results = {}
        print(f"[WEATHER_RECORDER] Starting multi-city capture for {len(city_keys)} cities")
        logger.info(f"Multi-city capture started: {len(city_keys)} cities")
        
        for i, city_key in enumerate(city_keys, 1):
            print(f"[WEATHER_RECORDER] Processing city {i}/{len(city_keys)}: {city_key}")
            try:
                result = self.capture_weather(city_key, capture_type)
                results[city_key] = result
                print(f"[WEATHER_RECORDER] ✅ {city_key} completed")
                logger.info(f"City capture completed: {city_key}")
            except Exception as e:
                print(f"[WEATHER_RECORDER] ❌ {city_key} failed: {str(e)}")
                logger.error(f"City capture failed: {city_key} - {str(e)}")
                results[city_key] = None
        
        success_count = sum(1 for r in results.values() if r is not None)
        print(f"[WEATHER_RECORDER] Multi-city capture completed. Success: {success_count}/{len(city_keys)}")
        logger.info(f"Multi-city capture completed: {success_count}/{len(city_keys)} successful")
        return results


def capture_weather_for_city(city_key: str, capture_type: str = "video") -> Union[str, List[str]]:
    """
    Convenience function to capture weather for a city
    
    Args:
        city_key: City to capture weather for
        capture_type: "video", "screenshot", or "both"
        
    Returns:
        Path to captured media file(s)
    """
    recorder = ProvincialWeatherRecorder()
    return recorder.capture_weather(city_key, capture_type)


def print_usage_examples():
    """Print comprehensive usage examples"""
    print("""
🌤️  Provincial Weather Recorder - Step 6 - Usage Examples
════════════════════════════════════════════════════════

📷 Capture Screenshot:
   python step6_weather_recorder.py --city=pulilan --type=screenshot

🎥 Capture Video:
   python step6_weather_recorder.py --city=manila --type=video

🎬 Capture Video with custom duration:
   python step6_weather_recorder.py --city=baguio --type=video --duration=30 --fps=2

📷 Capture Both Screenshot and Video:
   python step6_weather_recorder.py --city=tuguegarao --type=both

📝 Custom Output Filename:
   python step6_weather_recorder.py --city=manila --type=video --output=custom_weather_video

🏙️  List Available Cities:
   python step6_weather_recorder.py --list-cities

📂 File Structure:

   generated/media/
   ├── pulilan_weather_map1_20250525_143022.png
   ├── manila_weather_20250525_143045.webm
   ├── baguio_weather_20250525_143102.webm
   └── custom_weather_video.webm

🐍 Python Module Usage:
   from step6_weather_recorder import ProvincialWeatherRecorder
   
   recorder = ProvincialWeatherRecorder()
   path = recorder.capture_weather("pulilan")
""")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Provincial Weather Recorder - Capture weather data for Philippine cities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --city=pulilan --type=screenshot
  %(prog)s --city=manila --type=video --duration=30
  %(prog)s --city=baguio --type=video --output=my_custom_video
  %(prog)s --list-cities
        """
    )
    
    parser.add_argument('--city', type=str, 
                       choices=list(CITY_CONFIGS.keys()),
                       help="City to capture weather for")
    parser.add_argument('--type', type=str, default="video",
                       choices=["video", "screenshot", "both"],
                       help="Type of capture to perform (default: video)")
    parser.add_argument('--duration', type=int,
                       help=f"Video duration in seconds (default from config: {getattr(config, 'DEFAULT_WEATHER_VIDEO_DURATION', 15)})")
    parser.add_argument('--fps', type=int,
                       help=f"Video frames per second (default from config: {getattr(config, 'DEFAULT_WEATHER_VIDEO_FPS', 1)})")
    parser.add_argument('--output', type=str,
                       help="Custom output filename (without extension). If not provided, auto-generates based on city and timestamp")
    parser.add_argument('--list-cities', action='store_true',
                       help="List all available cities and exit")
    parser.add_argument('--examples', action='store_true',
                       help="Show usage examples and exit")
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.examples:
        print_usage_examples()
        exit(0)
    
    if args.list_cities:
        print("🏙️  Available Cities:")
        print("=" * 50)
        for key, city_config in CITY_CONFIGS.items():
            print(f"   {key:<20} - {city_config['name']}")
        print(f"\nTotal: {len(CITY_CONFIGS)} cities available")
        exit(0)
    
    # Validate required arguments
    if not args.city:
        print("❌ Error: --city is required")
        print("💡 Use --list-cities to see available options")
        print("💡 Example: --city=pulilan")
        exit(1)
    
    # Display configuration with config defaults
    recorder = ProvincialWeatherRecorder()
    duration = args.duration or recorder.default_duration
    fps = args.fps or recorder.default_fps
    
    print(f"🌤️  Provincial Weather Recorder - Step 6")
    print(f"City: {CITY_CONFIGS[args.city]['name']}")
    print(f"Output: {recorder.media_dir}")
    print(f"Capture Type: {args.type}")
    if args.output:
        print(f"Output Filename: {args.output}")
    if args.type in ["video", "both"]:
        print(f"Duration: {duration} seconds")
        print(f"FPS: {fps}")
    print("-" * 50)
    
    try:
        result = recorder.capture_weather(
            city_key=args.city,
            capture_type=args.type,
            duration_seconds=args.duration,
            fps=args.fps,
            output_filename=args.output
        )
        
        print(f"✅ Capture completed successfully!")
        if isinstance(result, list):
            print(f"📁 Files created:")
            for file_path in result:
                print(f"   - {file_path}")
        else:
            print(f"📁 File created: {result}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Weather capture failed: {str(e)}")
        exit(1) 
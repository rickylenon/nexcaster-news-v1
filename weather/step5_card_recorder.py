#!/usr/bin/env python3
"""
Weather Card Recorder - Step 5

Captures weather card visualizations from the Flask weather cards interface
and generates uniform WebM videos for multimedia composition.

This module integrates with:
- weather_cards.html served via Flask app
- constants.py for card definitions
- Real-time weather data from /api/weather/latest
- Centralized configuration from config.py

Features:
- Captures all weather card types defined in constants.py
- Uniform 1200x800 video output
- WebM format optimized for composition
- Simplified capture without external dependencies
- Progress tracking and error handling
- Configurable video duration and quality
- Defaults to data/latest/multimedia output directory

Usage:
    # Basic capture of all weather cards
    python step5_card_recorder.py
    
    # Custom job ID and Flask server
    python step5_card_recorder.py --job-id "weather_20250127" --flask-url "http://localhost:5001"
    
    # Custom video duration and quality
    python step5_card_recorder.py --video-duration 8 --video-fps 30
    
    # Debug mode with visible browser
    python step5_card_recorder.py --debug
    
    # Capture specific cards only
    python step5_card_recorder.py --cards card-temperature card-wind card-humidity

Library usage:
    from step5_card_recorder import WeatherCardRecorder
    
    recorder = WeatherCardRecorder()
    
    # Capture all cards
    videos = await recorder.capture_all_cards()
    
    # Capture specific cards
    videos = await recorder.capture_cards(['card-temperature', 'card-wind', 'card-humidity'])
"""

import os
import sys
import asyncio
import argparse
import time
import json
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from playwright.async_api import async_playwright
from loguru import logger
import requests

# Import constants and configuration
from constants import WEATHER_MEDIA_DESCRIPTIONS, get_description
import config

# Extract weather cards from media descriptions (filter card-* items)
WEATHER_CARD_DESCRIPTIONS = {k: v for k, v in WEATHER_MEDIA_DESCRIPTIONS.items() if k.startswith('card-')}

print(f"[CARD_RECORDER] Loaded {len(WEATHER_CARD_DESCRIPTIONS)} weather card types from constants")

class WeatherCardRecorder:
    """Captures weather card videos from Flask interface for multimedia composition"""
    
    def __init__(self, 
                 flask_url: str = None,
                 viewport_size: Tuple[int, int] = None,
                 video_fps: int = None,
                 job_id: str = "latest",
                 use_latest_manager: bool = True):
        """
        Initialize weather card recorder system with config defaults
        
        Args:
            flask_url: URL of the Flask weather cards interface (uses config default)
            viewport_size: Video viewport dimensions (width, height) (uses config default)
            video_fps: Video frame rate (uses config default)
            job_id: Job ID for file organization
            use_latest_manager: Whether to use LatestMediaManager for automatic organization
        """
        # Use configuration defaults
        self.flask_url = flask_url or getattr(config, 'DEFAULT_FLASK_URL', "http://localhost:5001")
        viewport_size = viewport_size or getattr(config, 'DEFAULT_CARD_VIEWPORT', (1200, 800))
        self.viewport_width, self.viewport_height = viewport_size
        self.video_fps = video_fps or getattr(config, 'DEFAULT_CARD_FPS', 30)
        self.job_id = job_id
        
        print(f"[CARD_RECORDER] Using configuration defaults:")
        print(f"[CARD_RECORDER] Flask URL: {self.flask_url}")
        print(f"[CARD_RECORDER] Viewport: {self.viewport_width}x{self.viewport_height}")
        print(f"[CARD_RECORDER] Video FPS: {self.video_fps}")
        
        # Set output directory - use config defaults
        self.output_dir = Path(getattr(config, 'DEFAULT_CARD_OUTPUT_DIR', 'data/latest/multimedia'))
        if job_id != "latest":
            self.output_dir = Path(f"data/{job_id}/multimedia")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[CARD_RECORDER] Initialized capture system")
        print(f"[CARD_RECORDER] Job ID: {self.job_id}")
        print(f"[CARD_RECORDER] Output directory: {self.output_dir}")
        
        logger.info(f"WeatherCardRecorder initialized with output: {self.output_dir}")
    
    def check_flask_server(self) -> bool:
        """Check if Flask server is running and accessible"""
        try:
            print(f"[CARD_RECORDER] Checking Flask server availability...")
            
            # Check health endpoint
            health_url = f"{self.flask_url}/api/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"[CARD_RECORDER] ✅ Flask server is healthy")
                print(f"[CARD_RECORDER] Server: {health_data.get('server', 'Unknown')}")
                print(f"[CARD_RECORDER] Available files: {health_data.get('available_files', 0)}")
                return True
            else:
                print(f"[CARD_RECORDER] ❌ Flask server health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[CARD_RECORDER] ❌ Flask server not accessible: {str(e)}")
            print(f"[CARD_RECORDER] Make sure to start the Flask app with: python app.py")
            return False
    
    def get_weather_card_url(self, card_key: str) -> str:
        """Generate the weather card URL for a specific card"""
        if card_key not in WEATHER_CARD_DESCRIPTIONS:
            raise ValueError(f"Unknown weather card: {card_key}")
        
        # Map card-* format to URL parameter format
        url_param = card_key.replace('card-', '')
        url = f"{self.flask_url}/?card={url_param}&data=api/weather/latest"
        return url
    
    def get_card_filename(self, card_key: str) -> str:
        """Generate filename for a card"""
        return f"card-{card_key.replace('card-', '')}.webm"
    
    def get_card_duration(self, card_key: str) -> int:
        """Get default duration for a card from config or fallback"""
        # Try to get from config first
        duration_config = getattr(config, 'DEFAULT_CARD_DURATIONS', {})
        if duration_config and card_key in duration_config:
            return duration_config[card_key]
        
        # Fallback duration map
        duration_map = {
            'card-temperature': 6,
            'card-feels-like': 5,
            'card-cloud-cover': 5,
            'card-precipitation': 7,
            'card-wind': 6,
            'card-humidity': 6,
            'card-uv': 5,
            'card-aqi': 5,
            'card-visibility': 5,
            'card-pressure': 6,
            'card-sun': 6,
            'card-moon': 5,
            'card-current': 8,
            'card-hourly': 10,
            'weather_overview': 10,
            'weather_current_overview': 8
        }
        return duration_map.get(card_key, 5)
    
    async def capture_weather_card(self, 
                                   card_key: str, 
                                   custom_duration: Optional[int] = None,
                                   headless: bool = True) -> str:
        """
        Capture a single weather card as a WebM video
        
        Args:
            card_key: Key identifying the weather card type (e.g., 'card-temperature')
            custom_duration: Override default duration for this card
            headless: Whether to run browser in headless mode
            
        Returns:
            Path to the generated video file
        """
        print(f"\n[CARD_RECORDER] Capturing weather card: {card_key}")
        
        # Validate card key
        if card_key not in WEATHER_CARD_DESCRIPTIONS:
            raise ValueError(f"Unknown weather card: {card_key}")
        
        # Build URL for the weather card
        card_url = self.get_weather_card_url(card_key)
        duration = custom_duration or self.get_card_duration(card_key)
        output_filename = self.get_card_filename(card_key)
        output_path = self.output_dir / output_filename
        
        print(f"[CARD_RECORDER] URL: {card_url}")
        print(f"[CARD_RECORDER] Duration: {duration}s")
        print(f"[CARD_RECORDER] Output: {output_filename}")
        print(f"[CARD_RECORDER] Description: {get_description(card_key)}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context(
                    viewport={'width': self.viewport_width, 'height': self.viewport_height}
                )
                page = await context.new_page()
                
                print(f"[CARD_RECORDER] Loading page...")
                await page.goto(card_url)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)  # Allow animations to settle
                
                # Setup video writer
                fourcc = cv2.VideoWriter_fourcc(*'VP80')  # VP8 codec for WebM
                out = cv2.VideoWriter(str(output_path), fourcc, self.video_fps, 
                                    (self.viewport_width, self.viewport_height))
                
                print(f"[CARD_RECORDER] Recording video for {duration} seconds at {self.video_fps} fps...")
                start_time = time.time()
                frame_count = 0
                target_frames = duration * self.video_fps
                
                try:
                    while frame_count < target_frames:
                        # Take screenshot and convert to video frame
                        screenshot = await page.screenshot()
                        image = Image.open(io.BytesIO(screenshot))
                        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                        out.write(frame)
                        frame_count += 1
                        
                        elapsed = time.time() - start_time
                        if frame_count % 30 == 0:  # Print every 30 frames (1 second at 30fps)
                            print(f"[CARD_RECORDER] Recording {card_key}: {elapsed:.1f}s - Frames: {frame_count}/{target_frames}")
                        
                        # Don't sleep too long - just a small delay to prevent overwhelming
                        await asyncio.sleep(0.01)
                        
                except KeyboardInterrupt:
                    print("[CARD_RECORDER] Recording stopped by user")
                finally:
                    out.release()
                    
                final_duration = time.time() - start_time
                print(f"[CARD_RECORDER] Recorded {card_key}: {frame_count} frames in {final_duration:.1f}s")
                
                await browser.close()
            
            print(f"[CARD_RECORDER] ✅ Successfully captured: {output_filename}")
            logger.info(f"Captured weather card {card_key}: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            error_msg = f"Failed to capture weather card {card_key}: {str(e)}"
            print(f"[CARD_RECORDER] ❌ {error_msg}")
            logger.error(error_msg)
            raise
    
    async def capture_all_cards(self, 
                                custom_durations: Optional[Dict[str, int]] = None,
                                headless: bool = True) -> Dict[str, str]:
        """
        Capture all weather cards as WebM videos
        
        Args:
            custom_durations: Override durations for specific cards
            headless: Whether to run browser in headless mode
            
        Returns:
            Dictionary mapping card keys to video file paths
        """
        print(f"\n[CARD_RECORDER] Starting capture of all weather cards")
        
        # Check Flask server first
        if not self.check_flask_server():
            raise Exception("Flask server is not available. Please start it with: python app.py")
        
        captured_videos = {}
        cards_to_capture = list(WEATHER_CARD_DESCRIPTIONS.keys())
        
        total_cards = len(cards_to_capture)
        print(f"[CARD_RECORDER] Will capture {total_cards} weather cards")
        
        # Capture each card
        for i, card_key in enumerate(cards_to_capture, 1):
            print(f"\n[CARD_RECORDER] === Card {i}/{total_cards}: {card_key} ===")
            
            try:
                # Get custom duration if specified
                duration = None
                if custom_durations and card_key in custom_durations:
                    duration = custom_durations[card_key]
                
                # Capture the card
                video_path = await self.capture_weather_card(
                    card_key=card_key,
                    custom_duration=duration,
                    headless=headless
                )
                
                captured_videos[card_key] = video_path
                
                # Small delay between captures to avoid overwhelming the server
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[CARD_RECORDER] ⚠️ Failed to capture {card_key}: {str(e)}")
                logger.warning(f"Failed to capture {card_key}: {str(e)}")
                # Continue with other cards
                continue
        
        print(f"\n[CARD_RECORDER] === CAPTURE COMPLETE ===")
        print(f"[CARD_RECORDER] Successfully captured: {len(captured_videos)}/{total_cards} cards")
        print(f"[CARD_RECORDER] Output directory: {self.output_dir}")
        
        for card_key, video_path in captured_videos.items():
            print(f"[CARD_RECORDER] ✅ {card_key} → {os.path.basename(video_path)}")
        
        logger.info(f"Weather card capture complete: {len(captured_videos)} cards captured")
        
        return captured_videos
    
    async def capture_cards(self, 
                            card_keys: List[str],
                            custom_durations: Optional[Dict[str, int]] = None,
                            headless: bool = True) -> Dict[str, str]:
        """
        Capture specific weather cards
        
        Args:
            card_keys: List of card keys to capture (e.g., ['card-temperature', 'card-wind'])
            custom_durations: Override durations for specific cards
            headless: Whether to run browser in headless mode
            
        Returns:
            Dictionary mapping card keys to video file paths
        """
        print(f"\n[CARD_RECORDER] Capturing specific cards: {card_keys}")
        
        # Check Flask server first
        if not self.check_flask_server():
            raise Exception("Flask server is not available. Please start it with: python app.py")
        
        captured_videos = {}
        
        for i, card_key in enumerate(card_keys, 1):
            print(f"\n[CARD_RECORDER] === Card {i}/{len(card_keys)}: {card_key} ===")
            
            try:
                # Validate card key
                if card_key not in WEATHER_CARD_DESCRIPTIONS:
                    print(f"[CARD_RECORDER] ⚠️ Unknown card key: {card_key}")
                    continue
                
                # Get custom duration if specified
                duration = None
                if custom_durations and card_key in custom_durations:
                    duration = custom_durations[card_key]
                
                # Capture the card
                video_path = await self.capture_weather_card(
                    card_key=card_key,
                    custom_duration=duration,
                    headless=headless
                )
                
                captured_videos[card_key] = video_path
                
                # Small delay between captures
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[CARD_RECORDER] ⚠️ Failed to capture {card_key}: {str(e)}")
                logger.warning(f"Failed to capture {card_key}: {str(e)}")
                continue
        
        print(f"\n[CARD_RECORDER] === CAPTURE COMPLETE ===")
        print(f"[CARD_RECORDER] Successfully captured: {len(captured_videos)}/{len(card_keys)} cards")
        
        return captured_videos
    
    def list_available_cards(self):
        """List all available weather cards with descriptions"""
        print(f"\n[CARD_RECORDER] === AVAILABLE WEATHER CARDS ===")
        
        print(f"\nAvailable Cards ({len(WEATHER_CARD_DESCRIPTIONS)}):")
        for i, (card_key, description) in enumerate(WEATHER_CARD_DESCRIPTIONS.items(), 1):
            duration = self.get_card_duration(card_key)
            print(f"  {i:2d}. {card_key:20s} - {description[:60]}... ({duration}s)")
        
        print(f"\nTotal: {len(WEATHER_CARD_DESCRIPTIONS)} cards available")

async def main():
    """Command line interface for weather card capture with config defaults"""
    parser = argparse.ArgumentParser(
        description="Capture weather card videos from Flask interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture all weather cards to data/latest/multimedia (default)
  python step5_card_recorder.py

  # Capture with custom job ID
  python step5_card_recorder.py --job-id "weather_20250127"

  # Capture specific cards only
  python step5_card_recorder.py --cards card-temperature card-wind card-humidity

  # Custom durations and visible browser
  python step5_card_recorder.py --video-duration 10 --show-browser

  # Debug mode with visible browser
  python step5_card_recorder.py --debug

  # Custom Flask server URL
  python step5_card_recorder.py --flask-url "http://192.168.1.100:5001"
        """
    )
    
    parser.add_argument(
        '--flask-url',
        help=f'URL of the Flask weather cards interface (default from config: {getattr(config, "DEFAULT_FLASK_URL", "http://localhost:5001")})'
    )
    
    parser.add_argument(
        '--job-id', 
        default='latest',
        help='Job ID for file organization (default: latest - saves to data/latest/multimedia)'
    )
    
    parser.add_argument(
        '--output', 
        help='Output directory name (overrides --job-id, disables latest manager)'
    )
    
    parser.add_argument(
        '--no-latest',
        action='store_true',
        help='Disable LatestMediaManager integration'
    )
    
    parser.add_argument(
        '--viewport-width',
        type=int,
        help=f'Video viewport width (default from config: {getattr(config, "DEFAULT_CARD_VIEWPORT", (1200, 800))[0]})'
    )
    
    parser.add_argument(
        '--viewport-height',
        type=int,
        help=f'Video viewport height (default from config: {getattr(config, "DEFAULT_CARD_VIEWPORT", (1200, 800))[1]})'
    )
    
    parser.add_argument(
        '--video-duration',
        type=int,
        help='Override default video duration for all cards (seconds)'
    )
    
    parser.add_argument(
        '--video-fps',
        type=int,
        help=f'Video frame rate (default from config: {getattr(config, "DEFAULT_CARD_FPS", 30)})'
    )
    
    parser.add_argument(
        '--cards',
        nargs='*',
        help='Capture only specific cards (e.g., --cards card-temperature card-wind card-humidity)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run with visible browser (for debugging)'
    )
    
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Show browser window (default is headless mode)'
    )
    
    parser.add_argument(
        '--list-cards',
        action='store_true',
        help='List all available weather cards and exit'
    )
    
    args = parser.parse_args()
    
    # Handle output parameter and latest manager settings
    use_latest_manager = not args.no_latest and not args.output
    job_id = args.output if args.output else args.job_id
    
    # Build viewport size from args or config defaults
    config_viewport = getattr(config, 'DEFAULT_CARD_VIEWPORT', (1200, 800))
    viewport_width = args.viewport_width or config_viewport[0]
    viewport_height = args.viewport_height or config_viewport[1]
    
    # Initialize capture system with config defaults
    recorder = WeatherCardRecorder(
        flask_url=args.flask_url,
        viewport_size=(viewport_width, viewport_height),
        video_fps=args.video_fps,
        job_id=job_id,
        use_latest_manager=use_latest_manager
    )
    
    # List cards and exit if requested
    if args.list_cards:
        recorder.list_available_cards()
        return
    
    try:
        # Setup custom durations if specified
        custom_durations = {}
        if args.video_duration:
            # Apply custom duration to all cards
            for card_key in WEATHER_CARD_DESCRIPTIONS.keys():
                custom_durations[card_key] = args.video_duration
            print(f"[CARD_RECORDER] Using custom duration: {args.video_duration}s for all cards")
        
        # Determine headless mode (default is headless unless explicitly shown)
        headless_mode = not (args.debug or args.show_browser)
        
        if args.cards:
            # Capture specific cards
            print(f"[CARD_RECORDER] Capturing specific cards: {args.cards}")
            videos = await recorder.capture_cards(
                card_keys=args.cards,
                custom_durations=custom_durations,
                headless=headless_mode
            )
        else:
            # Capture all cards
            print(f"[CARD_RECORDER] Capturing all weather cards")
            videos = await recorder.capture_all_cards(
                custom_durations=custom_durations,
                headless=headless_mode
            )
        
        # Final summary
        print(f"\n🎬 Weather cards capture completed!")
        print(f"📁 Output directory: {recorder.output_dir}")
        print(f"🎯 Cards captured: {len(videos)}")
        
        if videos:
            print(f"\n📹 Generated Videos:")
            for card_key, video_path in videos.items():
                file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
                size_mb = file_size / (1024 * 1024)
                print(f"   {card_key:20s} → {os.path.basename(video_path):30s} ({size_mb:.1f} MB)")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Weather card capture failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level:8} | {message}")
    
    asyncio.run(main()) 
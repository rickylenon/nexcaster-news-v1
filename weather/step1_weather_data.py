#!/usr/bin/env python3
import os
import sys

# Since we're now in the root directory, add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from loguru import logger
import aiohttp
import json
import os
from typing import Dict, Any, Optional, List
import hashlib
import base64
from datetime import datetime
import asyncio
import argparse
import logging
from openai import OpenAI
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

"""
Enhanced Weather Data Scraping System for Municipal Weather Reporting

This module provides advanced functionality to scrape weather data from various websites
with a focus on rich municipal weather reporting. Uses OpenAI Vision for comprehensive
data extraction including visual analysis for engaging weather storytelling.

PRIMARY RECOMMENDED SOURCE: MSN Weather (with location override for accurate municipal data)

Command-line usage:

    # MSN Weather (RECOMMENDED) - with location override for municipal accuracy
    python step1_scrape_data.py \
        -u "https://www.msn.com/en-ph/weather/forecast/in-Pulilan,PH-03?loc=eyJsIjoiUHVsaWxhbiIsInIiOiJQSC0wMyIsImMiOiJQaGlsaXBwaW5lcyIsImkiOiJQSCIsIngiOiIxMjAuODI5NCIsInkiOiIxNC45Mjg5In0%3D&weadegreetype=C&ocid=ansmsnweather" \
        --municipality "Pulilan" --region "Bulacan" --country "Philippines" \
        --timeout 25000 --headless
    
    # WorldWeatherOnline (alternative)
    python step1_scrape_data.py \
        -u "https://www.worldweatheronline.com/pulilan-weather/bulacan/ph.aspx" \
        --timeout 15000
    
    # Debug mode (visible browser)
    python step1_scrape_data.py \
        -u "https://www.msn.com/en-ph/weather/forecast/in-Pulilan,PH-03?..." \
        --municipality "Pulilan" --region "Bulacan" --no-headless --debug

Core Options:
    --url, -u              Weather page URL to scrape (uses config default if not provided)
    --timeout              Page timeout in milliseconds (default from config)
    --headless             Run browser in headless mode
    --no-headless          Run browser in visible mode (for debugging)
    --slowmo               Browser slow motion delay in milliseconds (default from config)
    --debug                Enable debug logging
    --save-to-latest       Save to data/latest directory (default: True)
    --save-to-raw          Save to data/weather/raw directory (legacy mode)

Location Override (recommended for MSN):
    --municipality         Municipality/city name (default from config)
    --region               Region/province name (default from config) 
    --country              Country name (default from config)

Enhanced Features:
    • OpenAI Vision analysis for rich weather data extraction
    • Visual storytelling elements (page mood, colors, atmosphere)
    • Municipal context with local weather impact
    • Comprehensive hourly and daily forecasts
    • Current weather focus (70%) + today's evolution (20%) + tomorrow preview (10%)
    • Clean weather-focused data (no traffic/transportation)

Data Output:
    By default, saves enhanced JSON to generated/weather_data.json.
    Contains current conditions, visual analysis, hourly forecasts, municipal context, 
    and atmospheric storytelling data optimized for engaging weather report segment generation.

Library usage:
    from step1_scrape_data import ScrapingSystem
    
    config = {'HEADLESS': True, 'DATA_DIR': 'data', 'SOURCE_NAME': 'api'}
    scraper = ScrapingSystem(config)
    
    # With location override for municipal accuracy
    result = await scraper.scrape_weather_data(
        url, 
        location_override={'municipality': 'Pulilan', 'region': 'Bulacan', 'country': 'Philippines'}
    )
    
    # Or save directly to generated directory
    session_id = await scraper.scrape_and_save(
        url,
        location_override={'municipality': 'Pulilan', 'region': 'Bulacan', 'country': 'Philippines'}
    )
"""

import config

class PlaywrightManager:
    def __init__(self, headless=True, slow_mo=50):
        self._playwright = None
        self._browser = None
        self.headless = headless
        self.slow_mo = slow_mo
        logger.info(f"Initializing PlaywrightManager (headless={headless}, slow_mo={slow_mo})")

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless, 
            slow_mo=self.slow_mo
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def new_page(self, user_agent=None):
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use PlaywrightManager as context manager.")
        page = await self._browser.new_page()
        
        # Set default user agent if provided
        if user_agent:
            await page.set_extra_http_headers({"User-Agent": user_agent})
            logger.debug(f"Set custom user agent: {user_agent}")
            
        # Set default viewport (larger for better visibility)
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        logger.debug("Created new browser page")
        return page

class OpenAIVisionAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        logger.info("Initialized OpenAI Vision Analyzer with modern client")

    async def analyze(self, image_data: bytes, element_type: str) -> Dict[str, Any]:
        """Analyze image data using OpenAI Vision API"""
        try:
            import base64
            
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Enhanced prompts for weather page analysis
            weather_prompts = {
                'weather_page': """
                Analyze this weather webpage screenshot and extract ALL weather information in JSON format for municipal weather reporting.
                
                Focus on CURRENT CONDITIONS and visual elements that support engaging weather storytelling.
                
                IMPORTANT: IGNORE ANY NEWS ARTICLES, WEATHER NEWS FEEDS, OR ARTICLE TIMESTAMPS. 
                Focus ONLY on the main weather data and current weather time display, NOT news article dates.
                
                Please extract:
                1. Current weather conditions (PRIMARY FOCUS):
                   - Temperature (exact value with unit) - This is the most important element
                   - Weather condition (sunny, cloudy, rainy, etc.) - Describe precisely 
                   - Wind speed and direction (if available)
                   - Humidity percentage (if available)
                   - Pressure (with unit, if available)
                   - Precipitation amount (current, if available)
                   - Visibility (if available)
                   - UV index (if available)
                   - Heat index or "feels like" temperature (if available)
                   - Current time/moment context (WEATHER TIME ONLY, not news article times)
                
                2. Visual analysis for storytelling:
                   - Dominant colors on the page (bright/sunny vs gray/cloudy themes)
                   - Weather icons present (describe the main weather symbol/icon)
                   - Overall visual mood/energy of the page layout
                   - How the page "feels" visually (bright/inviting vs dark/cautious)
                   - Temperature display prominence (large/small, color, visual emphasis)
                   - Any animated or dynamic visual elements
                
                3. Hourly forecast for TODAY (detailed):
                   - Next 12-24 hours with specific times
                   - Temperature progression through the day
                   - Condition changes throughout today
                   - When peak temperature will occur
                   - Evening/sunset conditions
                
                4. Daily forecast (brief, focus on tomorrow):
                   - Tomorrow's high/low temperatures  
                   - Tomorrow's expected conditions
                   - Next 2-3 days summary (brief)
                   - Any significant weather changes coming
                
                5. Location and timing context:
                   - City/municipality name (exact)
                   - Region/province (if available)
                   - Country
                   - Current local time and date (from WEATHER section only, ignore news timestamps)
                   - Sunrise/sunset times (if available)
                
                6. Additional atmospheric data:
                   - Any weather alerts or warnings visible
                   - Air quality information (if available)
                   - Weather maps or radar visible in the image
                   - Seasonal context or unusual conditions noted
                   - Any notable weather patterns described on page
                
                7. Municipal-relevant details (WEATHER-FOCUSED ONLY):
                   - Any references to local areas, neighborhoods, or landmarks mentioned in weather context
                   - Outdoor activity recommendations based on weather conditions
                   - Weather impact on community activities or local events
                   - Agricultural or environmental notes related to weather
                   - Any weather-specific local advisories (NO traffic or transportation data)
                
                CRITICAL: If you see multiple timestamps on the page, use ONLY the weather-related current time, 
                NOT news article publication dates. Weather time should be current/recent, not from 2023 or older years.
                
                Return ONLY a valid JSON object with this enhanced structure:
                {
                  "current": {
                    "temperature": "34°C",
                    "conditions": "Sunny", 
                    "wind": "8 kmph NE",
                    "humidity": "65%",
                    "pressure": "1009 mb",
                    "precipitation": "0.00 mm",
                    "visibility": "10 km",
                    "uv_index": "3",
                    "heat_index": "36°C",
                    "current_time": "9:39 AM"
                  },
                  "visual_analysis": {
                    "dominant_colors": ["bright yellow", "warm orange", "clear blue"],
                    "main_weather_icon": "large bright sun symbol",
                    "page_mood": "bright and inviting",
                    "visual_energy": "high energy, warm and welcoming",
                    "temperature_display": "prominently displayed, large golden text",
                    "overall_atmosphere": "sunny and optimistic layout"
                  },
                  "location": {
                    "name": "Pulilan",
                    "region": "Bulacan",
                    "country": "Philippines",
                    "local_time": "Current weather time only - ignore news dates",
                    "timezone_context": "Philippine Standard Time"
                  },
                  "today_hourly": [
                    {"time": "10:00 AM", "temperature": "35°C", "conditions": "Sunny"},
                    {"time": "11:00 AM", "temperature": "36°C", "conditions": "Sunny"},
                    {"time": "12:00 PM", "temperature": "37°C", "conditions": "Hot"}
                  ],
                  "daily_forecast": [
                    {"date": "Today", "high": "37°C", "low": "26°C", "conditions": "Sunny"},
                    {"date": "Tomorrow", "high": "36°C", "low": "25°C", "conditions": "Partly Cloudy"}
                  ],
                  "additional": {
                    "sunrise": "5:42 AM",
                    "sunset": "6:15 PM",
                    "daylight_hours": "12 hours 33 minutes",
                    "air_quality": "Good",
                    "weather_summary": "Hot and sunny conditions continue",
                    "seasonal_note": "Typical summer weather",
                    "activity_suitability": "Good for indoor activities, limit outdoor exposure",
                    "alerts": []
                  },
                  "municipal_context": {
                    "local_references": ["Pulilan Town Plaza", "Central Market area", "Residential neighborhoods"],
                    "weather_activities": ["Great for rice farming", "Perfect for outdoor markets"],
                    "health_advisories": ["Stay hydrated", "Use sun protection", "Seek shade during peak hours"],
                    "community_impact": "Hot weather may affect outdoor work and farming activities"
                  }
                }
                """.strip()
            }
            
            prompt = weather_prompts.get(element_type, weather_prompts['weather_page'])
            
            logger.info(f"Analyzing {element_type} with OpenAI Vision...")
            
            # For older OpenAI version, we need to use synchronous call in an executor
            import asyncio
            import functools
            
            def sync_openai_call():
                return self.client.chat.completions.create(
                    model="gpt-4o",  # Updated to current model that supports vision
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_b64}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )
            
            # Run the synchronous OpenAI call in a thread executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, sync_openai_call)
            
            logger.debug(f"OpenAI Vision response: {response}")
            
            # Extract the analysis content
            content = response.choices[0].message.content
            logger.info(f"OpenAI Vision analysis completed. Content length: {len(content) if content else 0}")
            
            # Try to parse as JSON, fall back to text if needed
            try:
                # Handle markdown code blocks if present
                content_clean = content.strip()
                if content_clean.startswith('```'):
                    # Extract JSON from markdown code blocks
                    lines = content_clean.split('\n')
                    json_lines = []
                    in_code_block = False
                    for line in lines:
                        if line.startswith('```'):
                            in_code_block = not in_code_block
                            continue
                        if in_code_block:
                            json_lines.append(line)
                    content_clean = '\n'.join(json_lines)
                
                weather_analysis = json.loads(content_clean)
                logger.info("Successfully parsed OpenAI Vision response as JSON")
                return {"weather_data": weather_analysis}
            except json.JSONDecodeError:
                logger.warning("OpenAI Vision response was not valid JSON, storing as text analysis")
                return {"weather_data": content}
                
        except Exception as e:
            logger.error(f"Error with OpenAI Vision analysis: {str(e)}")
            return {"error": str(e), "weather_data": None}

class VisualDataCache:
    def __init__(self, cache_dir: str, ttl: int = 3600):
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Initialized VisualDataCache with directory: {cache_dir}")

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result"""
        cache_path = self._get_cache_path(key)
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Retrieved cached data for key: {key}")
                return data
        except Exception as e:
            logger.error(f"Error reading cache for key {key}: {str(e)}")
        return None

    def store(self, key: str, result: Dict[str, Any]):
        """Store analysis result"""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(result, f)
            logger.debug(f"Stored cache data for key: {key}")
        except Exception as e:
            logger.error(f"Error storing cache for key {key}: {str(e)}")

class ScrapingSystem:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraping system with configuration"""
        self.config = config
        
        # Set OpenAI API key from config 
        openai_key = config.get('OPENAI_API_KEY')
        print(f"OpenAI API key: {openai_key}")  
        if not openai_key:
            # Try to get from project config
            try:
                import config as project_config
                openai_key = project_config.OPENAI_API_KEY
                logger.info("Using OpenAI API key from project config")
            except (ImportError, AttributeError):
                logger.warning("No OpenAI API key found in config")
        
        if openai_key:
            self.vision_analyzer = OpenAIVisionAnalyzer(openai_key)
            logger.info("Initialized OpenAI Vision Analyzer")
        else:
            self.vision_analyzer = None
            logger.warning("OpenAI Vision Analyzer not available - no API key")
        
        # Visual data cache for improved performance
        cache_dir = os.path.join(config.get('DATA_DIR', 'data'), 'weather', 'cache')
        self.visual_cache = VisualDataCache(cache_dir)
        
        logger.info("Initialized ScrapingSystem")

    async def scrape_weather_data(self, url: str, page_timeout: int = 60000, location_override: Dict[str, str] = None) -> Dict[str, Any]:
        """Main method to scrape weather data from a URL
        
        Args:
            url: Weather page URL to scrape
            page_timeout: Timeout in milliseconds
            location_override: Dict with keys 'municipality', 'region', 'country' to override extracted location
        """
        # Use config values for headless and slow_mo if provided
        headless = self.config.get('HEADLESS', False)  # Default to non-headless for debugging
        slow_mo = self.config.get('SLOW_MO', 100)  # Default slower for better site compatibility
        
        # Use non-headless mode for debugging, and add slow_mo for better site compatibility
        async with PlaywrightManager(headless=headless, slow_mo=slow_mo) as playwright:
            # Set a common user agent to avoid being blocked
            common_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            page = await playwright.new_page(user_agent=common_user_agent)
            
            try:
                # Enhanced page navigation with configurable timeout
                logger.info(f"Navigating to URL with {page_timeout}ms timeout")
                await page.goto(url, timeout=page_timeout)
                logger.info(f"Navigated to URL: {url}")
                
                # Check if this is MSN weather - handle differently
                is_msn = 'msn.com' in url.lower()
                if is_msn:
                    logger.info("Detected MSN weather page - using MSN-specific handling")
                    # For MSN, don't wait for network idle - just wait for content to load
                    await page.wait_for_load_state('domcontentloaded', timeout=15000)
                    logger.info("MSN page DOM content loaded")
                    
                    # Wait for weather content to appear
                    try:
                        await page.wait_for_selector('[data-module="WeatherCurrentConditions"], .weather-card, .current-weather', timeout=10000)
                        logger.info("MSN weather content detected")
                    except:
                        logger.info("MSN weather selectors not found, proceeding anyway")
                    
                    # Give additional time for MSN's dynamic content
                    await asyncio.sleep(5)
                    
                else:
                    # Original handling for other sites
                    # Wait for the page to load more content
                    await page.wait_for_load_state('networkidle', timeout=page_timeout)
                    logger.debug("Page reached network idle state")
                
                # Check if we got redirected or are on the wrong page
                current_url = page.url
                logger.info(f"Current URL after navigation: {current_url}")
                
                # Check for and handle cookie consent dialogs (common on weather sites)
                await self._handle_cookie_dialogs(page)
                
                # For WorldWeatherOnline, check if we need to search for the specific location
                if not is_msn:
                    await self._ensure_correct_weather_page(page, url)
                
                # Wait a bit more for dynamic content to load
                await asyncio.sleep(3)
                
                # Scroll down to ensure all dynamic content loads
                logger.debug("Scrolling page to load all content")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                await page.evaluate("window.scrollTo(0, 0)")  # Back to top
                await asyncio.sleep(3)

                # PRIMARY METHOD: Use OpenAI Vision with full page screenshot
                logger.info("Using OpenAI Vision as primary extraction method...")
                visual_data = await self._extract_with_vision(page)
                
                # ENHANCED HOURLY DATA EXTRACTION: Extract detailed hourly data from tabs (MSN specific)
                hourly_data = {}
                if is_msn:
                    logger.info("Extracting enhanced hourly data from MSN tabs...")
                    try:
                        hourly_data = await self._extract_hourly_data_from_tabs(page)
                        logger.info(f"Successfully extracted hourly data from {len(hourly_data)} tabs")
                    except Exception as hourly_error:
                        logger.error(f"Error extracting hourly data: {str(hourly_error)}")
                        hourly_data = {}
                
                # FALLBACK METHOD: DOM-based extraction if vision fails
                text_data = {}
                if not visual_data or not visual_data.get('weather_data'):
                    logger.info("Vision extraction failed or incomplete, falling back to DOM extraction...")
                    text_data = await self._extract_text_data_fallback(page)
                else:
                    logger.info("Vision extraction successful, using vision data as primary source")
                    # Convert vision data to text_data format for compatibility
                    text_data = self._convert_vision_to_text_data(visual_data, location_override)

                # Combine and validate data
                result = self._aggregate_data(text_data, visual_data)
                
                # Integrate hourly data into the result
                if hourly_data:
                    result['enhanced_hourly_data'] = hourly_data
                    logger.info("Integrated enhanced hourly data into result")
                
                logger.info("Successfully aggregated weather data")

                return result
            except Exception as e:
                logger.error(f"Error scraping weather data: {str(e)}")
                
                # Try to capture screenshot for debugging
                try:
                    screenshots_dir = os.path.join(self.config['DATA_DIR'], 'debug')
                    os.makedirs(screenshots_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(screenshots_dir, f"error_{timestamp}.png")
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"Saved error screenshot to {screenshot_path}")
                except Exception as screenshot_error:
                    logger.warning(f"Failed to save error screenshot: {str(screenshot_error)}")
                
                raise

    async def _handle_cookie_dialogs(self, page) -> None:
        """Handle cookie consent dialogs that might appear on weather sites"""
        try:
            logger.info("Checking for cookie consent dialogs...")
            
            # First check for WorldWeatherOnline specific consent dialogs
            wwo_consent_selectors = [
                "#onetrust-accept-btn-handler",  # Common OnetrustLLC cookie button
                ".accept-all-cookies",  # WorldWeatherOnline specific
                "#qc-cmp2-ui button[mode='primary']",  # CMP v2 accept button
                "button:has-text('Accept all cookies')",
                "button:has-text('Accept All')",
                "button:has-text('Accept All Cookies')",
                "div.qc-cmp2-summary-buttons button[mode='primary']"
            ]
            
            # Try WorldWeatherOnline specific selectors first with extra wait
            for selector in wwo_consent_selectors:
                try:
                    logger.debug(f"Checking for cookie dialog selector: {selector}")
                    if await page.locator(selector).count() > 0:
                        logger.info(f"Found cookie consent dialog with selector: {selector}")
                        await asyncio.sleep(1)  # Wait a bit for dialog to be fully interactive
                        await page.locator(selector).click()
                        logger.info("Clicked cookie consent button")
                        await asyncio.sleep(2)  # Wait for dialog to disappear
                        return
                except Exception as e:
                    logger.debug(f"Failed to interact with selector {selector}: {str(e)}")
            
            # Common selectors for cookie consent buttons/dialogs
            consent_selectors = [
                'button:has-text("Accept")', 
                'button:has-text("Agree")',
                'button:has-text("I Agree")',
                'button:has-text("OK")',
                'button:has-text("Continue")',
                'div.cookieConsent button',
                'div.cookie-consent button',
                'div[id*="cookie"] button',
                'div[class*="cookie"] button',
                '[id*="cookie"] button',
                '[class*="cookie"] button',
                '[id*="consent"] button',
                '[class*="consent"] button',
                'div#cookies-policy-alert button.btn-cookies-policy',
                'div.gdpr-module button',
                'div.privacy-alert button',
                '.cookieMessage .button',
                '#cookie-banner .accept-button',
                '.cookie-notice-container #cn-accept-cookie'
            ]
            
            # Try each selector and click if found
            for selector in consent_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        logger.info(f"Found cookie consent dialog with selector: {selector}")
                        await page.locator(selector).click()
                        logger.info("Clicked cookie consent button")
                        await asyncio.sleep(1)  # Wait for dialog to disappear
                        return
                except Exception as e:
                    logger.debug(f"Failed to interact with selector {selector}: {str(e)}")
                        
            # If no button was found or clicked, try to click on page body to dismiss overlay
            try:
                # Check if there's any overlay with z-index that might be a cookie dialog
                has_overlay = await page.evaluate("""
                    () => {
                        const overlays = document.querySelectorAll('div[id*="cookie"], div[class*="cookie"]');
                        return overlays.length > 0;
                    }
                """)
                
                if has_overlay:
                    logger.info("Found cookie overlay, trying to dismiss it by clicking on page body")
                    await page.evaluate("""
                        () => {
                            document.body.click();
                        }
                    """)
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Failed to dismiss cookie overlay: {str(e)}")
                
            logger.info("Finished handling cookie dialogs")
            
        except Exception as e:
            logger.error(f"Error handling cookie dialogs: {str(e)}")
            # Continue execution even if cookie handling fails

    async def _ensure_correct_weather_page(self, page, original_url: str) -> None:
        """Ensure we're on the correct weather page, handle redirects and searches if needed"""
        try:
            current_url = page.url
            logger.info(f"Checking if we're on the correct weather page. Current: {current_url}")
            
            # Check if we're on a search or general page instead of specific weather page
            page_title = await page.title()
            page_content = await page.content()
            
            logger.info(f"Page title: {page_title}")
            
            # Check if we're on a search page or general location page
            is_search_page = any(indicator in page_content.lower() for indicator in [
                "search for a city", 
                "search for a location", 
                "major cities and towns",
                "holiday weather"
            ])
            
            # Check if we have actual weather data
            has_weather_data = any(indicator in page_content.lower() for indicator in [
                "°c", "°f", "temperature", "sunny", "cloudy", "rain", "wind:", "pressure:"
            ])
            
            if is_search_page and not has_weather_data:
                logger.warning("Detected search/general page instead of specific weather page")
                
                # Try to search for the specific location
                if 'worldweatheronline.com' in current_url:
                    await self._search_worldweatheronline_location(page, original_url)
                else:
                    logger.warning("Unknown weather site, cannot auto-navigate to specific location")
            else:
                logger.info("Appears to be on a specific weather page")
                
        except Exception as e:
            logger.warning(f"Error checking page type: {str(e)}")
            # Continue anyway, might still be able to extract data

    async def _search_worldweatheronline_location(self, page, original_url: str) -> None:
        """Search for specific location on WorldWeatherOnline"""
        try:
            # Extract location from URL
            location_match = None
            import re
            url_parts = original_url.split('/')
            for part in url_parts:
                if '-weather' in part:
                    location_match = part.replace('-weather', '').replace('-', ' ')
                    break
            
            if not location_match:
                logger.warning("Could not extract location from URL for search")
                return
                
            logger.info(f"Attempting to search for location: {location_match}")
            
            # Look for search box
            search_selectors = [
                'input[placeholder*="city"]',
                'input[placeholder*="location"]', 
                'input[type="text"]',
                '.search input',
                '#search input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        search_input = page.locator(selector).first
                        logger.info(f"Found search input with selector: {selector}")
                        break
                except:
                    continue
                    
            if search_input:
                # Clear and type location
                await search_input.clear()
                await search_input.fill(location_match)
                await asyncio.sleep(1)
                
                # Look for search button
                search_button_selectors = [
                    'button:has-text("Search")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                    '.search button',
                    '#search button'
                ]
                
                search_button = None
                for selector in search_button_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            search_button = page.locator(selector).first
                            logger.info(f"Found search button with selector: {selector}")
                            break
                    except:
                        continue
                
                if search_button:
                    await search_button.click()
                    logger.info("Clicked search button")
                    
                    # Wait for results
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    await asyncio.sleep(3)
                    
                    # Check if we have results and try to click the first result
                    result_selectors = [
                        'a[href*="weather"]',
                        '.search-result a',
                        '.result a'
                    ]
                    
                    for selector in result_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                first_result = page.locator(selector).first
                                href = await first_result.get_attribute('href')
                                if href and location_match.lower() in href.lower():
                                    logger.info(f"Clicking on search result: {href}")
                                    await first_result.click()
                                    await page.wait_for_load_state('networkidle', timeout=10000)
                                    await asyncio.sleep(3)
                                    break
                        except Exception as e:
                            logger.debug(f"Error clicking search result: {str(e)}")
                            continue
                else:
                    # Try pressing Enter if no button found
                    await search_input.press('Enter')
                    logger.info("Pressed Enter to search")
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    await asyncio.sleep(3)
            else:
                logger.warning("Could not find search input on page")
                
        except Exception as e:
            logger.warning(f"Error searching for location: {str(e)}")
            # Continue anyway

    async def _hide_msn_news_feeds(self, page) -> None:
        """Hide MSN news feeds and weather news sections that contain old timestamps"""
        try:
            logger.info("Hiding MSN news feeds and weather news sections...")
            
            # CSS to hide various news and feed sections that contain old timestamps
            hide_news_css = """
                /* Hide weather news feed */
                [data-module*="WeatherNews"],
                [data-module*="NewsRecommendations"],
                [data-module*="WeatherFeed"],
                .weather-news,
                .news-feed,
                
                /* Hide news carousel and articles */
                [data-module*="NewsCarousel"],
                [data-module*="NewsFeedCarousel"],
                .news-carousel,
                .article-carousel,
                
                /* Hide specific MSN news sections */
                div[data-t*="news"],
                div[data-t*="article"],
                section[aria-label*="news"],
                section[aria-label*="article"],
                
                /* Hide bottom news/article sections */
                .news-section,
                .article-section,
                .trending-news,
                .related-articles,
                
                /* Hide MSN-specific feed components */
                cs-weather-news,
                cs-news-feed,
                weather-feed-wc,
                
                /* Hide any elements with news-related classes */
                [class*="news"]:not([class*="weather"]),
                [class*="article"]:not([class*="weather"]),
                [class*="feed"]:not([class*="weather"]):not([class*="forecast"]),
                
                /* Hide timestamp containers that aren't weather-related */
                .timestamp:not(.weather-timestamp),
                .date-time:not(.weather-time),
                .published-date,
                .article-date,
                
                /* Hide bottom sections with news content */
                .bottom-content,
                .below-fold,
                .secondary-content
                {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    height: 0 !important;
                    overflow: hidden !important;
                }
                
                /* Ensure weather-specific content remains visible */
                [data-module*="Weather"]:not([data-module*="WeatherNews"]),
                [data-module*="Forecast"],
                .weather-card,
                .forecast-card,
                .current-weather,
                .weather-conditions,
                .temperature,
                .weather-details
                {
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                }
            """
            
            # Apply the CSS to hide news sections
            await page.add_style_tag(content=hide_news_css)
            
            # Also try to remove news elements via JavaScript
            await page.evaluate("""
                () => {
                    // Remove elements that likely contain news with old timestamps
                    const newsSelectors = [
                        '[data-module*="WeatherNews"]',
                        '[data-module*="NewsRecommendations"]', 
                        '[data-module*="WeatherFeed"]',
                        '[data-module*="NewsCarousel"]',
                        'div[data-t*="news"]',
                        'div[data-t*="article"]',
                        '.news-section',
                        '.article-section',
                        '.trending-news',
                        '.related-articles',
                        'cs-weather-news',
                        'cs-news-feed',
                        'weather-feed-wc'
                    ];
                    
                    newsSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => el.remove());
                    });
                    
                    // Remove any elements containing old dates (heuristic approach)
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach(el => {
                        const text = el.textContent || '';
                        // Look for date patterns that are clearly old (2023, 2022, etc)
                        if (text.match(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(2023|2022|2021)\b/i)) {
                            // Don't remove if it's part of weather data
                            if (!el.closest('[data-module*="Weather"]') && 
                                !el.closest('.weather-card') && 
                                !el.closest('.forecast-card')) {
                                el.style.display = 'none';
                            }
                        }
                    });
                }
            """)
            
            logger.info("Successfully hidden MSN news feeds and weather news sections")
            
        except Exception as e:
            logger.error(f"Error hiding MSN news feeds: {str(e)}")
            # Continue execution even if hiding fails

    async def _extract_with_vision(self, page) -> Dict[str, Any]:
        """Extract weather data using OpenAI Vision with full page screenshot"""
        try:
            logger.info("Capturing full page screenshot for vision analysis...")
            
            # For MSN pages, hide news feeds before taking screenshot
            page_url = page.url
            if page_url and 'msn.com' in page_url.lower():
                await self._hide_msn_news_feeds(page)
                # Wait a moment for the hiding to take effect
                await asyncio.sleep(1)
            
            # Capture full page screenshot
            full_page_screenshot = await page.screenshot(full_page=True)
            logger.info(f"Captured screenshot ({len(full_page_screenshot)} bytes)")
            
            # Generate cache key
            screenshot_hash = hashlib.sha256(full_page_screenshot).hexdigest()
            
            # Check cache first
            cached_result = self.visual_cache.get(screenshot_hash)
            if cached_result:
                logger.info("Using cached vision analysis")
                return cached_result
            
            # Analyze with OpenAI Vision
            logger.info("Sending screenshot to OpenAI Vision for analysis...")
            analysis_result = await self.vision_analyzer.analyze(full_page_screenshot, 'weather_page')
            
            # Cache the result
            self.visual_cache.store(screenshot_hash, analysis_result)
            
            logger.info("OpenAI Vision analysis completed successfully")
            return {'weather_data': analysis_result, 'screenshot_hash': screenshot_hash}
            
        except Exception as e:
            logger.error(f"Error in vision extraction: {str(e)}")
            return {}

    async def _extract_hourly_data_from_tabs(self, page) -> Dict[str, Any]:
        """Extract hourly data by clicking through different forecast tabs"""
        try:
            logger.info("Starting enhanced hourly data extraction from tabs")
            
            hourly_data = {
                'overview': {},
                'precipitation': {},
                'wind': {},
                'air_quality': {},
                'humidity': {},
                'cloud_cover': {}
            }
            
            # Define tab selectors and their corresponding data types
            tabs_to_extract = [
                {
                    'name': 'overview',
                    'selector': 'button[data-forecasttype="forecastButton_overview"]',
                    'data_type': 'temperature_overview'
                },
                {
                    'name': 'precipitation',
                    'selector': 'button[data-forecasttype="forecastButton_precipitation"]',
                    'data_type': 'precipitation_hourly'
                },
                {
                    'name': 'wind',
                    'selector': 'button[data-forecasttype="forecastButton_wind"]',
                    'data_type': 'wind_hourly'
                },
                {
                    'name': 'air_quality',
                    'selector': 'button[data-forecasttype="forecastButton_airquality"]',
                    'data_type': 'aqi_hourly'
                },
                {
                    'name': 'humidity',
                    'selector': 'button[data-forecasttype="forecastButton_humidity"]',
                    'data_type': 'humidity_hourly'
                },
                {
                    'name': 'cloud_cover',
                    'selector': 'button[data-forecasttype="forecastButton_cloudcover"]',
                    'data_type': 'cloud_hourly'
                }
            ]
            
            for tab_info in tabs_to_extract:
                try:
                    logger.info(f"Extracting data from {tab_info['name']} tab")
                    
                    # Click the tab button
                    tab_button = await page.wait_for_selector(tab_info['selector'], timeout=5000)
                    if tab_button:
                        await tab_button.click()
                        logger.info(f"Clicked {tab_info['name']} tab")
                        
                        # Wait for content to load
                        await page.wait_for_timeout(2000)
                        
                        # Extract hourly data from the chart/content
                        tab_data = await self._extract_tab_specific_data(page, tab_info['name'])
                        hourly_data[tab_info['name']] = tab_data
                        
                        logger.info(f"Extracted {len(tab_data)} data points from {tab_info['name']} tab")
                    else:
                        logger.warning(f"Could not find {tab_info['name']} tab button")
                        
                except Exception as tab_error:
                    logger.error(f"Error extracting {tab_info['name']} tab data: {str(tab_error)}")
                    continue
            
            logger.info(f"Completed hourly data extraction from {len(hourly_data)} tabs")
            return hourly_data
            
        except Exception as e:
            logger.error(f"Error in hourly data extraction: {str(e)}")
            return {}

    async def _extract_tab_specific_data(self, page, tab_name: str) -> Dict[str, Any]:
        """Extract specific data based on the active tab"""
        try:
            tab_data = {}
            
            if tab_name == 'wind':
                # Extract wind speed and gust data from SVG chart
                wind_data = await self._extract_wind_chart_data(page)
                tab_data.update(wind_data)
                
            elif tab_name == 'precipitation':
                # Extract precipitation data
                precip_data = await self._extract_precipitation_chart_data(page)
                tab_data.update(precip_data)
                
            elif tab_name == 'humidity':
                # Extract humidity data
                humidity_data = await self._extract_humidity_chart_data(page)
                tab_data.update(humidity_data)
                
            elif tab_name == 'air_quality':
                # Extract air quality data
                aqi_data = await self._extract_aqi_chart_data(page)
                tab_data.update(aqi_data)
                
            elif tab_name == 'cloud_cover':
                # Extract cloud cover data
                cloud_data = await self._extract_cloud_chart_data(page)
                tab_data.update(cloud_data)
                
            elif tab_name == 'overview':
                # Extract temperature overview data
                temp_data = await self._extract_temperature_chart_data(page)
                tab_data.update(temp_data)
            
            # Also extract time labels for all tabs
            time_labels = await self._extract_time_labels(page)
            if time_labels:
                tab_data['time_labels'] = time_labels
            
            return tab_data
            
        except Exception as e:
            logger.error(f"Error extracting {tab_name} specific data: {str(e)}")
            return {}

    async def _extract_wind_chart_data(self, page) -> Dict[str, Any]:
        """Extract wind speed and gust data from the wind chart"""
        try:
            wind_data = {}
            
            # Extract wind speed values from chart elements
            wind_speeds = await page.evaluate("""
                () => {
                    const windElements = document.querySelectorAll('.hiValue-DS-EntryPoint1-1 span:first-child');
                    return Array.from(windElements).map(el => parseInt(el.textContent) || 0);
                }
            """)
            
            # Extract wind gust values
            wind_gusts = await page.evaluate("""
                () => {
                    const gustElements = document.querySelectorAll('.barLevel-DS-EntryPoint1-1');
                    return Array.from(gustElements).map(el => {
                        const match = el.textContent.match(/Gusts: (\\d+)km\\/h/);
                        return match ? parseInt(match[1]) : 0;
                    });
                }
            """)
            
            if wind_speeds:
                wind_data['hourly_wind_speed'] = wind_speeds
                logger.info(f"Extracted {len(wind_speeds)} wind speed values")
            
            if wind_gusts:
                wind_data['hourly_wind_gusts'] = wind_gusts
                logger.info(f"Extracted {len(wind_gusts)} wind gust values")
            
            return wind_data
            
        except Exception as e:
            logger.error(f"Error extracting wind chart data: {str(e)}")
            return {}

    async def _extract_precipitation_chart_data(self, page) -> Dict[str, Any]:
        """Extract precipitation data from the precipitation chart"""
        try:
            precip_data = {}
            
            # Extract precipitation values
            precipitation_values = await page.evaluate("""
                () => {
                    // Look for precipitation values in various possible selectors
                    const selectors = [
                        '.hiValue-DS-EntryPoint1-1 span:first-child',
                        '.valueNumSection-DS-EntryPoint1-1 .hiValue-DS-EntryPoint1-1',
                        '[data-testid="precipitation-value"]'
                    ];
                    
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            return Array.from(elements).map(el => {
                                const text = el.textContent;
                                const match = text.match(/(\\d+(?:\\.\\d+)?)/);
                                return match ? parseFloat(match[1]) : 0;
                            });
                        }
                    }
                    return [];
                }
            """)
            
            if precipitation_values:
                precip_data['hourly_precipitation'] = precipitation_values
                logger.info(f"Extracted {len(precipitation_values)} precipitation values")
            
            return precip_data
            
        except Exception as e:
            logger.error(f"Error extracting precipitation chart data: {str(e)}")
            return {}

    async def _extract_humidity_chart_data(self, page) -> Dict[str, Any]:
        """Extract humidity data from the humidity chart"""
        try:
            humidity_data = {}
            
            # Extract humidity percentage values
            humidity_values = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('.hiValue-DS-EntryPoint1-1 span:first-child');
                    return Array.from(elements).map(el => {
                        const text = el.textContent;
                        const match = text.match(/(\\d+)%?/);
                        return match ? parseInt(match[1]) : 0;
                    });
                }
            """)
            
            if humidity_values:
                humidity_data['hourly_humidity'] = humidity_values
                logger.info(f"Extracted {len(humidity_values)} humidity values")
            
            return humidity_data
            
        except Exception as e:
            logger.error(f"Error extracting humidity chart data: {str(e)}")
            return {}

    async def _extract_aqi_chart_data(self, page) -> Dict[str, Any]:
        """Extract air quality index data from the AQI chart"""
        try:
            aqi_data = {}
            
            # Extract AQI values
            aqi_values = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('.hiValue-DS-EntryPoint1-1 span:first-child');
                    return Array.from(elements).map(el => {
                        const text = el.textContent;
                        const match = text.match(/(\\d+)/);
                        return match ? parseInt(match[1]) : 0;
                    });
                }
            """)
            
            if aqi_values:
                aqi_data['hourly_aqi'] = aqi_values
                logger.info(f"Extracted {len(aqi_values)} AQI values")
            
            return aqi_data
            
        except Exception as e:
            logger.error(f"Error extracting AQI chart data: {str(e)}")
            return {}

    async def _extract_cloud_chart_data(self, page) -> Dict[str, Any]:
        """Extract cloud cover data from the cloud cover chart"""
        try:
            cloud_data = {}
            
            # Extract cloud cover percentage values
            cloud_values = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('.hiValue-DS-EntryPoint1-1 span:first-child');
                    return Array.from(elements).map(el => {
                        const text = el.textContent;
                        const match = text.match(/(\\d+)%?/);
                        return match ? parseInt(match[1]) : 0;
                    });
                }
            """)
            
            if cloud_values:
                cloud_data['hourly_cloud_cover'] = cloud_values
                logger.info(f"Extracted {len(cloud_values)} cloud cover values")
            
            return cloud_data
            
        except Exception as e:
            logger.error(f"Error extracting cloud cover chart data: {str(e)}")
            return {}

    async def _extract_temperature_chart_data(self, page) -> Dict[str, Any]:
        """Extract temperature data from the overview/temperature chart"""
        try:
            temp_data = {}
            
            # Extract temperature values
            temp_values = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('.hiValue-DS-EntryPoint1-1 span:first-child');
                    return Array.from(elements).map(el => {
                        const text = el.textContent;
                        const match = text.match(/(\\d+)/);
                        return match ? parseInt(match[1]) : 0;
                    });
                }
            """)
            
            if temp_values:
                temp_data['hourly_temperature'] = temp_values
                logger.info(f"Extracted {len(temp_values)} temperature values")
            
            return temp_data
            
        except Exception as e:
            logger.error(f"Error extracting temperature chart data: {str(e)}")
            return {}

    async def _extract_time_labels(self, page) -> List[str]:
        """Extract time labels from the chart x-axis"""
        try:
            time_labels = await page.evaluate("""
                () => {
                    const timeElements = document.querySelectorAll('.hourLabel-DS-EntryPoint1-1');
                    return Array.from(timeElements).map(el => el.textContent.trim());
                }
            """)
            
            if time_labels:
                logger.info(f"Extracted {len(time_labels)} time labels")
                return time_labels
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting time labels: {str(e)}")
            return []

    def _convert_vision_to_text_data(self, visual_data: Dict[str, Any], location_override: Dict[str, str] = None) -> Dict[str, Any]:
        """Convert OpenAI Vision analysis to text_data format for compatibility"""
        try:
            weather_data = visual_data.get('weather_data', {})
            
            # Handle the new enhanced structured JSON format from OpenAI Vision
            if isinstance(weather_data, dict):
                
                # Handle nested structure where data might be in weather_data.weather_data
                if 'weather_data' in weather_data and isinstance(weather_data['weather_data'], dict):
                    weather_data = weather_data['weather_data']
                
                # Extract from enhanced structured format
                current = weather_data.get('current', {})
                location = weather_data.get('location', {})
                visual_analysis = weather_data.get('visual_analysis', {})
                today_hourly = weather_data.get('today_hourly', [])
                daily_forecast = weather_data.get('daily_forecast', [])
                additional = weather_data.get('additional', {})
                municipal_context = weather_data.get('municipal_context', {})
                
                # Apply location override if provided (especially useful for MSN)
                if location_override:
                    logger.info(f"Applying location override: {location_override}")
                    location_name = location_override.get('municipality', location.get('name', 'Unknown'))
                    location_region = location_override.get('region', location.get('region', 'Unknown'))
                    location_country = location_override.get('country', location.get('country', 'Unknown'))
                else:
                    location_name = location.get('name', weather_data.get('location', 'Unknown'))
                    location_region = location.get('region', 'Unknown')
                    location_country = location.get('country', 'Unknown')
                
                # Override local_time with current computer date/time to avoid old news timestamps
                current_datetime = datetime.now()
                current_date_str = current_datetime.strftime("%A, %B %d, %Y %I:%M %p")
                
                # Extract only the time portion from vision if available, but use current date
                extracted_time = current.get('current_time', 'Unknown')
                if extracted_time and extracted_time != 'Unknown':
                    # Try to extract just the time part (like "2:00 PM") and combine with current date
                    import re
                    time_match = re.search(r'(\d{1,2}:\d{2}\s*[APap][Mm])', str(extracted_time))
                    if time_match:
                        time_only = time_match.group(1)
                        current_date_only = current_datetime.strftime("%A, %B %d, %Y")
                        current_date_str = f"{current_date_only} {time_only}"
                        logger.info(f"Using current date with extracted time: {current_date_str}")
                    else:
                        logger.info(f"Using full current datetime: {current_date_str}")
                else:
                    logger.info(f"No valid time extracted, using current datetime: {current_date_str}")
                
                # Also override the location.local_time if it contains old dates
                location_time = location.get('local_time', 'Unknown')
                if location_time and isinstance(location_time, str):
                    # Check if the extracted date contains old years (2023, 2022, 2021)
                    if re.search(r'\b(2023|2022|2021|2020)\b', location_time):
                        logger.warning(f"Detected old date in extracted location time: {location_time}")
                        logger.info(f"Overriding with current date: {current_date_str}")
                        location_time = current_date_str
                    else:
                        # If it looks current, keep it but log it
                        logger.info(f"Extracted location time appears current: {location_time}")
                else:
                    location_time = current_date_str
                
                # Build enhanced forecast summary from daily forecast
                forecast_summary = "Unknown"
                if daily_forecast:
                    forecast_parts = []
                    for day in daily_forecast[:3]:  # Take first 3 days for summary
                        date = day.get('date', 'Unknown')
                        high = day.get('high', 'Unknown')
                        low = day.get('low', 'Unknown') 
                        conditions = day.get('conditions', 'Unknown')
                        forecast_parts.append(f"{date}: {high}/{low}, {conditions}")
                    forecast_summary = " | ".join(forecast_parts)
                
                # Build today's hourly summary
                hourly_summary = "Unknown"
                if today_hourly:
                    hourly_parts = []
                    for hour in today_hourly[:5]:  # Take first 5 hours
                        time = hour.get('time', 'Unknown')
                        temp = hour.get('temperature', 'Unknown')
                        conditions = hour.get('conditions', 'Unknown')
                        hourly_parts.append(f"{time}: {temp}, {conditions}")
                    hourly_summary = " | ".join(hourly_parts)
                
                # Return in the enhanced text_data format with all new fields
                result = {
                    # Core current conditions
                    'temperature': current.get('temperature', weather_data.get('temperature', 'Unknown')),
                    'conditions': current.get('conditions', weather_data.get('conditions', 'Unknown')),
                    'wind': current.get('wind', weather_data.get('wind', 'Unknown')),
                    'pressure': current.get('pressure', weather_data.get('pressure', 'Unknown')),
                    'humidity': current.get('humidity', weather_data.get('humidity', 'Unknown')),
                    'precipitation': current.get('precipitation', weather_data.get('precipitation', 'Unknown')),
                    'uv_index': current.get('uv_index', weather_data.get('uv_index', 'Unknown')),
                    'visibility': current.get('visibility', weather_data.get('visibility', 'Unknown')),
                    'heat_index': current.get('heat_index', 'Unknown'),
                    'current_time': current.get('current_time', 'Unknown'),
                    
                    # Location context (use override if provided)
                    'location': location_name,
                    'region': location_region,
                    'country': location_country,
                    'local_time': location_time,
                    'timezone_context': location.get('timezone_context', 'Unknown'),
                    
                    # Forecast summaries
                    'forecast': forecast_summary,
                    'hourly_summary': hourly_summary,
                    'today_hourly': today_hourly,
                    'daily_forecast': daily_forecast,
                    
                    # Enhanced atmospheric data
                    'sunrise': additional.get('sunrise', 'Unknown'),
                    'sunset': additional.get('sunset', 'Unknown'),
                    'daylight_hours': additional.get('daylight_hours', 'Unknown'),
                    'air_quality': additional.get('air_quality', 'Unknown'),
                    'weather_summary': additional.get('weather_summary', 'Unknown'),
                    'seasonal_note': additional.get('seasonal_note', 'Unknown'),
                    'activity_suitability': additional.get('activity_suitability', 'Unknown'),
                    'alerts': additional.get('alerts', []),
                    
                    # Visual analysis for storytelling
                    'visual_analysis': {
                        'dominant_colors': visual_analysis.get('dominant_colors', []),
                        'main_weather_icon': visual_analysis.get('main_weather_icon', 'Unknown'),
                        'page_mood': visual_analysis.get('page_mood', 'Unknown'),
                        'visual_energy': visual_analysis.get('visual_energy', 'Unknown'),
                        'temperature_display': visual_analysis.get('temperature_display', 'Unknown'),
                        'overall_atmosphere': visual_analysis.get('overall_atmosphere', 'Unknown')
                    },
                    
                    # Municipal context for local reporting
                    'municipal_context': {
                        "local_references": municipal_context.get("local_references", []),
                        "weather_activities": municipal_context.get("weather_activities", []),
                        "health_advisories": municipal_context.get("health_advisories", []),
                        "community_impact": municipal_context.get("community_impact", "Unknown")
                    },
                    
                    # Processing metadata
                    'vision_extracted': True,
                    'data_richness': 'enhanced',  # Flag to indicate enhanced data structure
                    'location_overridden': location_override is not None
                }
                
                logger.info(f"Enhanced vision data conversion: temp={result['temperature']}, conditions={result['conditions']}, location={result['location']}, visual_mood={result['visual_analysis']['page_mood']}")
                return result
                
            elif isinstance(weather_data, str):
                # If OpenAI returns text, try to parse it or store as raw
                logger.warning("OpenAI Vision returned text instead of JSON structure")
                return {
                    'raw_analysis': weather_data, 
                    'temperature': 'Unknown', 
                    'conditions': 'Unknown', 
                    'forecast': 'Unknown',
                    'vision_extracted': True,
                    'data_richness': 'text_only',
                    'location_overridden': location_override is not None
                }
            else:
                logger.warning("OpenAI Vision returned unexpected format")
                return {
                    'temperature': 'Unknown', 
                    'conditions': 'Unknown', 
                    'forecast': 'Unknown',
                    'vision_extracted': False,
                    'data_richness': 'failed',
                    'location_overridden': location_override is not None
                }
                
        except Exception as e:
            logger.error(f"Error converting enhanced vision data: {str(e)}")
            return {
                'temperature': 'Unknown', 
                'conditions': 'Unknown', 
                'forecast': 'Unknown',
                'vision_extracted': False,
                'data_richness': 'error',
                'error': str(e),
                'location_overridden': location_override is not None
            }

    async def _extract_text_data_fallback(self, page) -> Dict[str, Any]:
        """Extract text-based weather data as fallback method"""
        try:
            # Check if this is WorldWeatherOnline for any location
            is_wwo = False
            try:
                url = page.url
                if 'worldweatheronline.com' in url:
                    is_wwo = True
                    logger.info("Detected WorldWeatherOnline page, using specific selectors")
            except:
                pass
            
            # Initialize default values
            temperature = "Unknown"
            conditions = "Unknown"
            forecast = "Unknown"
            additional_data = {}
                
            if is_wwo:
                # Enhanced selectors for WorldWeatherOnline
                try:
                    # Try to get the main temperature display (large temperature number)
                    temp_selectors = [
                        'text:contains("°C")',  # Direct text search
                        'text:contains("°c")',
                        '.temp',
                        '.temperature',
                        'h1:has-text("°")',
                        'h2:has-text("°")',
                        'div:has-text("°C")',
                        'span:has-text("°C")'
                    ]
                    
                    for selector in temp_selectors:
                        try:
                            elements = await page.locator(selector).all()
                            if elements:
                                for element in elements[:3]:  # Check first 3 matches
                                    text = await element.inner_text()
                                    if text and ('°' in text):
                                        # Extract just the temperature part
                                        import re
                                        temp_match = re.search(r'(\d+)\s*[°℃]\s*[CF]?', text, re.IGNORECASE)
                                        if temp_match:
                                            temperature = f"{temp_match.group(1)}°C"
                                            logger.debug(f"Found temperature: {temperature} using selector: {selector}")
                                            break
                                if temperature != "Unknown":
                                    break
                        except Exception as e:
                            logger.debug(f"Temperature selector {selector} failed: {str(e)}")
                            continue
                    
                    # Try to get weather conditions (Sunny, Cloudy, etc.)
                    condition_selectors = [
                        'text:contains("Sunny")',
                        'text:contains("Cloudy")', 
                        'text:contains("Rain")',
                        'text:contains("Clear")',
                        'text:contains("Partly")',
                        '.weather-condition',
                        '.condition'
                    ]
                    
                    # Also look for common weather condition words in the page
                    page_text = await page.inner_text('body')
                    weather_words = ['sunny', 'cloudy', 'partly cloudy', 'rain', 'clear', 'overcast', 'fog', 'storm']
                    for word in weather_words:
                        if word in page_text.lower():
                            conditions = word.title()
                            logger.debug(f"Found condition: {conditions} in page text")
                            break
                    
                    # Try specific selectors if general text search didn't work
                    if conditions == "Unknown":
                        for selector in condition_selectors:
                            try:
                                elements = await page.locator(selector).all()
                                if elements:
                                    conditions = await elements[0].inner_text()
                                    if conditions and len(conditions.strip()) > 0:
                                        logger.debug(f"Found conditions: {conditions} using selector: {selector}")
                                        break
                            except Exception as e:
                                logger.debug(f"Condition selector {selector} failed: {str(e)}")
                                continue
                    
                    # Try to get additional weather data (wind, pressure, etc.)
                    try:
                        wind_text = await page.locator('text:contains("Wind:")').first.inner_text()
                        if wind_text:
                            additional_data['wind'] = wind_text.strip()
                    except:
                        pass
                        
                    try:
                        pressure_text = await page.locator('text:contains("Pressure:")').first.inner_text()
                        if pressure_text:
                            additional_data['pressure'] = pressure_text.strip()
                    except:
                        pass
                        
                    try:
                        precip_text = await page.locator('text:contains("Precip:")').first.inner_text()
                        if precip_text:
                            additional_data['precipitation'] = precip_text.strip()
                    except:
                        pass
                    
                    # Try to get forecast data from the weekly forecast section
                    try:
                        forecast_elements = await page.locator('div:has-text("SAT") >> ..').all()
                        if forecast_elements:
                            forecast_data = []
                            for element in forecast_elements[:5]:  # Get first 5 days
                                day_text = await element.inner_text()
                                if day_text and len(day_text.strip()) > 0:
                                    forecast_data.append(day_text.strip())
                            if forecast_data:
                                forecast = " | ".join(forecast_data)
                    except Exception as e:
                        logger.debug(f"Error extracting forecast: {str(e)}")
                    
                    logger.debug(f"WorldWeatherOnline extraction completed: temp={temperature}, conditions={conditions}")
                    
                except Exception as e:
                    logger.debug(f"Error in WorldWeatherOnline-specific extraction: {str(e)}")
                    # Fall back to generic extraction
            
            # Generic extraction for other sites or as fallback
            if temperature == "Unknown" or conditions == "Unknown":
                logger.info("Using generic extraction methods")
                
                # Generic temperature selectors
                generic_temp_selectors = [
                    '.temperature', '.temp', '.current-temp',
                    '.current-temperature', '.temp-value', 
                    'span.temp', 'div.temp', 'h1', 'h2', 'h3'
                ]
                
                for selector in generic_temp_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        for element in elements[:3]:
                            text = await element.inner_text()
                            if text and ('°' in text or 'temp' in text.lower()):
                                # Extract temperature using regex
                                import re
                                temp_match = re.search(r'(\d+)\s*[°℃℉]\s*[CFcf]?', text)
                                if temp_match:
                                    temperature = text.strip()
                                    logger.debug(f"Generic temp found: {temperature}")
                                    break
                        if temperature != "Unknown":
                            break
                    except Exception as e:
                        continue
                
                # Generic conditions
                if conditions == "Unknown":
                    # Look for weather condition patterns in page text
                    try:
                        page_content = await page.content()
                        import re
                        
                        condition_patterns = [
                            r'\b(sunny|clear)\b',
                            r'\b(cloudy|overcast)\b', 
                            r'\b(partly cloudy)\b',
                            r'\b(rain|rainy|raining)\b',
                            r'\b(snow|snowy|snowing)\b',
                            r'\b(storm|stormy)\b',
                            r'\b(fog|foggy)\b'
                        ]
                        
                        for pattern in condition_patterns:
                            match = re.search(pattern, page_content, re.IGNORECASE)
                            if match:
                                conditions = match.group(1).title()
                                logger.debug(f"Generic condition found: {conditions}")
                                break
                    except Exception as e:
                        logger.debug(f"Error in generic condition extraction: {str(e)}")
            
            # Final result
            result = {
                'temperature': temperature,
                'conditions': conditions,
                'forecast': forecast,
                **additional_data
            }
            
            logger.info(f"Fallback text extraction result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text data: {str(e)}")
            return {
                'temperature': "Unknown",
                'conditions': "Unknown", 
                'forecast': "Unknown"
            }

    async def _process_visual_elements(self, page) -> Dict[str, Any]:
        """Process visual elements from the page"""
        visual_data = {}
        
        # Check if this is WorldWeatherOnline for Pulilan
        is_pulilan_wwo = False
        try:
            url = page.url
            if 'worldweatheronline.com' in url and 'pulilan' in url.lower():
                is_pulilan_wwo = True
                logger.info("Processing WorldWeatherOnline Pulilan page visuals")
        except:
            pass
            
        if is_pulilan_wwo:
            # Specific element types for WorldWeatherOnline
            wwo_elements = {
                'forecast_table': 'table:has(th:has-text("Weather in Pulilan"))',
                'weather_map': 'img[src*="map"], div.map-container',
                'hourly_forecast': 'div:has-text("Hourly")', 
                'weekly_forecast': 'table:has(th:has-text("14 Day Weather Pulilan"))'
            }
            
            # Process the forecast table
            try:
                forecast_table = await page.locator(wwo_elements['forecast_table']).screenshot()
                if forecast_table:
                    element_hash = hashlib.sha256(forecast_table).hexdigest()
                    cached = self.visual_cache.get(element_hash)
                    if cached:
                        logger.debug("Using cached analysis for forecast table")
                        visual_data['forecast_table'] = cached
                    else:
                        analysis = await self.vision_analyzer.analyze(forecast_table, 'table')
                        self.visual_cache.store(element_hash, analysis)
                        visual_data['forecast_table'] = analysis
                    logger.debug("Processed forecast table visual")
            except Exception as e:
                logger.warning(f"Error processing forecast table: {str(e)}")

            # Process the weather map if available
            try:
                map_image = await page.locator(wwo_elements['weather_map']).screenshot()
                if map_image:
                    element_hash = hashlib.sha256(map_image).hexdigest()
                    cached = self.visual_cache.get(element_hash)
                    if cached:
                        logger.debug("Using cached analysis for weather map")
                        visual_data['map'] = cached
                    else:
                        analysis = await self.vision_analyzer.analyze(map_image, 'map')
                        self.visual_cache.store(element_hash, analysis)
                        visual_data['map'] = analysis
                    logger.debug("Processed weather map visual")
            except Exception as e:
                logger.warning(f"Error processing weather map: {str(e)}")

            # Process the weekly forecast table
            try:
                weekly_forecast = await page.locator(wwo_elements['weekly_forecast']).screenshot()
                if weekly_forecast:
                    element_hash = hashlib.sha256(weekly_forecast).hexdigest()
                    cached = self.visual_cache.get(element_hash)
                    if cached:
                        logger.debug("Using cached analysis for weekly forecast")
                        visual_data['weekly_forecast'] = cached
                    else:
                        analysis = await self.vision_analyzer.analyze(weekly_forecast, 'chart')
                        self.visual_cache.store(element_hash, analysis)
                        visual_data['weekly_forecast'] = analysis
                    logger.debug("Processed weekly forecast visual")
            except Exception as e:
                logger.warning(f"Error processing weekly forecast: {str(e)}")

            return visual_data
           
        # Regular element types for other weather sites
        element_types = ['chart', 'map', 'table', 'radar']

        for element_type in element_types:
            try:
                # Example selector - adjust based on target website
                element = await page.locator(f'.weather-{element_type}').screenshot()
                
                # Generate cache key
                element_hash = hashlib.sha256(element).hexdigest()
                
                # Check cache
                cached = self.visual_cache.get(element_hash)
                if cached:
                    logger.debug(f"Using cached analysis for {element_type}")
                    visual_data[element_type] = cached
                    continue

                # Analyze with OpenAI Vision
                analysis = await self.vision_analyzer.analyze(element, element_type)
                
                # Cache results
                self.visual_cache.store(element_hash, analysis)
                
                visual_data[element_type] = analysis
                logger.debug(f"Processed {element_type} element")
            except Exception as e:
                logger.warning(f"Error processing {element_type}: {str(e)}")
                continue

        # If no visuals were found using the specific selectors, try to capture full page screenshots
        if not visual_data:
            try:
                logger.info("No specific visual elements found. Capturing full page screenshot.")
                full_page = await page.screenshot(full_page=True)
                element_hash = hashlib.sha256(full_page).hexdigest()
                cached = self.visual_cache.get(element_hash)
                if cached:
                    visual_data['full_page'] = cached
                else:
                    analysis = await self.vision_analyzer.analyze(full_page, 'weather_page')
                    self.visual_cache.store(element_hash, analysis)
                    visual_data['full_page'] = analysis
            except Exception as e:
                logger.warning(f"Error processing full page screenshot: {str(e)}")

        return visual_data

    def _aggregate_data(self, text_data: Dict[str, Any], visual_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine and validate scraped data with enhanced structure for municipal weather reporting"""
        # Combine text and visual data with enhanced structure
        aggregated_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": self.config.get("SOURCE_NAME", "unknown"),
                "version": "2.0",  # Updated version for enhanced data structure
                "data_richness": text_data.get("data_richness", "standard"),
                "extraction_method": "vision_primary" if text_data.get("vision_extracted") else "text_fallback"
            },
            "text_data": text_data,
            "visual_data": visual_data
        }
        
        # Enhanced current conditions section with visual context
        aggregated_data["current_conditions"] = {
            "temperature": text_data.get("temperature"),
            "conditions": text_data.get("conditions"),
            "heat_index": text_data.get("heat_index"),
            "current_time": text_data.get("current_time"),
            "details": {
                "wind": text_data.get("wind"),
                "humidity": text_data.get("humidity"),
                "pressure": text_data.get("pressure"),
                "visibility": text_data.get("visibility"),
                "uv_index": text_data.get("uv_index"),
                "precipitation": text_data.get("precipitation"),
                "air_quality": text_data.get("air_quality")
            },
            "visual_context": text_data.get("visual_analysis", {}),
            "activity_suitability": text_data.get("activity_suitability")
        }
        
        # Enhanced forecast section with today's focus
        aggregated_data["forecast"] = {
            "today_hourly": text_data.get("today_hourly", []),
            "hourly_summary": text_data.get("hourly_summary"),
            "daily": text_data.get("daily_forecast", []),
            "summary": text_data.get("forecast"),
            "tomorrow_preview": self._extract_tomorrow_preview(text_data.get("daily_forecast", []))
        }
        
        # Enhanced location context for municipal reporting
        aggregated_data["location_context"] = {
            "municipality": text_data.get("location"),
            "region": text_data.get("region"),
            "country": text_data.get("country"),
            "local_time": text_data.get("local_time"),
            "timezone_context": text_data.get("timezone_context"),
            "municipal_context": {
                "local_references": text_data.get("municipal_context", {}).get("local_references", []),
                "weather_activities": text_data.get("municipal_context", {}).get("weather_activities", []),
                "health_advisories": text_data.get("municipal_context", {}).get("health_advisories", []),
                "community_impact": text_data.get("municipal_context", {}).get("community_impact", "Unknown")
            }
        }
        
        # Enhanced atmospheric and storytelling data
        aggregated_data["atmospheric_data"] = {
            "sunrise": text_data.get("sunrise"),
            "sunset": text_data.get("sunset"),
            "daylight_hours": text_data.get("daylight_hours"),
            "weather_summary": text_data.get("weather_summary"),
            "seasonal_note": text_data.get("seasonal_note"),
            "alerts": text_data.get("alerts", []),
            "visual_mood": text_data.get("visual_analysis", {}).get("page_mood"),
            "visual_energy": text_data.get("visual_analysis", {}).get("visual_energy")
        }
        
        # Process enhanced visual data if available
        if "weather_data" in visual_data:
            enhanced_visual = visual_data.get("weather_data", {})
            if isinstance(enhanced_visual, dict):
                # Add visual analysis for storytelling
                if "visual_analysis" in enhanced_visual:
                    aggregated_data["visual_storytelling"] = enhanced_visual["visual_analysis"]
                
                # Add municipal context for local reporting
                if "municipal_context" in enhanced_visual:
                    aggregated_data["local_impact"] = enhanced_visual["municipal_context"]
        
        # Add validation status with enhanced criteria
        aggregated_data["metadata"]["is_valid"] = bool(
            text_data.get("temperature") and 
            text_data.get("conditions") and
            text_data.get("location")
        )
        
        # Add data completeness assessment
        completeness_score = self._assess_data_completeness(text_data)
        aggregated_data["metadata"]["completeness_score"] = completeness_score
        aggregated_data["metadata"]["segment_readiness"] = completeness_score >= 0.7  # 70% completeness for good segments
        
        logger.info(f"Enhanced data aggregation completed: valid={aggregated_data['metadata']['is_valid']}, completeness={completeness_score:.2f}, richness={aggregated_data['metadata']['data_richness']}")
        return aggregated_data
    
    def _extract_tomorrow_preview(self, daily_forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract tomorrow's weather for preview segment"""
        try:
            if len(daily_forecast) >= 2:  # Should have today and tomorrow
                tomorrow = daily_forecast[1]  # Second entry should be tomorrow
                return {
                    "high": tomorrow.get("high"),
                    "low": tomorrow.get("low"),
                    "conditions": tomorrow.get("conditions"),
                    "precipitation": tomorrow.get("precipitation"),
                    "comparison_note": f"Tomorrow will be {tomorrow.get('conditions', 'unknown')} with highs around {tomorrow.get('high', 'unknown')}"
                }
            return {"comparison_note": "Tomorrow's forecast not available"}
        except Exception as e:
            logger.warning(f"Error extracting tomorrow preview: {str(e)}")
            return {"comparison_note": "Tomorrow's forecast unavailable"}
    
    def _assess_data_completeness(self, text_data: Dict[str, Any]) -> float:
        """Assess completeness of scraped data for segment generation"""
        try:
            # Define required and optional fields with weights
            required_fields = {
                'temperature': 0.3,
                'conditions': 0.3, 
                'location': 0.2
            }
            
            optional_fields = {
                'wind': 0.05,
                'humidity': 0.05,
                'today_hourly': 0.05,
                'daily_forecast': 0.05,
                'sunrise': 0.02,
                'sunset': 0.02,
                'visual_analysis': 0.05,
                'municipal_context': 0.03
            }
            
            score = 0.0
            max_score = sum(required_fields.values()) + sum(optional_fields.values())
            
            # Score required fields
            for field, weight in required_fields.items():
                if text_data.get(field) and text_data.get(field) != 'Unknown':
                    score += weight
            
            # Score optional fields
            for field, weight in optional_fields.items():
                value = text_data.get(field)
                if value and value != 'Unknown':
                    if isinstance(value, (list, dict)) and len(value) > 0:
                        score += weight
                    elif isinstance(value, str) and len(value) > 0:
                        score += weight
            
            return min(score / max_score, 1.0)  # Normalize to 0-1
            
        except Exception as e:
            logger.warning(f"Error assessing data completeness: {str(e)}")
            return 0.5  # Default moderate score

    async def scrape_and_save(self, url: str, page_timeout: int = 60000, location_override: Dict[str, str] = None) -> str:
        """Scrape weather data from a URL and save it to generated directory"""
        try:
            # Scrape the data
            logger.info(f"Scraping with timeout: {page_timeout}ms")
            weather_data = await self.scrape_weather_data(url, page_timeout=page_timeout, location_override=location_override)
            logger.info("Successfully scraped weather data")
            
            # Save to generated directory
            generated_dir = 'generated'
            os.makedirs(generated_dir, exist_ok=True)
            
            output_file = os.path.join(generated_dir, 'weather_data.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(weather_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved weather data to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error in scrape_and_save: {str(e)}")
            raise

async def main():
    """Main function for command-line usage"""
    import argparse
    
    # Import defaults from config
    from config import (
        DEFAULT_WEATHER_URL, 
        DEFAULT_MUNICIPALITY, 
        DEFAULT_REGION, 
        DEFAULT_COUNTRY,
        DEFAULT_WEATHER_TIMEOUT,
        DEFAULT_WEATHER_HEADLESS,
        DEFAULT_WEATHER_SLOWMO
    )
    
    parser = argparse.ArgumentParser(description='Scrape weather data using enhanced vision analysis')
    parser.add_argument('-u', '--url', default=DEFAULT_WEATHER_URL, help=f'Weather page URL to scrape (default: {DEFAULT_WEATHER_URL})')
    parser.add_argument('--timeout', type=int, default=DEFAULT_WEATHER_TIMEOUT, help=f'Page timeout in milliseconds (default: {DEFAULT_WEATHER_TIMEOUT})')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in non-headless mode (for debugging)')
    parser.add_argument('--slowmo', type=int, default=DEFAULT_WEATHER_SLOWMO, help=f'Slow motion delay in milliseconds (default: {DEFAULT_WEATHER_SLOWMO})')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Location override parameters (especially useful for MSN) - with defaults from config
    parser.add_argument('--municipality', type=str, default=DEFAULT_MUNICIPALITY, help=f'Municipality/city name to override extracted location (default: {DEFAULT_MUNICIPALITY})')
    parser.add_argument('--region', type=str, default=DEFAULT_REGION, help=f'Region/state name to override extracted location (default: {DEFAULT_REGION})')
    parser.add_argument('--country', type=str, default=DEFAULT_COUNTRY, help=f'Country name to override extracted location (default: {DEFAULT_COUNTRY})')
    
    args = parser.parse_args()
    
    # Set up logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Override headless mode based on arguments, with config default as fallback
    headless_mode = DEFAULT_WEATHER_HEADLESS  # Use config default
    if args.no_headless:
        headless_mode = False
    elif args.headless:
        headless_mode = True
    
    # Create location override - now always create since we have defaults from config
    location_override = {
        'municipality': args.municipality,
        'region': args.region,
        'country': args.country
    }
    logger.info(f"Using location override from config: {location_override}")
    
    # Configuration for scraping
    config = {
        'HEADLESS': headless_mode,
        'SLOW_MO': args.slowmo,
        'DATA_DIR': 'data',
        'SOURCE_NAME': 'manual_scraping'
    }
    
    try:
        # Initialize scraping system
        scraper = ScrapingSystem(config)
        
        # Scrape data and save to generated directory
        print(f"🚀 Starting weather scraping for URL: {args.url}")
        if location_override:
            print(f"📍 Using location override: {location_override}")
        
        output_file = await scraper.scrape_and_save(
            url=args.url,
            page_timeout=args.timeout,
            location_override=location_override
        )
        
        # Load the result for display
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        print(f"✅ Successfully scraped weather data!")
        print(f"📁 Data saved to: {output_file}")
        
        # Print key extracted data for verification
        weather_data = result.get('text_data', {})  # Use text_data instead of weather_data
        print(f"🌡️  Temperature: {weather_data.get('temperature', 'Unknown')}")
        print(f"☁️  Conditions: {weather_data.get('conditions', 'Unknown')}")
        print(f"📍 Location: {weather_data.get('location', 'Unknown')}, {weather_data.get('region', 'Unknown')}")
        print(f"🔍 Data Source: {result.get('metadata', {}).get('source', 'Unknown')}")
        print(f"📊 Data Richness: {weather_data.get('data_richness', 'Unknown')}")
        if location_override:
            print(f"🏷️  Location Override Applied: {weather_data.get('location_overridden', False)}")
        
        # Additional rich data display
        print(f"💨 Wind: {weather_data.get('wind', 'Unknown')}")
        print(f"💧 Humidity: {weather_data.get('humidity', 'Unknown')}")
        print(f"🌅 Sunrise: {weather_data.get('sunrise', 'Unknown')}")
        print(f"🌅 Sunset: {weather_data.get('sunset', 'Unknown')}")
        print(f"🎯 Completeness Score: {result.get('metadata', {}).get('completeness_score', 'Unknown')}")
        print(f"🎨 Visual Mood: {weather_data.get('visual_analysis', {}).get('page_mood', 'Unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to scrape weather data: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    # Set up logging when running as a script
    import config
    
    # Configure loguru logger
    log_format = config.LOG_FORMAT if hasattr(config, 'LOG_FORMAT') else "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    logs_dir = config.LOGS_DIR if hasattr(config, 'LOGS_DIR') else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, format=log_format, level="INFO")
    logger.add(os.path.join(logs_dir, "scraper_cli.log"), rotation="500 MB", retention="10 days", format=log_format)
    
    logger.info("Starting step1_scrape_data.py as standalone script")
    # Run the main function
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Step 4: Update News Manifest with Media
This script updates news_manifest.json to add relevant media based on news_data.json

python step4_update_manifest.py --add-weather
"""

import os
import json
import sys

def load_news_data():
    """Load news data from generated/news_data.json"""
    news_data_path = os.path.join('generated', 'news_data.json')
    if not os.path.exists(news_data_path):
        print(f"Error: {news_data_path} not found!")
        return None
    
    with open(news_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} news items from {news_data_path}")
    return data

def load_manifest():
    """Load current news manifest as a list of segments"""
    manifest_path = os.path.join('generated', 'news_manifest.json')
    if not os.path.exists(manifest_path):
        print(f"Error: {manifest_path} not found!")
        print("Please run step 3 first to generate audio files.")
        return None
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded manifest with {len(data)} segments")
    return data

def make_weather_abs_path(path):
    if path.startswith('/'):
        return path
    if path.startswith('generated/'):
        return f"/weather/{path}"
    return f"/weather/generated/{path}"

def format_weather_segment(seg):
    """Format a weather segment to match the required manifest format for the player."""
    # Ensure audio_path is absolute and correct
    seg['audio_path'] = make_weather_abs_path(seg['audio_path'])
    # Ensure media array exists
    if 'media' not in seg or not isinstance(seg['media'], list):
        seg['media'] = []
    # Make all media.path absolute and correct
    for m in seg['media']:
        if 'path' in m:
            m['path'] = make_weather_abs_path(m['path'])
    # Ensure headline is an object
    headline_text = seg.get('headline', seg.get('segment_index', 'Weather'))
    seg['headline'] = {
        "text": headline_text if isinstance(headline_text, str) else str(headline_text),
        "location": "Pulilan, Bulacan",
        "category": "Weather",
        "priority": "normal",
        "timestamp": "LIVE"
    }
    return seg

def load_weather_segments():
    """Load and extract required weather segments from weather/generated/weather_manifest.json, formatted for the player."""
    weather_manifest_path = os.path.join('weather', 'generated', 'weather_manifest.json')
    if not os.path.exists(weather_manifest_path):
        print(f"Error: {weather_manifest_path} not found!")
        return []
    with open(weather_manifest_path, 'r', encoding='utf-8') as f:
        weather_data = json.load(f)
    print(f"Loaded weather manifest with {len(weather_data)} segments")
    # List of required segment_types
    required_types = [
        'weather_overview',
        'weather_current_overview',
        'card_wind',
        'weather_map1',
        'weather_map2',
        'card_temperature',
        'card_feels_like',
        'card_current',
        'card_hourly',
    ]
    selected_segments = [format_weather_segment(seg) for seg in weather_data if seg['segment_type'] in required_types]
    print(f"Extracted {len(selected_segments)} required weather segments:")
    for seg in selected_segments:
        print(f"  - {seg['segment_index']} ({seg['segment_type']})")
    return selected_segments

def map_media_to_segments(segments, news_data):
    """Map media from news_data to manifest segments (segments is a list)"""
    print("Mapping media to segments...")
    updated_segments = []
    for segment in segments:
        segment_type = segment['segment_type']
        segment_index = segment.get('segment_index', '')
        print(f"\nProcessing segment: {segment_type} ({segment_index})")
        segment['media'] = []
        # Add anchor_video field
        anchor_video_path = f"generated/anchor/{segment_index}.mp4"
        if os.path.exists(anchor_video_path):
            segment['anchor_video'] = anchor_video_path
        else:
            segment['anchor_video'] = ""
        if segment_type == 'opening_greeting':
            segment['media'].append({
                "video": "intro.mp4",
                "path": "media/intro.mp4",
                "type": "intro_video"
            })
            print(f"  ✅ Added intro.mp4")
        elif segment_type == 'closing_remarks':
            segment['media'].append({
                "video": "outro.mp4",
                "path": "media/outro.mp4",
                "type": "outro_video"
            })
            print(f"  ✅ Added outro.mp4")
        elif segment_type == 'headline_opening':
            segment['media'].append({
                "video": "babad.mp4",
                "path": "media/babad.mp4",
                "type": "babad_video"
            })
            print(f"  ✅ Added outro.mp4")
        elif segment_type == 'headline':
            headline_number = None
            if segment_index.startswith('headline_'):
                try:
                    headline_number = int(segment_index.split('_')[1])
                except (ValueError, IndexError):
                    print(f"  ⚠️  Could not extract headline number from: {segment_index}")
            if headline_number is not None:
                headline_index = headline_number - 1
                if headline_index >= 0 and headline_index < len(news_data):
                    news_item = news_data[headline_index]
                    segment['headline'] = {
                        "text": segment.get('script', ''),
                        "location": "Pulilan, Bulacan",
                        "category": "Breaking News" if headline_number == 1 else "Local News",
                        "priority": "high" if headline_number == 1 else "normal",
                        "timestamp": "LIVE"
                    }
                    if news_item.get('media') and len(news_item['media']) > 0:
                        first_image = news_item['media'][0]
                        segment['media'].append({
                            "image": first_image['image'],
                            "path": f"media/{first_image['image']}",
                            "type": "headline_image",
                            "news_index": headline_index + 1,
                            "original_name": first_image.get('original_name', ''),
                            "size_mb": first_image.get('size_mb', 0)
                        })
                        print(f"  ✅ Added headline {headline_number} with lower-third data and image: {first_image['image'][:30]}...")
                    else:
                        print(f"  ⚠️  No media found for headline {headline_number}")
                else:
                    print(f"  ⚠️  Headline {headline_number} not found in news data (only {len(news_data)} items)")
            else:
                print(f"  ⚠️  Could not determine headline number for: {segment_index}")
        elif segment_type == 'news':
            news_number = None
            if segment_index.startswith('news_'):
                try:
                    news_number = int(segment_index.split('_')[1])
                except (ValueError, IndexError):
                    print(f"  ⚠️  Could not extract news story number from: {segment_index}")
            if news_number is not None:
                news_index = news_number - 1
                if news_index >= 0 and news_index < len(news_data):
                    news_item = news_data[news_index]
                    corresponding_headline = None
                    for header_segment in segments:
                        if (header_segment['segment_type'] == 'headline' and 
                            header_segment.get('segment_index', '') == f"headline_{news_number}"):
                            corresponding_headline = header_segment
                            break
                    if corresponding_headline and corresponding_headline.get('headline'):
                        segment['headline'] = corresponding_headline['headline'].copy()
                        print(f"  ✅ Added headline info from 'headline_{news_number}' to news story")
                    else:
                        segment['headline'] = {
                            "text": news_item.get('title', segment.get('script', '')[:100] + '...'),
                            "location": "Pulilan, Bulacan",
                            "category": "Breaking News" if news_number == 1 else "Local News",
                            "priority": "high" if news_number == 1 else "normal",
                            "timestamp": "LIVE"
                        }
                        print(f"  ✅ Added fallback headline info for news story {news_number}")
                    if news_item.get('media'):
                        for media_item in news_item['media']:
                            segment['media'].append({
                                "image": media_item['image'],
                                "path": f"media/{media_item['image']}",
                                "type": "news_image",
                                "original_name": media_item.get('original_name', ''),
                                "size_mb": media_item.get('size_mb', 0)
                            })
                        print(f"  ✅ Added {len(news_item['media'])} media items for news story {news_number}")
                    else:
                        print(f"  ⚠️  No media found for news story {news_number}")
                else:
                    print(f"  ⚠️  News story {news_number} not found in news data (only {len(news_data)} items)")
            else:
                print(f"  ⚠️  Could not determine news story number for: {segment_index}")
        updated_segments.append(segment)
    return updated_segments

def insert_weather_segments(segments, weather_segments):
    """Insert weather segments after the last news segment and before closing remarks."""
    # Find index of last news segment
    last_news_idx = -1
    for i, seg in enumerate(segments):
        if seg['segment_type'] == 'news':
            last_news_idx = i
    if last_news_idx == -1:
        print("Warning: No news segment found. Appending weather segments before closing remarks.")
        for i, seg in enumerate(segments):
            if seg['segment_type'] == 'closing_remarks':
                last_news_idx = i - 1
                break
        if last_news_idx == -1:
            print("Warning: No closing_remarks found. Appending weather segments at end.")
            last_news_idx = len(segments) - 1
    insert_pos = last_news_idx + 1
    print(f"Inserting weather segments at position {insert_pos}")
    new_segments = segments[:insert_pos] + weather_segments + segments[insert_pos:]
    print(f"Manifest now has {len(new_segments)} segments after weather insertion.")
    return new_segments

def save_updated_manifest(segments):
    """Save updated manifest back to file as a list"""
    manifest_path = os.path.join('generated', 'news_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Updated manifest saved to: {manifest_path}")

def print_media_summary(segments):
    """Print summary of media assignments"""
    print(f"\n📊 Media Assignment Summary:")
    print(f"=" * 50)
    for segment in segments:
        media_count = len(segment.get('media', []))
        print(f"{segment.get('segment_index', '')}: {media_count} media items")
        for media in segment.get('media', []):
            if 'video' in media:
                print(f"  🎥 {media['video']} ({media['type']})")
            elif 'image' in media:
                print(f"  🖼️  {media['image'][:40]}... ({media['type']})")

def main():
    """Main function to update manifest with media and optionally add weather segments"""
    print("=== Nexcaster News Manifest Media Updater ===")
    print("Step 4: Adding media mappings to news manifest")
    print()
    add_weather = False
    if '--add-weather' in sys.argv:
        add_weather = True
        print("[CLI] --add-weather flag detected. Will insert weather segments.")
    news_data = load_news_data()
    if not news_data:
        return
    segments = load_manifest()
    if not segments:
        return
    updated_segments = map_media_to_segments(segments, news_data)
    if add_weather:
        weather_segments = load_weather_segments()
        updated_segments = insert_weather_segments(updated_segments, weather_segments)
        print("[INFO] Weather segments inserted into manifest.")
    save_updated_manifest(updated_segments)
    print_media_summary(updated_segments)
    print(f"\n🎯 Media mapping complete!")
    print(f"All segments now have appropriate media assignments.")

if __name__ == "__main__":
    main() 
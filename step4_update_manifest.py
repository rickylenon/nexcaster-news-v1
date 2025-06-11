#!/usr/bin/env python3
"""
Step 4: Update News Manifest with Media
This script updates news_manifest.json to add relevant media based on news_data.json
"""

import os
import json

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
    """Load current news manifest"""
    manifest_path = os.path.join('generated', 'news_manifest.json')
    if not os.path.exists(manifest_path):
        print(f"Error: {manifest_path} not found!")
        print("Please run step 3 first to generate audio files.")
        return None
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded manifest with {len(data['individual_segments'])} segments")
    return data

def map_media_to_segments(manifest, news_data):
    """Map media from news_data to manifest segments"""
    print("Mapping media to segments...")
    
    updated_segments = []
    
    for segment in manifest['individual_segments']:
        segment_type = segment['segment_type']
        print(f"\nProcessing segment: {segment_type}")
        
        # Add media array to segment
        segment['media'] = []
        
        if segment_type == 'opening_greeting':
            # Add intro.mp4 for opening
            segment['media'].append({
                "video": "intro.mp4",
                "path": "media/intro.mp4",
                "type": "intro_video"
            })
            print(f"  ✅ Added intro.mp4")
            
        elif segment_type == 'closing_remarks':
            # Add outro.mp4 for closing
            segment['media'].append({
                "video": "outro.mp4", 
                "path": "media/outro.mp4",
                "type": "outro_video"
            })
            print(f"  ✅ Added outro.mp4")
            
        elif segment_type == 'headline_opening':
            # No media for headline opening - it's just the introduction
            print(f"  📢 Headline opening - no media needed")
            
        elif segment_type == 'headline':
            # For headlines, extract the number from display_name (e.g., "News Headline 1" -> 1)
            display_name = segment.get('display_name', '')
            headline_number = None
            
            # Extract number from display name like "News Headline 1", "News Headline 2", etc.
            if 'Headline' in display_name:
                try:
                    # Split by space and get the last part, which should be the number
                    parts = display_name.split()
                    headline_number = int(parts[-1])
                except (ValueError, IndexError):
                    print(f"  ⚠️  Could not extract headline number from: {display_name}")
            
            if headline_number is not None:
                headline_index = headline_number - 1  # Convert to 0-based index
                if headline_index >= 0 and headline_index < len(news_data):
                    news_item = news_data[headline_index]
                    
                    # Add first media from corresponding news item for headline
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
                        print(f"  ✅ Added headline {headline_number} image: {first_image['image'][:30]}...")
                    else:
                        print(f"  ⚠️  No media found for headline {headline_number}")
                else:
                    print(f"  ⚠️  Headline {headline_number} not found in news data (only {len(news_data)} items)")
            else:
                print(f"  ⚠️  Could not determine headline number for: {display_name}")
            
        elif segment_type == 'news':
            # For news stories, extract the number from display_name (e.g., "News Story 1" -> 1)
            display_name = segment.get('display_name', '')
            news_number = None
            
            # Extract number from display name like "News Story 1", "News Story 2", etc.
            if 'Story' in display_name:
                try:
                    # Split by space and get the last part, which should be the number
                    parts = display_name.split()
                    news_number = int(parts[-1])
                except (ValueError, IndexError):
                    print(f"  ⚠️  Could not extract news story number from: {display_name}")
            
            if news_number is not None:
                news_index = news_number - 1  # Convert to 0-based index
                if news_index >= 0 and news_index < len(news_data):
                    news_item = news_data[news_index]
                    
                    # Add all media from corresponding news item
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
                print(f"  ⚠️  Could not determine news story number for: {display_name}")
        
        updated_segments.append(segment)
    
    # Update manifest with media-enhanced segments
    manifest['individual_segments'] = updated_segments
    
    return manifest

def save_updated_manifest(manifest):
    """Save updated manifest back to file"""
    manifest_path = os.path.join('generated', 'news_manifest.json')
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Updated manifest saved to: {manifest_path}")

def print_media_summary(manifest):
    """Print summary of media assignments"""
    print(f"\n📊 Media Assignment Summary:")
    print(f"=" * 50)
    
    for segment in manifest['individual_segments']:
        media_count = len(segment.get('media', []))
        print(f"{segment['display_name']}: {media_count} media items")
        
        for media in segment.get('media', []):
            if 'video' in media:
                print(f"  🎥 {media['video']} ({media['type']})")
            elif 'image' in media:
                print(f"  🖼️  {media['image'][:40]}... ({media['type']})")

def main():
    """Main function to update manifest with media"""
    print("=== Nexcaster News Manifest Media Updater ===")
    print("Step 4: Adding media mappings to news manifest")
    print()
    
    # Load news data
    news_data = load_news_data()
    if not news_data:
        return
    
    # Load current manifest
    manifest = load_manifest()
    if not manifest:
        return
    
    # Map media to segments
    updated_manifest = map_media_to_segments(manifest, news_data)
    
    # Save updated manifest
    save_updated_manifest(updated_manifest)
    
    # Print summary
    print_media_summary(updated_manifest)
    
    print(f"\n🎯 Media mapping complete!")
    print(f"All segments now have appropriate media assignments.")

if __name__ == "__main__":
    main() 
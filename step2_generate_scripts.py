#!/usr/bin/env python3
"""
Step 2: Generate News Scripts
This script generates news_scripts.json from news_data.json using LLM
"""

import os
import json
import openai
from datetime import datetime
import pytz
from config import SEGMENT_TYPES, DEFAULT_SEGMENT_ORDER, STATION_INFO, LLM_CONFIG, LANGUAGE

def load_news_data():
    """Load news data from generated/news_data.json"""
    news_data_path = os.path.join('generated', 'news_data.json')
    if not os.path.exists(news_data_path):
        print(f"Error: {news_data_path} not found!")
        print("Please run step 1 first to upload news content.")
        return None
    
    with open(news_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} news items from {news_data_path}")
    return data

def get_current_time_info():
    """Get current time information for the news broadcast"""
    manila_tz = pytz.timezone(STATION_INFO['timezone'])
    now = datetime.now(manila_tz)
    
    time_info = {
        'time': now.strftime('%I:%M %p'),
        'day': now.strftime('%A'),
        'date': now.strftime('%B %d, %Y'),
        'location': STATION_INFO['location'],
        'region': STATION_INFO['region'],
        'station': STATION_INFO['station_name'],
        'anchor': STATION_INFO['anchor_name']
    }
    
    print(f"Broadcast time: {time_info['time']} on {time_info['day']}, {time_info['date']}")
    return time_info

def generate_opening_script(time_info):
    """Generate opening greeting script"""
    hour = datetime.now().hour
    
    if LANGUAGE.lower() == "filipino":
        if hour < 12:
            greeting = "Magandang umaga"
        elif hour < 18:
            greeting = "Magandang hapon"
        else:
            greeting = "Magandang gabi"
        
        script = f"{greeting}, {time_info['location']}! Ito ang {time_info['time']} ngayong {time_info['day']}, {time_info['date']}, dito sa {time_info['region']}. Ako si {time_info['anchor']} mula sa {time_info['station']}, naghahatid ng mga pinakabagong balita at update mula sa aming komunidad."
    else:
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        script = f"{greeting}, {time_info['location']}! It's {time_info['time']} on this {time_info['day']}, {time_info['date']}, here in {time_info['region']}. I'm {time_info['anchor']} with {time_info['station']}, bringing you the latest news and updates from our community."
    
    return {
        "segment_name": "opening_greeting",
        "display_name": SEGMENT_TYPES["opening"]["display_name"],
        "display_order": 0,
        "duration": SEGMENT_TYPES["opening"]["default_duration"],
        "script": script
    }

def generate_summary_script(news_data, time_info):
    """Generate news summary script using LLM"""
    if not news_data:
        return None
    
    # Prepare context for LLM
    news_context = ""
    for i, item in enumerate(news_data, 1):
        news_context += f"News {i}: {item['news']}\n"
    
    prompt = f"""Create a brief news summary script for {STATION_INFO['station_name']} based on these news items:

{news_context}

Requirements:
- Language: Write the script in {LANGUAGE}
- Duration: approximately {SEGMENT_TYPES['summary']['default_duration']} seconds
- Professional TV news tone
- Local Pulilan, Bulacan perspective
- Brief overview highlighting the main stories
- Smooth transition to detailed news coverage
- DO NOT start with greetings (opening already handled that)
- Start directly with "Narito ang mga pangunahing balita..." or similar
- IMPORTANT: Generate ONLY the text that the anchor would speak out loud
- Do NOT include video directions, camera cuts, or production notes
- Output should be ready for text-to-speech conversion

Script (anchor speech only in {LANGUAGE}, no greeting):"""

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": LLM_CONFIG["system_prompt"]},
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_CONFIG["temperature"],
            max_tokens=LLM_CONFIG["max_tokens"]
        )
        
        script = response.choices[0].message.content.strip()
        print("Generated summary script using LLM")
        
        return {
            "segment_name": "news_summary",
            "display_name": SEGMENT_TYPES["summary"]["display_name"],
            "display_order": 1,
            "duration": SEGMENT_TYPES["summary"]["default_duration"],
            "script": script
        }
    except Exception as e:
        print(f"Error generating summary script: {e}")
        # Fallback to simple template
        if LANGUAGE.lower() == "filipino":
            fallback_script = f"Narito ang mga pangunahing balita ngayong araw mula sa {time_info['location']} at mga karatig lugar sa {time_info['region']}."
        else:
            fallback_script = f"Here are today's top stories from {time_info['location']} and surrounding areas in {time_info['region']}."
        
        return {
            "segment_name": "news_summary",
            "display_name": SEGMENT_TYPES["summary"]["display_name"],
            "display_order": 1,
            "duration": SEGMENT_TYPES["summary"]["default_duration"],
            "script": fallback_script
        }

def generate_news_scripts(news_data, time_info):
    """Generate individual news story scripts using LLM"""
    news_scripts = []
    
    for i, news_item in enumerate(news_data):
        print(f"Generating script for news item {i+1}...")
        
        # Prepare media context
        media_context = ""
        if news_item.get('media'):
            media_types = []
            for media in news_item['media']:
                if 'image' in media:
                    media_types.append("images")
                elif 'video' in media:
                    media_types.append("video footage")
                elif 'link' in media:
                    media_types.append("online content")
            
            if media_types:
                media_context = f"\nAvailable media: {', '.join(set(media_types))}"
        
        prompt = f"""Create a news story script for {STATION_INFO['station_name']} based on this news content:

News Context: {news_item['news']}{media_context}

Requirements:
- Language: Write the script in {LANGUAGE}
- Duration: approximately {SEGMENT_TYPES['news']['default_duration']} seconds
- Professional TV news reporting style
- Include relevant details and context
- Local Pulilan, Bulacan perspective when applicable
- Engaging and informative for viewers
- Natural flow and good pacing
- DO NOT start with greetings like "Magandang araw" (opening already handled that)
- Start directly with the news content or use transitions like "Sa iba pang balita..."
- Maintain continuity with previous segments
- IMPORTANT: Generate ONLY the text that the anchor would speak out loud
- Do NOT include video directions, camera cuts, or production notes
- Do NOT include bracketed instructions like [Opening Shot] or [Cut to]
- Do NOT include quoted speech from other people - paraphrase their statements
- Output should be ready for text-to-speech conversion

Script (anchor speech only in {LANGUAGE}, no greeting, smooth transition):"""

        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=[
                    {"role": "system", "content": LLM_CONFIG["system_prompt"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=LLM_CONFIG["temperature"],
                max_tokens=LLM_CONFIG["max_tokens"]
            )
            
            script = response.choices[0].message.content.strip()
            print(f"Generated script for news item {i+1} using LLM")
            
        except Exception as e:
            print(f"Error generating script for news item {i+1}: {e}")
            # Fallback to simple template
            if LANGUAGE.lower() == "filipino":
                script = f"Sa iba pang balita, {news_item['news']}"
            else:
                script = f"In other news, {news_item['news']}"
        
        news_script = {
            "segment_name": f"news{i+1}",
            "display_name": f"News Story {i+1}",
            "display_order": i + 2,  # After opening and summary
            "duration": SEGMENT_TYPES["news"]["default_duration"],
            "script": script
        }
        
        news_scripts.append(news_script)
    
    return news_scripts

def generate_closing_script(time_info):
    """Generate closing script"""
    if LANGUAGE.lower() == "filipino":
        script = f"Iyan muna ang mga balita ngayong araw mula sa {time_info['station']}. Salamat sa inyong pakikinig dito sa {time_info['location']}, {time_info['region']}. Ako si {time_info['anchor']}, at makikita namin kayo sa susunod na ulat. Magkaroon kayo ng magandang araw!"
    else:
        script = f"That's all for now from {time_info['station']}. Thank you for staying informed with us here in {time_info['location']}, {time_info['region']}. I'm {time_info['anchor']}, and we'll see you next time. Have a great day!"
    
    return {
        "segment_name": "closing_remarks",
        "display_name": SEGMENT_TYPES["closing"]["display_name"],
        "display_order": 999,  # Last segment
        "duration": SEGMENT_TYPES["closing"]["default_duration"],
        "script": script
    }

def save_news_scripts(scripts):
    """Save generated scripts to news_scripts.json"""
    output_path = os.path.join('generated', 'news_scripts.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scripts, f, indent=2, ensure_ascii=False)
    
    print(f"News scripts saved to {output_path}")
    print(f"Generated {len(scripts)} script segments")

def main():
    """Main function to generate news scripts"""
    print("=== Nexcaster News Script Generator ===")
    print("Step 2: Generating news scripts from uploaded content")
    print()
    
    # Load news data
    news_data = load_news_data()
    if not news_data:
        return
    
    # Get current time information
    time_info = get_current_time_info()
    
    # Generate all script segments
    scripts = []
    
    # 1. Opening greeting
    print("Generating opening greeting...")
    opening = generate_opening_script(time_info)
    scripts.append(opening)
    
    # 2. News summary (if there are news items)
    if news_data:
        print("Generating news summary...")
        summary = generate_summary_script(news_data, time_info)
        if summary:
            scripts.append(summary)
    
    # 3. Individual news stories
    if news_data:
        print("Generating individual news stories...")
        news_scripts = generate_news_scripts(news_data, time_info)
        scripts.extend(news_scripts)
    
    # 4. Closing remarks
    print("Generating closing remarks...")
    closing = generate_closing_script(time_info)
    scripts.append(closing)
    
    # Sort by display_order
    scripts.sort(key=lambda x: x['display_order'])
    
    # Save to file
    save_news_scripts(scripts)
    
    print()
    print("=== Script Generation Complete ===")
    print(f"Total segments: {len(scripts)}")
    total_duration = sum(script['duration'] for script in scripts)
    print(f"Estimated total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
    
    # Display summary
    print("\nGenerated segments:")
    for script in scripts:
        print(f"  - {script['display_name']}: {script['duration']}s")

if __name__ == "__main__":
    main() 
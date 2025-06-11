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
import re
from dotenv import load_dotenv
from config import SEGMENT_TYPES, DEFAULT_SEGMENT_ORDER, STATION_INFO, LLM_CONFIG, LANGUAGE, FILIPINO_TEXT_PROCESSING, USE_REPLACEMENTS

# Load environment variables from .env file
load_dotenv()

def clean_special_characters(text):
    """Replace special characters with standard equivalents"""
    for char, replacement in FILIPINO_TEXT_PROCESSING["special_chars"].items():
        text = text.replace(char, replacement)
    return text

def apply_filipino_replacements(text):
    """Apply Filipino pronunciation and abbreviation replacements"""
    replacements = FILIPINO_TEXT_PROCESSING["replacements"]
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
    
    for original, replacement in sorted_replacements:
        # Use word boundaries for most replacements to avoid partial matches
        if original.isalpha() or original.endswith('.'):
            # For abbreviations and words, use word boundaries
            pattern = r'\b' + re.escape(original) + r'\b'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        else:
            # For symbols and other characters, simple replacement
            text = text.replace(original, replacement)
    
    return text

def apply_spell_out_replacements(text):
    """Apply spell-out replacements for specific terms"""
    spell_out = FILIPINO_TEXT_PROCESSING["spell_out"]
    
    for original, replacement in spell_out.items():
        # Use word boundaries to match complete terms
        pattern = r'\b' + re.escape(original) + r'\b'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def improve_address_formatting(text):
    """Improve address formatting to sound more natural"""
    address_patterns = FILIPINO_TEXT_PROCESSING["address_patterns"]
    
    for pattern_config in address_patterns:
        pattern = pattern_config["pattern"]
        replacement = pattern_config["replacement"]
        text = re.sub(pattern, replacement, text)
    
    return text

def clean_punctuation(text):
    """Clean and normalize punctuation for better TTS"""
    # Remove multiple consecutive punctuation
    text = re.sub(r'[.]{2,}', '...', text)  # Replace multiple dots with ellipsis
    text = re.sub(r'[!]{2,}', '!', text)    # Replace multiple exclamations
    text = re.sub(r'[?]{2,}', '?', text)    # Replace multiple questions
    
    # Ensure proper spacing after punctuation
    text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([,;])([A-Za-z])', r'\1 \2', text)
    
    # Remove parentheses and brackets (often contain production notes)
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def remove_production_notes(text):
    """Remove common production notes and TV directions"""
    # Common TV production phrases to remove
    production_phrases = [
        r'\[.*?\]',  # Anything in brackets
        r'\(.*?\)',  # Anything in parentheses  
        r'CUT TO:?.*',
        r'FADE IN:?.*',
        r'FADE OUT:?.*',
        r'VOICE OVER:?.*',
        r'V\.O\..*',
        r'ON SCREEN:?.*',
        r'GRAPHICS:?.*',
        r'LOWER THIRD:?.*',
        r'B-ROLL:?.*',
        r'SOT:?.*',  # Sound on tape
        r'NAT SOUND:?.*',
        r'LIVE SHOT:?.*',
        r'STANDUP:?.*',
        r'PACKAGE:?.*',
        r'TEASE:?.*',
        r'ANCHOR:?.*',
        r'REPORTER:?.*',
    ]
    
    for phrase_pattern in production_phrases:
        text = re.sub(phrase_pattern, '', text, flags=re.IGNORECASE)
    
    return text

def normalize_numbers_and_time(text):
    """Normalize numbers and time expressions for Filipino TTS"""
    # Convert 12-hour time format to Filipino words
    text = re.sub(r'(\d{1,2}):(\d{2})\s*(AM|PM)', 
                  lambda m: f"{m.group(1)}:{m.group(2)} {FILIPINO_TEXT_PROCESSING['replacements'].get(m.group(3), m.group(3))}", 
                  text, flags=re.IGNORECASE)
    
    # Convert large numbers to more readable format
    text = re.sub(r'\b(\d{1,3}),(\d{3})\b', r'\1 libo at \2', text)  # Thousands
    text = re.sub(r'\b(\d+),(\d{3}),(\d{3})\b', r'\1 milyon \2 libo at \3', text)  # Millions
    
    return text

def process_filipino_script(text):
    """
    Main function to process and clean Filipino scripts for better TTS pronunciation
    """
    print(f"Processing script text...")
    
    # Step 1: Remove production notes and TV directions
    text = remove_production_notes(text)
    print(f"  - Removed production notes")
    
    # Step 2: Clean special characters
    text = clean_special_characters(text)
    print(f"  - Cleaned special characters")
    
    # Step 3: Apply Filipino-specific replacements
    text = apply_filipino_replacements(text)
    print(f"  - Applied Filipino replacements")
    
    # Step 4: Apply spell-out replacements
    text = apply_spell_out_replacements(text)
    print(f"  - Applied spell-out replacements")
    
    # Step 5: Improve address formatting
    text = improve_address_formatting(text)
    print(f"  - Improved address formatting")
    
    # Step 6: Normalize numbers and time
    text = normalize_numbers_and_time(text)
    print(f"  - Normalized numbers and time")
    
    # Step 7: Clean punctuation (do this last)
    text = clean_punctuation(text)
    print(f"  - Cleaned punctuation")
    
    print(f"Script processing complete")
    return text

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
    
    # Process the script for Filipino TTS if language is Filipino and USE_REPLACEMENTS is True
    if LANGUAGE.lower() == "filipino" and USE_REPLACEMENTS:
        script = process_filipino_script(script)
        print("Applied Filipino text processing to opening script")
    
    return {
        "segment_type": "opening_greeting",
        "display_name": SEGMENT_TYPES["opening"]["display_name"],
        "display_order": 0,
        "duration": SEGMENT_TYPES["opening"]["default_duration"],
        "script": script
    }

def generate_summary_scripts(news_data, time_info):
    """Generate individual news headline scripts using LLM for each news item"""
    if not news_data:
        return []
    
    summary_scripts = []
    
    # 1. Generate headline opening segment
    print("Generating headline opening...")
    if LANGUAGE.lower() == "filipino":
        opening_script = "Narito ang mga pangunahing balita sa aming bayan."
    else:
        opening_script = "Here are today's top stories from our community."
    
    # Process the opening script for Filipino TTS if language is Filipino and USE_REPLACEMENTS is True
    if LANGUAGE.lower() == "filipino" and USE_REPLACEMENTS:
        opening_script = process_filipino_script(opening_script)
        print("Applied Filipino text processing to headline opening")
    
    summary_opening = {
        "segment_type": "headline_opening",
        "display_name": "News Headline Opening",
        "display_order": 1,
        "duration": 5.0,  # Short opening
        "script": opening_script
    }
    summary_scripts.append(summary_opening)
    
    # 2. Generate individual headline segments
    for i, news_item in enumerate(news_data):
        print(f"Generating headline for news item {i+1}...")
        
        prompt = f"""Create a news HEADLINE TITLE for {STATION_INFO['station_name']} for this specific news item:

News Content: {news_item['news']}

Requirements:
- Language: Write the script in {LANGUAGE}
- Duration: approximately {SEGMENT_TYPES['headline']['default_duration']} seconds per headline
- Create a proper NEWS HEADLINE TITLE like you'd see on TV news
- Think of how CNN, BBC, or GMA News headlines work - short, clear, informative titles
- DO NOT copy snippets from the actual content
- DO NOT include phrases like "Pakiusap sa mga may-ari" or "Alamin kung paano"
- Create a TITLE that summarizes what the story is about
- Local Pulilan perspective when relevant
- Examples of good headline titles:
  * "Stray Dog Recovery Program Launched in Multiple Barangays"  
  * "Women's Agricultural Training Program Success in Peñabatan"
  * "Rainy Season Preparation Tips Released by Weather Bureau"
- DO NOT include opening phrases like "Narito ang mga pangunahing balita" (already handled separately)
- DO NOT include transitions like "Samantala" or "Sa iba pang balita" (keep it clean and direct)
- Start directly with the headline title
- Keep it professional and informative
- IMPORTANT: Generate ONLY the text that the anchor would speak out loud
- Do NOT include video directions, camera cuts, or production notes
- Do NOT use abbreviations (spell out LGU, DOH, PNP, etc.)
- Do NOT use title abbreviations - spell them out: use "Miss" not "Ms.", "Doctor" not "Dr.", "Mister" not "Mr.", "Santo" not "Sto.", etc.
- Do NOT use special characters or symbols
- Use simple, clear punctuation only (periods, commas, question marks, exclamation points)
- When mentioning addresses, use natural conversational format (not robotic like GPS/Waze)
- Write numbers and dates in word form when possible
- Output should be ready for text-to-speech conversion
- Keep it brief and title-like - this is a HEADLINE TITLE, not content

Script (anchor headline TITLE only in {LANGUAGE}, professional news title format, no opening phrases or transitions, no abbreviations, spell out all titles):"""

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
            print(f"Generated headline script for news item {i+1} using LLM")
            
        except Exception as e:
            print(f"Error generating headline script for news item {i+1}: {e}")
            # Fallback to simple template
            script = news_item['news'][:150] + ("..." if len(news_item['news']) > 150 else "")
        
        # Process the script for Filipino TTS if language is Filipino and USE_REPLACEMENTS is True
        if LANGUAGE.lower() == "filipino" and USE_REPLACEMENTS:
            script = process_filipino_script(script)
            print(f"Applied Filipino text processing to headline script {i+1}")
        
        summary_script = {
            "segment_type": "headline",
            "display_name": f"News Headline {i+1}",
            "display_order": i + 2,  # After opening (0) and headline_opening (1)
            "duration": SEGMENT_TYPES["headline"]["default_duration"],
            "script": script
        }
        
        summary_scripts.append(summary_script)
    
    return summary_scripts

def generate_news_scripts(news_data, time_info):
    """Generate individual news story scripts and headlines using LLM"""
    news_scripts = []
    
    for i, news_item in enumerate(news_data):
        print(f"Generating headline and script for news item {i+1}...")
        
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
        
        # First, generate the headline
        headline_prompt = f"""Create a news HEADLINE for {STATION_INFO['station_name']} for this specific news item:

News Content: {news_item['news']}

Requirements:
- Language: Write the headline in {LANGUAGE}
- Create a proper NEWS HEADLINE like you'd see on TV news
- Think of how CNN, BBC, or GMA News headlines work - short, clear, informative titles
- DO NOT copy snippets from the actual content
- DO NOT include phrases like "Pakiusap sa mga may-ari" or "Alamin kung paano"
- Create a TITLE that summarizes what the story is about
- Local Pulilan, Bulacan perspective when relevant
- Examples of good headline titles:
  * "Stray Dog Recovery Program Launched in Multiple Barangays"  
  * "Women's Agricultural Training Program Success in Peñabatan"
  * "Rainy Season Preparation Tips Released by Weather Bureau"
- Start directly with the headline title
- Keep it professional and informative
- IMPORTANT: Generate ONLY the headline text that would appear on screen
- Do NOT use abbreviations (spell out LGU, DOH, PNP, etc.)
- Do NOT use title abbreviations - spell them out: use "Miss" not "Ms.", "Doctor" not "Dr.", "Mister" not "Mr.", "Santo" not "Sto.", etc.
- Do NOT use special characters or symbols
- Use simple, clear punctuation only
- Keep it brief and title-like - this is a HEADLINE, not content

Headline (in {LANGUAGE}, professional news headline format, no abbreviations, spell out all titles):"""

        headline = ""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=[
                    {"role": "system", "content": LLM_CONFIG["system_prompt"]},
                    {"role": "user", "content": headline_prompt}
                ],
                temperature=LLM_CONFIG["temperature"],
                max_tokens=LLM_CONFIG["max_tokens"]
            )
            
            headline = response.choices[0].message.content.strip()
            print(f"Generated headline for news item {i+1} using LLM")
            
        except Exception as e:
            print(f"Error generating headline for news item {i+1}: {e}")
            # Fallback to simple template
            headline = news_item['news'][:100] + ("..." if len(news_item['news']) > 100 else "")
        
        # Process the headline for Filipino TTS if language is Filipino and USE_REPLACEMENTS is True
        if LANGUAGE.lower() == "filipino" and USE_REPLACEMENTS:
            headline = process_filipino_script(headline)
            print(f"Applied Filipino text processing to headline {i+1}")
        
        # Now generate the script
        script_prompt = f"""Create a news story script for {STATION_INFO['station_name']} based on this news content:

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
- Do NOT use abbreviations (spell out LGU, DOH, PNP, etc.)
- Do NOT use title abbreviations - spell them out: use "Miss" not "Ms.", "Doctor" not "Dr.", "Mister" not "Mr.", "Santo" not "Sto.", etc.
- Do NOT use special characters or symbols
- Use simple, clear punctuation only (periods, commas, question marks, exclamation points)
- When mentioning addresses, use natural conversational format (not robotic like GPS/Waze)
- Write numbers and dates in word form when possible
- Output should be ready for text-to-speech conversion

Script (anchor speech only in {LANGUAGE}, no greeting, smooth transition, no abbreviations, spell out all titles):"""

        script = ""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=[
                    {"role": "system", "content": LLM_CONFIG["system_prompt"]},
                    {"role": "user", "content": script_prompt}
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
        
        # Process the script for Filipino TTS if language is Filipino and USE_REPLACEMENTS is True
        if LANGUAGE.lower() == "filipino" and USE_REPLACEMENTS:
            script = process_filipino_script(script)
            print(f"Applied Filipino text processing to news script {i+1}")
        
        news_script = {
            "segment_type": "news",
            "display_name": f"News Story {i+1}",
            "display_order": i + 100,  # After opening, headline_opening, and headlines, using 100+ to ensure they come after all headlines
            "duration": SEGMENT_TYPES["news"]["default_duration"],
            "headline": headline,
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
    
    # Process the script for Filipino TTS if language is Filipino and USE_REPLACEMENTS is True
    if LANGUAGE.lower() == "filipino" and USE_REPLACEMENTS:
        script = process_filipino_script(script)
        print("Applied Filipino text processing to closing script")
    
    return {
        "segment_type": "closing_remarks",
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
    
    # 2. News summaries (if there are news items)
    if news_data:
        print("Generating news summaries...")
        summaries = generate_summary_scripts(news_data, time_info)
        scripts.extend(summaries)
    
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
    
    # Display headline
    print("\nGenerated segments:")
    for script in scripts:
        print(f"  - {script['display_name']}: {script['duration']}s")

if __name__ == "__main__":
    main() 
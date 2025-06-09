# Nexcaster News Report Generator

A simple Flask application for generating professional TV news reports from uploaded content and media.

## Features

- **Step 1**: Web interface for uploading news content with images, videos, and links
- **Step 2**: AI-powered script generation using LLM
- **Step 3**: Text-to-speech audio generation with accurate duration measurement
- **Step 4**: Media mapping to news manifest for video generation

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API Key** (for script generation)
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Run the Flask Application**
   ```bash
   python app.py
   ```

4. **Open in Browser**
   Navigate to `http://localhost:5000`

## Usage

### Step 1: Upload News Content

1. Open the web interface at `http://localhost:5000`
2. Enter news context in the text area
3. Upload media files (images/videos) - optional
4. Add media links - optional
5. Click "Upload News Content"

The data will be saved to `generated/news_data.json` and media files to `media/`

### Step 2: Generate Scripts

Run the script generator to create news scripts from uploaded content:

```bash
python step2_generate_scripts.py
```

This will:
- Read from `generated/news_data.json`
- Generate professional news scripts using LLM
- Save results to `generated/news_scripts.json`

### Step 3: Generate Audio

Run the TTS generator to create audio files from news scripts:

```bash
python step3_tts_generator.py
```

This will:
- Read from `generated/news_scripts.json`
- Generate audio files using Google Cloud TTS or OpenAI TTS
- Measure actual audio durations (not estimates)
- Combine individual segments into a complete audio file
- Save audio files to `generated/audio/` and metadata to `generated/audio_metadata.json`

### Step 4: Update Manifest with Media

Run the manifest updater to map media to news segments:

```bash
python step4_update_manifest.py
```

This will:
- Read from `generated/news_data.json` and `generated/news_manifest.json`
- Map `intro.mp4` to opening greeting
- Map `outro.mp4` to closing remarks
- Add summary images to news summary segment
- Map corresponding media to each news story
- Save updated manifest to `generated/news_manifest.json`

## File Structure

```
nexcaster-news.v1/
├── app.py                     # Main Flask application
├── config.py                  # Configuration settings
├── step2_generate_scripts.py  # Script generation
├── step3_tts_generator.py     # TTS audio generation with duration measurement
├── step4_update_manifest.py   # Media mapping to news manifest
├── templates/
│   └── index.html            # Web interface
├── media/                    # Uploaded media files
└── generated/                # Generated content
    ├── news_data.json        # Uploaded news content
    ├── news_scripts.json     # Generated scripts
    ├── news_manifest.json    # Complete news manifest with media
    ├── audio_metadata.json   # Audio files metadata with accurate durations
    └── audio/                # Generated audio files
        ├── opening_greeting.mp3
        ├── news_summary.mp3
        ├── news1.mp3, news2.mp3, news3.mp3
        ├── closing_remarks.mp3
        └── combined.mp3      # Complete combined audio
```

## Configuration

Edit `config.py` to customize:

- **Segment Types**: Opening, summary, news, closing
- **Station Information**: Location, name, anchor
- **LLM Settings**: Model, temperature, prompts
- **TTS Settings**: Voice, speed, format, service selection (Google Cloud/OpenAI)
- **Audio Settings**: Speaking rate, pitch, duration measurement

## Data Formats

### News Data Format (`news_data.json`)
```json
[
  {
    "news": "News context and details",
    "media": [
      {"image": "filename.jpg"},
      {"video": "filename.mp4"},
      {"link": "https://example.com/image.jpg"}
    ],
    "timestamp": "2025-01-03T10:30:00"
  }
]
```

### Audio Metadata Format (`audio_metadata.json`)
```json
{
  "individual_segments": [
    {
      "segment_name": "opening_greeting",
      "display_name": "Opening Greeting",
      "audio_file": "opening_greeting.mp3",
      "audio_path": "generated/audio/opening_greeting.mp3",
      "script": "Magandang umaga, Pulilan!...",
      "duration": 16.248,
      "language": "Filipino",
      "voice_used": "en-US-Chirp3-HD-Achernar",
      "tts_service": "Google Cloud"
    }
  ],
  "combined_audio": {
    "combined_file": "combined.mp3",
    "total_duration": 197.84,
    "segment_count": 6
  }
}
```

### News Manifest Format (`news_manifest.json`)
```json
{
  "individual_segments": [
    {
      "segment_name": "opening_greeting",
      "display_name": "Opening Greeting",
      "audio_file": "opening_greeting.mp3",
      "duration": 16.248,
      "script": "Magandang umaga, Pulilan!...",
      "media": [
        {
          "video": "intro.mp4",
          "path": "media/intro.mp4",
          "type": "intro_video"
        }
      ]
    }
  ]
}
```

### News Scripts Format (`news_scripts.json`)
```json
[
  {
    "segment_name": "opening_greeting",
    "display_name": "Opening Greeting",
    "display_order": 0,
    "duration": 15.0,
    "script": "Good morning, Pulilan! It's 10:30 AM..."
  }
]
```

## Development

The application includes comprehensive logging to trace data flow. Check the console output when running each step to monitor progress and troubleshoot issues.

### Current Implementation Status

- ✅ **Step 1**: Complete - Web upload interface
- ✅ **Step 2**: Complete - Script generation with LLM
- ✅ **Step 3**: Complete - TTS audio generation with accurate duration measurement
- ✅ **Step 4**: Complete - Media mapping to news manifest

### Recent Updates

#### v1.2 - Audio Duration Fix & Media Mapping
- **Fixed**: Step 3 now measures actual audio file durations instead of using estimates
- **Enhanced**: TTS generator shows real-time duration comparison (estimated vs actual)
- **Improved**: Combined audio duration includes accurate gap/pause calculations
- **Renamed**: `step4_subtitle_generator.py` → `step4_update_manifest.py`
- **Simplified**: Step 4 now focuses on media mapping rather than subtitle generation
- **Added**: Automatic mapping of intro/outro videos to opening/closing segments
- **Added**: Smart summary image selection from news stories
- **Added**: Complete media assignment for each news segment

## Notes

- This implementation provides a complete workflow from content upload to media-mapped manifest
- All generated content is saved in JSON format for easy processing
- The web interface provides a modern, responsive design for easy use
- Audio durations are measured from actual generated files for precision
- Media mapping automatically organizes content for video generation pipeline

## Required Media Files

The system expects the following files in the `media/` directory:
- `intro.mp4` - Opening video for news greeting
- `outro.mp4` - Closing video for news ending
- Uploaded images and videos from news content upload

## API Keys Required

- **OpenAI API Key**: For script generation (Step 2) and optionally TTS (Step 3)
- **Google Cloud Credentials**: For Google Cloud TTS (Step 3) - set `TTS_USE = "GOOGLE"` in config.py 
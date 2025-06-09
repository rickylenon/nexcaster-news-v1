# Nexcaster News Report Generator

A simple Flask application for generating professional TV news reports from uploaded content and media.

## Features

- **Step 1**: Web interface for uploading news content with images, videos, and links
- **Step 2**: AI-powered script generation using LLM
- **Step 3**: Text-to-speech audio generation (placeholder)
- **Step 4**: Subtitle generation with precise timing (placeholder)

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

### Step 3: Generate Audio (Placeholder)

```bash
python step3_tts_generator.py
```

### Step 4: Generate Subtitles (Placeholder)

```bash
python step4_subtitle_generator.py
```

## File Structure

```
nexcaster-news.v1/
├── app.py                     # Main Flask application
├── config.py                  # Configuration settings
├── step2_generate_scripts.py  # Script generation
├── step3_tts_generator.py     # TTS audio generation (placeholder)
├── step4_subtitle_generator.py # Subtitle generation (placeholder)
├── templates/
│   └── index.html            # Web interface
├── media/                    # Uploaded media files
└── generated/                # Generated content
    ├── news_data.json        # Uploaded news content
    ├── news_scripts.json     # Generated scripts
    ├── audio/                # Generated audio files
    └── subtitle_data.json    # Generated subtitles
```

## Configuration

Edit `config.py` to customize:

- **Segment Types**: Opening, summary, news, closing
- **Station Information**: Location, name, anchor
- **LLM Settings**: Model, temperature, prompts
- **TTS Settings**: Voice, speed, format
- **Subtitle Settings**: Timing parameters

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
- 🚧 **Step 3**: Placeholder - TTS generation framework
- 🚧 **Step 4**: Placeholder - Subtitle generation framework

## Notes

- This is a basic implementation focused on the core workflow
- Steps 3 and 4 are placeholder implementations that provide the framework for future development
- All generated content is saved in JSON format for easy processing
- The web interface provides a modern, responsive design for easy use 
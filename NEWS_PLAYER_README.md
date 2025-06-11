# Nexcaster News Media Player

A sophisticated media player for synchronized news presentation with multimedia content, based on the Nexcaster Weather Player architecture.

## Features

### 🎬 Media Synchronization
- **Synchronized Playback**: Audio, video, and images synchronized to news segments
- **Timeline Control**: Seek to any point in the news broadcast
- **Automatic Switching**: Media automatically switches based on news segments
- **Smooth Transitions**: Seamless transitions between different media types

### 📺 Media Support
- **Audio**: MP3 files for news narration and segments
- **Video**: MP4/WebM for intro/outro and news videos
- **Images**: JPG/PNG for news photos and graphics
- **Combined Audio**: Single audio track with all news segments

### 🎛️ Player Controls
- **Play/Pause/Stop**: Standard media controls
- **Volume Control**: Independent volume for news audio, video audio, and master volume
- **Timeline Scrubbing**: Click anywhere on the timeline to jump to that time
- **Segment Navigation**: Click on any news segment to jump directly to it

### 📋 News Segments Display
- **Opening Greeting**: Welcome message with intro video
- **News Summary**: Overview of all news items with images
- **Individual News Stories**: Detailed news segments with associated media
- **Closing Remarks**: Farewell message with outro video

### 🐛 Debug Features
- **Debug Console**: Real-time logging of player operations
- **Status Indicators**: Visual status for manifest, audio, and media loading
- **Performance Monitoring**: Timeline sync and media switching diagnostics

## Usage

### Starting the Server
```bash
python app.py
```

The server will start on `http://localhost:5001` with the following endpoints:

- **News Upload Interface**: `http://localhost:5001/`
- **News Media Player**: `http://localhost:5001/player`
- **API Health Check**: `http://localhost:5001/api/health`
- **News Manifest**: `http://localhost:5001/api/news/manifest`

### Using the Media Player

1. **Access the Player**: Navigate to `http://localhost:5001/player`
2. **Wait for Loading**: The player will automatically load the news manifest
3. **Check Status**: Verify all status indicators show "Ready"
4. **Start Playback**: Click the "Play" button
5. **Navigate**: Use timeline or click on segments in the playlist

### Player Interface

#### Main Components
- **Media Stage**: Central area displaying videos and images
- **Playlist Panel**: Right sidebar showing all news segments
- **Control Panel**: Bottom area with play controls and timeline
- **Volume Controls**: Audio level controls for different tracks
- **Debug Panel**: Optional debug information (toggle with Debug button)

#### Controls
- **▶️ Play**: Start or resume playback
- **⏸️ Pause**: Pause playback (can be resumed)
- **⏹️ Stop**: Stop and reset to beginning
- **🔄 Reload**: Reload the news manifest
- **🐛 Debug**: Toggle debug console

#### Volume Controls
- **🎵 News Audio**: Volume for news narration and segments
- **🎬 Video Audio**: Volume for video content (intro/outro)
- **🔊 Master**: Overall volume control

## Data Structure

### News Manifest
The player expects a news manifest at `generated/news_manifest.json`:

```json
{
  "individual_segments": [
    {
      "segment_type": "opening_greeting",
      "display_name": "Opening Greeting",
      "audio_file": "opening_greeting.mp3",
      "audio_path": "generated/audio/opening_greeting.mp3",
      "script": "News intro script...",
      "duration": 15.456,
      "language": "Filipino",
      "media": [
        {
          "video": "intro.mp4",
          "path": "media/intro.mp4",
          "type": "intro_video"
        }
      ]
    }
  ],
  "combined_audio": {
    "combined_file": "combined.mp3",
    "combined_path": "generated/audio/combined.mp3",
    "total_duration": 195.32
  }
}
```

### File Structure
```
nexcaster-news.v1/
├── app.py                          # Flask application
├── news_player.html               # Media player interface
├── generated/
│   ├── news_manifest.json         # News segments and timing
│   └── audio/
│       ├── combined.mp3           # Main audio track
│       ├── opening_greeting.mp3   # Individual segments
│       ├── news_summary.mp3
│       └── ...
└── media/
    ├── intro.mp4                  # Intro video
    ├── outro.mp4                  # Outro video
    └── [news-images].jpg          # News photos
```

## API Endpoints

### GET /player
Serves the news media player HTML interface.

### GET /api/news/manifest
Returns the news manifest with timing and media information.

**Response:**
```json
{
  "individual_segments": [...],
  "combined_audio": {...},
  "generation_info": {...},
  "api_metadata": {
    "served_at": "2025-06-09T14:09:42.731355",
    "server": "Nexcaster News API v1.0"
  }
}
```

### GET /api/health
Health check endpoint showing system status.

**Response:**
```json
{
  "status": "healthy",
  "news_items": 3,
  "manifest_available": true,
  "audio_files": 7,
  "media_files": 8,
  "endpoints": {...}
}
```

### GET /generated/<filename>
Serves generated files (audio, manifest) from the `generated/` directory.

### GET /media/<filename>
Serves media files (images, videos) from the `media/` directory.

## Technical Implementation

### Media Synchronization
- Uses `performance.now()` for high-precision timing
- Synchronizes all media to a master timeline based on the combined audio track
- Handles pause/resume with timeline correction
- Automatic sync correction every 500ms to prevent drift

### Segment Management
- Calculates segment start/end times from audio durations
- Activates/deactivates media based on current timeline position
- Prioritizes visual media (videos/images) over audio-only segments
- Smooth transitions between different media types

### Audio Architecture
- **Main Audio**: Combined MP3 with all news segments
- **Segment Audio**: Individual segment audio files (for future use)
- **Video Audio**: Audio tracks from video files
- **Volume Mixing**: Independent volume controls with master volume

### Error Handling
- Graceful fallback when media files are missing
- Automatic retry for failed media loads
- User-friendly error messages
- Debug logging for troubleshooting

## Browser Compatibility

### Supported Browsers
- **Chrome/Chromium**: Recommended (best performance)
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support

### Required Features
- HTML5 Audio/Video
- ES6 JavaScript (async/await, classes)
- CSS Grid and Flexbox
- RequestAnimationFrame API

## Troubleshooting

### Common Issues

**1. Player won't load**
- Check if `generated/news_manifest.json` exists
- Verify the Flask server is running on port 5001
- Check browser console for errors

**2. Audio doesn't play**
- Ensure audio files exist in `generated/audio/`
- Check file permissions
- Verify audio files are not corrupted

**3. Media doesn't display**
- Check if media files exist in `media/` directory
- Verify file paths in the manifest are correct
- Check browser console for 404 errors

**4. Sync issues**
- Enable debug mode to monitor sync performance
- Check if audio files have correct durations
- Verify manifest timing calculations

### Debug Mode
Enable debug mode by clicking the "🐛 Debug" button to see:
- Real-time sync information
- Media activation/deactivation events
- Timeline position updates
- Error messages and warnings

## Development Notes

### Based on Weather Player
This news media player is adapted from the Nexcaster Weather Media Player, with modifications for:
- News segment structure instead of weather subtitles
- Image display for news photos
- Simplified audio architecture (no background music)
- News-specific styling and branding

### Future Enhancements
- Live streaming support
- Multi-language subtitle support
- Social media integration
- Analytics and viewing metrics
- Mobile-responsive design improvements

## License

Part of the Nexcaster News application suite. 
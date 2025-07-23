import os
import json
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'media'
GENERATED_FOLDER = 'generated'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'avi', 'mov', 'webm', 'mkv', 'flv'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max total upload size

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_news_data():
    """Load existing news data from JSON file"""
    news_data_path = os.path.join(GENERATED_FOLDER, 'news_data.json')
    if os.path.exists(news_data_path):
        with open(news_data_path, 'r') as f:
            return json.load(f)
    return []

def save_news_data(data):
    """Save news data to JSON file"""
    news_data_path = os.path.join(GENERATED_FOLDER, 'news_data.json')
    with open(news_data_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"News data saved to {news_data_path}")

@app.route('/')
def index():
    """Main page to upload news content"""
    news_data = load_news_data()
    print(f"Loaded {len(news_data)} news items")
    return render_template('index.html', news_data=news_data)

@app.route('/upload', methods=['POST'])
def upload_news():
    """Handle news upload with media files"""
    print("Received upload request")
    
    news_context = request.form.get('news_context')
    if not news_context:
        flash('Please provide news context', 'error')
        return redirect(url_for('index'))
    
    print(f"News context: {news_context}")
    
    # Handle uploaded files
    media_files = []
    files = request.files.getlist('media_files')
    upload_results = {
        'successful_uploads': 0,
        'failed_uploads': 0,
        'images': 0,
        'videos': 0,
        'failed_files': []
    }
    
    print(f"Processing {len(files)} uploaded files...")
    
    for i, file in enumerate(files):
        if file and file.filename != '':
            print(f"Processing file {i+1}/{len(files)}: {file.filename}")
            
            # Check file extension
            if not allowed_file(file.filename):
                upload_results['failed_uploads'] += 1
                upload_results['failed_files'].append(f"{file.filename} (unsupported format)")
                print(f"Skipped unsupported file: {file.filename}")
                continue
            
            # Check file size (limit per file: 50MB)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit per file
                upload_results['failed_uploads'] += 1
                upload_results['failed_files'].append(f"{file.filename} (file too large)")
                print(f"Skipped large file: {file.filename} ({file_size / (1024*1024):.1f}MB)")
                continue
            
            try:
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save file
                file.save(file_path)
                
                # Determine media type and get file info
                ext = filename.rsplit('.', 1)[1].lower()
                file_info = {
                    "original_name": filename,
                    "size": file_size,
                    "size_mb": round(file_size / (1024*1024), 2)
                }
                
                if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}:
                    media_files.append({
                        "image": unique_filename,
                        **file_info
                    })
                    upload_results['images'] += 1
                    print(f"Saved image: {unique_filename} ({file_info['size_mb']}MB)")
                    
                elif ext in {'mp4', 'avi', 'mov', 'webm', 'mkv', 'flv'}:
                    media_files.append({
                        "video": unique_filename,
                        **file_info
                    })
                    upload_results['videos'] += 1
                    print(f"Saved video: {unique_filename} ({file_info['size_mb']}MB)")
                
                upload_results['successful_uploads'] += 1
                
            except Exception as e:
                upload_results['failed_uploads'] += 1
                upload_results['failed_files'].append(f"{file.filename} (upload error)")
                print(f"Error uploading {file.filename}: {e}")
    
    # Handle links
    links = request.form.getlist('links')
    for link in links:
        if link.strip():
            media_files.append({"link": link.strip()})
            print(f"Added link: {link.strip()}")
    
    # Create news item
    news_item = {
        "news": news_context,
        "media": media_files,
        "timestamp": datetime.now().isoformat(),
        "upload_summary": upload_results
    }
    
    # Load existing data and append new item
    news_data = load_news_data()
    news_data.append(news_item)
    save_news_data(news_data)
    
    # Generate success/error messages
    if upload_results['successful_uploads'] > 0:
        success_msg = f"News item uploaded successfully! "
        success_msg += f"Processed {upload_results['successful_uploads']} files: "
        success_msg += f"{upload_results['images']} images, {upload_results['videos']} videos"
        flash(success_msg, 'success')
        print(f"Upload successful: {success_msg}")
    
    if upload_results['failed_uploads'] > 0:
        error_msg = f"Failed to upload {upload_results['failed_uploads']} files: "
        error_msg += ", ".join(upload_results['failed_files'])
        flash(error_msg, 'error')
        print(f"Upload errors: {error_msg}")
    
    print(f"News item added successfully. Total items: {len(news_data)}")
    return redirect(url_for('index'))

@app.route('/api/news-data')
def get_news_data():
    """API endpoint to get news data"""
    news_data = load_news_data()
    return jsonify(news_data)

@app.route('/media/<filename>')
def serve_media(filename):
    """Serve uploaded media files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete-news/<int:index>', methods=['POST'])
def delete_news(index):
    """Delete a news item by index"""
    news_data = load_news_data()
    if 0 <= index < len(news_data):
        deleted_item = news_data.pop(index)
        save_news_data(news_data)
        
        # Clean up media files
        for media in deleted_item.get('media', []):
            if 'image' in media:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], media['image'])
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted media file: {media['image']}")
            elif 'video' in media:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], media['video'])
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted media file: {media['video']}")
        
        flash('News item deleted successfully!', 'success')
        print(f"Deleted news item at index {index}")
    else:
        flash('Invalid news item index', 'error')
    
    return redirect(url_for('index'))

@app.route('/update-news/<int:index>', methods=['POST'])
def update_news(index):
    """Update a news item by index"""
    print(f"Received update request for news item {index}")
    
    try:
        news_data = load_news_data()
        if index < 0 or index >= len(news_data):
            return jsonify({'success': False, 'error': 'Invalid news item index'}), 400
        
        # Get updated content
        news_content = request.form.get('news_content')
        if not news_content or not news_content.strip():
            return jsonify({'success': False, 'error': 'News content cannot be empty'}), 400
        
        # Update the news content
        news_data[index]['news'] = news_content.strip()
        
        # Handle media updates (links)
        updated_links = request.form.getlist('updated_links')
        if updated_links:
            # Remove existing links and add updated ones
            existing_media = news_data[index].get('media', [])
            non_link_media = [m for m in existing_media if 'link' not in m]
            
            # Add updated links
            for link in updated_links:
                if link.strip():
                    non_link_media.append({"link": link.strip()})
            
            news_data[index]['media'] = non_link_media
        
        # Handle media file deletions
        deleted_media = request.form.getlist('deleted_media')
        if deleted_media:
            existing_media = news_data[index].get('media', [])
            for media_id in deleted_media:
                # Find and remove media item
                for media in existing_media[:]:  # Use slice copy to safely modify during iteration
                    if (media.get('image') == media_id or 
                        media.get('video') == media_id):
                        # Delete physical file
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], media_id)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Deleted media file: {media_id}")
                        existing_media.remove(media)
                        break
            
            news_data[index]['media'] = existing_media
        
        # Handle new file uploads
        new_files = request.files.getlist('new_media_files')
        if new_files:
            existing_media = news_data[index].get('media', [])
            
            for file in new_files:
                if file and file.filename != '':
                    if not allowed_file(file.filename):
                        continue
                    
                    # Check file size
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size > 50 * 1024 * 1024:  # 50MB limit
                        continue
                    
                    try:
                        # Generate unique filename
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        
                        # Save file
                        file.save(file_path)
                        
                        # Add to media list
                        ext = filename.rsplit('.', 1)[1].lower()
                        file_info = {
                            "original_name": filename,
                            "size": file_size,
                            "size_mb": round(file_size / (1024*1024), 2)
                        }
                        
                        if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}:
                            existing_media.append({
                                "image": unique_filename,
                                **file_info
                            })
                        elif ext in {'mp4', 'avi', 'mov', 'webm', 'mkv', 'flv'}:
                            existing_media.append({
                                "video": unique_filename,
                                **file_info
                            })
                        
                        print(f"Added new media file: {unique_filename}")
                    except Exception as e:
                        print(f"Error uploading new file {file.filename}: {e}")
            
            news_data[index]['media'] = existing_media
        
        # Update timestamp
        news_data[index]['last_updated'] = datetime.now().isoformat()
        
        # Save updated data
        save_news_data(news_data)
        
        print(f"Updated news item {index} successfully")
        return jsonify({'success': True, 'message': 'News item updated successfully'})
        
    except Exception as e:
        print(f"Error updating news item {index}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete-media/<int:news_index>/<media_filename>', methods=['POST'])
def delete_media(news_index, media_filename):
    """Delete a specific media file from a news item"""
    try:
        news_data = load_news_data()
        if news_index < 0 or news_index >= len(news_data):
            return jsonify({'success': False, 'error': 'Invalid news item index'}), 400
        
        # Find and remove the media file
        media_list = news_data[news_index].get('media', [])
        media_removed = False
        
        for media in media_list[:]:  # Use slice copy to safely modify during iteration
            if media.get('image') == media_filename or media.get('video') == media_filename:
                # Delete physical file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], media_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted media file: {media_filename}")
                
                # Remove from media list
                media_list.remove(media)
                media_removed = True
                break
        
        if not media_removed:
            return jsonify({'success': False, 'error': 'Media file not found'}), 404
        
        # Update news data
        news_data[news_index]['media'] = media_list
        news_data[news_index]['last_updated'] = datetime.now().isoformat()
        save_news_data(news_data)
        
        return jsonify({'success': True, 'message': 'Media file deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting media file {media_filename}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/player')
@app.route('/player/')
def news_player():
    """Serve the news media player interface"""
    try:
        # Check if news_player.html exists
        if os.path.exists('news_player.html'):
            print("📺 Serving news media player interface")
            return send_from_directory('.', 'news_player.html')
        else:
            print("❌ news_player.html file not found")
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>News Media Player - File Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #dc3545; }
                    .info { color: #007bff; margin-top: 20px; }
                </style>
            </head>
            <body>
                <h1 class="error">⚠️ News Media Player Not Found</h1>
                <p>The news_player.html file is missing.</p>
                <div class="info">
                    <h3>Available Endpoints:</h3>
                    <p><a href="/">News Upload Interface</a></p>
                    <p><a href="/api/news-data">News Data API</a></p>
                    <p><a href="/api/news/manifest">News Manifest API</a></p>
                </div>
            </body>
            </html>
            """), 404
    except Exception as e:
        print(f"❌ Error serving news media player: {str(e)}")
        return jsonify({'error': 'Failed to serve news media player interface'}), 500

@app.route('/api/news/manifest')
def get_news_manifest():
    """API endpoint to get news manifest for media player"""
    try:
        manifest_path = os.path.join(GENERATED_FOLDER, 'news_manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Check for anchor videos and add them to segments
            anchor_dir = os.path.join(GENERATED_FOLDER, 'anchor')
            anchor_videos = {}
            if os.path.exists(anchor_dir):
                for filename in os.listdir(anchor_dir):
                    if filename.endswith('.mp4'):
                        # Extract base name without extension
                        base_name = filename[:-4]  # Remove .mp4
                        anchor_videos[base_name] = {
                            'video': filename,
                            'path': f'/generated/anchor/{filename}',
                            'type': 'anchor_video'
                        }
            
            # Add anchor videos to segments
            segments = manifest.get('individual_segments', [])
            for segment in segments:
                audio_file = segment.get('audio_file', '')
                if audio_file:
                    # Remove .mp3 extension to match anchor video names
                    base_audio_name = audio_file[:-4] if audio_file.endswith('.mp3') else audio_file
                    if base_audio_name in anchor_videos:
                        # Add anchor video to segment media
                        if 'media' not in segment:
                            segment['media'] = []
                        segment['media'].append(anchor_videos[base_audio_name])
                        print(f"✅ Added anchor video for segment: {segment.get('display_name', 'Unknown')}")
            
            # Add API metadata
            manifest['api_metadata'] = {
                'served_at': datetime.now().isoformat(),
                'server': 'Nexcaster News API v1.0',
                'endpoint': '/api/news/manifest',
                'anchor_videos_found': len(anchor_videos)
            }
            
            segment_types = {}
            for segment in segments:
                segment_type = segment.get('segment_type', 'unknown')
                if segment_type == 'headline_opening':
                    segment_types['headline_opening'] = segment_types.get('headline_opening', 0) + 1
                elif segment_type == 'headline':
                    segment_types['headlines'] = segment_types.get('headlines', 0) + 1
                elif segment_type == 'news':
                    segment_types['news_stories'] = segment_types.get('news_stories', 0) + 1
                elif segment_type in ['opening_greeting', 'closing_remarks']:
                    segment_types['greetings'] = segment_types.get('greetings', 0) + 1
                else:
                    segment_types['other'] = segment_types.get('other', 0) + 1
            
            print(f"✅ Served news manifest with {len(segments)} segments:")
            for segment_type, count in segment_types.items():
                print(f"   - {segment_type}: {count}")
            print(f"🎬 Found {len(anchor_videos)} anchor videos")
            
            return jsonify(manifest)
        else:
            print("❌ News manifest not found")
            return jsonify({
                'error': 'News manifest not found',
                'message': 'Run TTS generation to create the manifest',
                'timestamp': datetime.now().isoformat()
            }), 404
    except Exception as e:
        print(f"❌ Error getting news manifest: {e}")
        return jsonify({
            'error': 'Failed to load news manifest',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for news application"""
    try:
        news_data = load_news_data()
        manifest_exists = os.path.exists(os.path.join(GENERATED_FOLDER, 'news_manifest.json'))
        audio_dir_exists = os.path.exists(os.path.join(GENERATED_FOLDER, 'audio'))
        
        # Count audio files
        audio_files = 0
        if audio_dir_exists:
            audio_files = len([f for f in os.listdir(os.path.join(GENERATED_FOLDER, 'audio')) 
                             if f.endswith('.mp3')])
        
        # Count media files
        media_files = len([f for f in os.listdir(UPLOAD_FOLDER) 
                          if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))])
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'server': 'Nexcaster News API v1.0',
            'news_items': len(news_data),
            'manifest_available': manifest_exists,
            'audio_files': audio_files,
            'media_files': media_files,
            'directories': {
                'upload_folder': UPLOAD_FOLDER,
                'generated_folder': GENERATED_FOLDER,
                'audio_folder': os.path.join(GENERATED_FOLDER, 'audio')
            },
            'endpoints': {
                'news_upload': url_for('index', _external=True),
                'news_player': url_for('news_player', _external=True),
                'news_data': url_for('get_news_data', _external=True),
                'news_manifest': url_for('get_news_manifest', _external=True),
                'health_check': url_for('health_check', _external=True)
            }
        })
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/generated/<path:filename>')
def serve_generated_files(filename):
    """Serve generated files (audio, manifest, etc.)"""
    try:
        print(f"📁 Serving generated file: {filename}")
        return send_from_directory(GENERATED_FOLDER, filename)
    except Exception as e:
        print(f"❌ Error serving generated file {filename}: {e}")
        return jsonify({
            'error': f'File "{filename}" not found',
            'timestamp': datetime.now().isoformat()
        }), 404

@app.route('/weather/generated/audio/<path:filename>')
def serve_weather_audio(filename):
    print(f"[DEBUG] Serving weather audio: {filename}")
    return send_from_directory('weather/generated/audio', filename)

@app.route('/weather/generated/<path:filename>')
def serve_weather_generated(filename):
    print(f"[DEBUG] Serving weather generated file: {filename}")
    return send_from_directory('weather/generated', filename)

@app.route('/weather/generated/media/<path:filename>')
def serve_weather_media(filename):
    print(f"[DEBUG] Serving weather media: {filename}")
    return send_from_directory('weather/generated/media', filename)

if __name__ == '__main__':
    print("🚀 Starting Nexcaster News App...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Generated folder: {GENERATED_FOLDER}")
    print("🌐 Server will be available at: http://localhost:5001")
    print("📝 Upload news content and generate audio at: http://localhost:5001/")
    print("📺 News Media Player at: http://localhost:5001/player")
    print("📊 API Endpoints:")
    print("   GET /api/news-data        - News data")
    print("   GET /api/news/manifest    - News manifest for player")
    print("   GET /api/health           - Health check")
    print("   GET /generated/<file>     - Generated audio/manifest files")
    print("   GET /media/<file>         - Media files (images/videos)")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 
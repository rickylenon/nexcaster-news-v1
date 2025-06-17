#!/usr/bin/env python3
"""
Nexcaster Weather Cards Application

Professional Flask application serving weather data API and interactive weather cards.
Combines weather data scraping, API endpoints, and video-ready weather card visualization.

Usage:
    python app.py
    flask run
    gunicorn app:app

Endpoints:
    GET /                          - Weather cards HTML interface
    GET /api/weather/latest        - Latest weather data
    GET /api/weather/list          - List all weather files
    GET /api/weather/<filename>    - Specific weather data file
    GET /api/health                - Health check
    GET /test                      - API test page
    GET /media/<path:filename>     - Serve multimedia files (json, webm, mp4, png, jpg)
    GET /files/<path:filename>     - Serve data files

Features:
    - Professional Flask application structure
    - CORS-enabled API endpoints
    - Real-time weather data from enhanced MSN scraping
    - Interactive weather cards with Chart.js visualizations
    - Video recording optimized (500x600px cards)
    - Navigation support (keyboard/mouse)
    - Comprehensive error handling and logging
    - Static file serving for multimedia content
"""

from flask import Flask, jsonify, render_template_string, request, send_file, send_from_directory, url_for, redirect, abort
from flask_cors import CORS
import os
import json
import glob
from datetime import datetime
import logging
from pathlib import Path
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
class Config:
    DATA_DIR = 'generated'
    MULTIMEDIA_DIR = os.path.join('generated', 'media')
    AUDIO_DIR = os.path.join('generated', 'audio')
    WEATHER_DATA_PATTERNS = [
        'weather_data.json',
        'weather_manifest.json',
        'weather_scripts.json'
    ]
    # Allowed file extensions for serving
    ALLOWED_EXTENSIONS = {
        'json': 'application/json',
        'webm': 'video/webm',
        'mp4': 'video/mp4',
        'mp3': 'audio/mpeg',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg'
    }
    HOST = '0.0.0.0'
    PORT = 5002
    DEBUG = True

app.config.from_object(Config)

def is_safe_path(basedir, path, follow_symlinks=True):
    """Check if a path is safe (prevents directory traversal attacks)"""
    if follow_symlinks:
        matchpath = os.path.realpath(path)
        basedir = os.path.realpath(basedir)
    else:
        matchpath = os.path.abspath(path)
        basedir = os.path.abspath(basedir)
    return basedir == os.path.commonpath([basedir, matchpath])

def get_file_extension(filename):
    """Get file extension safely"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def find_weather_files():
    """Find all weather data files in the generated directory"""
    weather_files = []
    
    # Check for weather data files in the generated directory
    for pattern in app.config['WEATHER_DATA_PATTERNS']:
        file_path = os.path.join(app.config['DATA_DIR'], pattern)
        if os.path.exists(file_path):
            rel_path = os.path.relpath(file_path, app.config['DATA_DIR'])
            weather_files.append({
                'filename': os.path.basename(file_path),
                'path': rel_path,
                'full_path': file_path,
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    # Sort by modification time (newest first)
    weather_files.sort(key=lambda x: x['modified'], reverse=True)
    
    logger.info(f"Found {len(weather_files)} weather data files")
    return weather_files

def load_weather_data(file_path):
    """Load and validate weather data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add API metadata
        data['api_metadata'] = {
            'served_at': datetime.now().isoformat(),
            'filename': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'server': 'Nexcaster Weather API v2.0'
        }
        
        logger.info(f"Successfully loaded weather data from {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading weather data from {file_path}: {str(e)}")
        raise

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the weather cards HTML interface"""
    try:
        # Check if a card parameter is provided
        card_param = request.args.get('card')
        
        # If no card parameter, redirect to current card
        if not card_param:
            return redirect(url_for('index', card='current'))
        
        # Check if weather_cards.html exists
        if os.path.exists('weather_cards.html'):
            return send_file('weather_cards.html')
        else:
            # Return a simple error page if file doesn't exist
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Weather Cards - File Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #dc3545; }
                    .info { color: #007bff; margin-top: 20px; }
                </style>
            </head>
            <body>
                <h1 class="error">⚠️ Weather Cards Not Found</h1>
                <p>The weather_cards.html file is missing.</p>
                <div class="info">
                    <h3>Available API Endpoints:</h3>
                    <p><a href="/api/health">Health Check</a></p>
                    <p><a href="/api/weather/list">Weather Files List</a></p>
                    <p><a href="/api/weather/latest">Latest Weather Data</a></p>
                    <p><a href="/test">API Test Page</a></p>
                </div>
            </body>
            </html>
            """), 404
    except Exception as e:
        logger.error(f"Error serving weather cards: {str(e)}")
        return jsonify({'error': 'Failed to serve weather cards interface'}), 500

@app.route('/test')
def test_page():
    """Serve the API test page"""
    try:
        if os.path.exists('test_weather_cards.html'):
            return send_file('test_weather_cards.html')
        else:
            # Generate a simple test page
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Nexcaster Weather API Test</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .endpoint a { color: #007bff; text-decoration: none; }
                    .endpoint a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>🌤️ Nexcaster Weather API Test</h1>
                <div class="endpoint">
                    <h3>Health Check</h3>
                    <a href="/api/health" target="_blank">GET /api/health</a>
                </div>
                <div class="endpoint">
                    <h3>Weather Files List</h3>
                    <a href="/api/weather/list" target="_blank">GET /api/weather/list</a>
                </div>
                <div class="endpoint">
                    <h3>Latest Weather Data</h3>
                    <a href="/api/weather/latest" target="_blank">GET /api/weather/latest</a>
                </div>
                <div class="endpoint">
                    <h3>Weather Manifest</h3>
                    <a href="/api/weather/manifest" target="_blank">GET /api/weather/manifest</a>
                </div>
                <div class="endpoint">
                    <h3>Weather Cards Interface</h3>
                    <a href="/" target="_blank">GET / (Weather Cards)</a>
                </div>
                <div class="endpoint">
                    <h3>Weather Media Player</h3>
                    <a href="/player" target="_blank">GET /player (Media Player)</a>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving test page: {str(e)}")
        return jsonify({'error': 'Failed to serve test page'}), 500

@app.route('/player')
def weather_player():
    """Serve the weather media player interface"""
    try:
        # Check if weather_player.html exists
        if os.path.exists('weather_player.html'):
            logger.info("Serving weather media player interface")
            return send_file('weather_player.html')
        else:
            logger.error("weather_player.html file not found")
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Weather Media Player - File Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #dc3545; }
                    .info { color: #007bff; margin-top: 20px; }
                </style>
            </head>
            <body>
                <h1 class="error">⚠️ Weather Media Player Not Found</h1>
                <p>The weather_player.html file is missing.</p>
                <div class="info">
                    <h3>Available Endpoints:</h3>
                    <p><a href="/">Weather Cards Interface</a></p>
                    <p><a href="/test">API Test Page</a></p>
                    <p><a href="/api/health">Health Check</a></p>
                </div>
            </body>
            </html>
            """), 404
    except Exception as e:
        logger.error(f"Error serving weather media player: {str(e)}")
        return jsonify({'error': 'Failed to serve weather media player interface'}), 500

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/health')
def api_health():
    """Health check endpoint with server status and configuration"""
    try:
        files = find_weather_files()
        
        # Check multimedia directories
        multimedia_dirs = []
        for dir_path in [app.config['MULTIMEDIA_DIR'], app.config.get('AUDIO_DIR')]:
            if dir_path and os.path.exists(dir_path):
                multimedia_dirs.append({
                    'path': dir_path,
                    'exists': True,
                    'files': len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                })
            else:
                multimedia_dirs.append({
                    'path': dir_path,
                    'exists': False,
                    'files': 0
                })
        
        # Check for weather_manifest.json
        manifest_file = os.path.join(app.config['DATA_DIR'], 'weather_manifest.json')
        manifest_available = os.path.exists(manifest_file)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'server': 'Nexcaster Weather API v2.0',
            'data_directory': app.config['DATA_DIR'],
            'multimedia_directories': multimedia_dirs,
            'available_files': len(files),
            'latest_file': files[0]['filename'] if files else None,
            'manifest_available': manifest_available,
            'supported_file_types': list(app.config['ALLOWED_EXTENSIONS'].keys()),
            'endpoints': {
                'weather_cards': url_for('index', _external=True),
                'weather_player': url_for('weather_player', _external=True),
                'latest_weather': url_for('api_weather_latest', _external=True),
                'weather_list': url_for('api_weather_list', _external=True),
                'weather_manifest': url_for('api_weather_manifest', _external=True),
                'media_list': url_for('list_media_files', _external=True),
                'test_page': url_for('test_page', _external=True)
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/weather/list')
def api_weather_list():
    """List all available weather data files"""
    try:
        files = find_weather_files()
        return jsonify({
            'status': 'success',
            'count': len(files),
            'files': files,
            'server': 'Nexcaster Weather API v2.0',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error listing weather files: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/weather/latest')
def api_weather_latest():
    """Get the most recent weather data file"""
    try:
        files = find_weather_files()
        if not files:
            return jsonify({
                'status': 'error',
                'error': 'No weather data files found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        latest_file = files[0]  # Already sorted by modification time
        data = load_weather_data(latest_file['full_path'])
        
        return jsonify({
            'status': 'success',
            'file_info': latest_file,
            'data': data,
            'server': 'Nexcaster Weather API v2.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting latest weather data: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/weather/<filename>')
def api_weather_file(filename):
    """Get specific weather data file"""
    try:
        # Find the file
        files = find_weather_files()
        target_file = None
        
        for file_info in files:
            if file_info['filename'] == filename:
                target_file = file_info
                break
        
        if not target_file:
            return jsonify({
                'status': 'error',
                'error': f'Weather data file "{filename}" not found',
                'available_files': [f['filename'] for f in files[:5]],
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Load and return the data
        data = load_weather_data(target_file['full_path'])
        
        return jsonify({
            'status': 'success',
            'file_info': target_file,
            'data': data,
            'server': 'Nexcaster Weather API v2.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting weather data for {filename}: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/weather/manifest')
def api_weather_manifest():
    """Get the weather media manifest with subtitle timing"""
    try:
        manifest_file = os.path.join(app.config['DATA_DIR'], 'weather_manifest.json')
        
        if not os.path.exists(manifest_file):
            return jsonify({
                'status': 'error',
                'error': 'Weather manifest not found',
                'message': 'Generate weather manifest to create the file',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # Add API metadata
        manifest_data['api_metadata'] = {
            'served_at': datetime.now().isoformat(),
            'file_size': os.path.getsize(manifest_file),
            'server': 'Nexcaster Weather API v2.0'
        }
        
        return jsonify({
            'status': 'success',
            'manifest': manifest_data,
            'server': 'Nexcaster Weather API v2.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting weather manifest: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ============================================================================
# MULTIMEDIA & FILE SERVING ROUTES
# ============================================================================

@app.route('/data/<path:filename>')
def serve_data_direct(filename):
    """Serve files directly from the data directory with /data/ prefix"""
    try:
        print(f"[DATA_SERVE] Requested file: /data/{filename}")
        
        # Get file extension
        ext = get_file_extension(filename)
        if ext not in app.config['ALLOWED_EXTENSIONS']:
            print(f"[DATA_SERVE] ❌ File extension '{ext}' not allowed")
            return jsonify({
                'error': f'File type .{ext} not supported',
                'allowed_types': list(app.config['ALLOWED_EXTENSIONS'].keys()),
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Construct full file path
        file_path = os.path.join(app.config['DATA_DIR'], filename)
        
        # Security check
        if not is_safe_path(app.config['DATA_DIR'], file_path):
            print(f"[DATA_SERVE] ⚠️ Unsafe path detected: {file_path}")
            return jsonify({
                'error': 'Invalid file path',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if not os.path.isfile(file_path):
            print(f"[DATA_SERVE] ❌ File not found: {file_path}")
            return jsonify({
                'error': f'File "/data/{filename}" not found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Set proper content type
        mimetype = app.config['ALLOWED_EXTENSIONS'].get(ext, 'application/octet-stream')
        
        print(f"[DATA_SERVE] ✅ Serving: {file_path} as {mimetype}")
        return send_file(file_path, mimetype=mimetype)
        
    except Exception as e:
        logger.error(f"Error serving data file /data/{filename}: {str(e)}")
        print(f"[DATA_SERVE] ❌ Error: {str(e)}")
        return jsonify({
            'error': 'Failed to serve data file',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/media/<path:filename>')
def serve_multimedia(filename):
    """Serve multimedia files (json, webm, mp4, png, jpg) from multimedia directories"""
    try:
        print(f"[MEDIA_SERVE] Requested file: {filename}")
        
        # Get file extension
        ext = get_file_extension(filename)
        if ext not in app.config['ALLOWED_EXTENSIONS']:
            print(f"[MEDIA_SERVE] ❌ File extension '{ext}' not allowed")
            return jsonify({
                'error': f'File type .{ext} not supported',
                'allowed_types': list(app.config['ALLOWED_EXTENSIONS'].keys()),
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Search in multimedia directories
        search_dirs = [
            app.config['MULTIMEDIA_DIR'],
            app.config.get('AUDIO_DIR', os.path.join(app.config['DATA_DIR'], 'audio')),
            app.config['DATA_DIR']
        ]
        
        file_found = None
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            file_path = os.path.join(search_dir, filename)
            print(f"[MEDIA_SERVE] Checking: {file_path}")
            
            # Security check
            if not is_safe_path(search_dir, file_path):
                print(f"[MEDIA_SERVE] ⚠️ Unsafe path detected: {file_path}")
                continue
                
            if os.path.isfile(file_path):
                file_found = file_path
                print(f"[MEDIA_SERVE] ✅ Found file: {file_path}")
                break
        
        if not file_found:
            print(f"[MEDIA_SERVE] ❌ File not found: {filename}")
            return jsonify({
                'error': f'File "{filename}" not found',
                'searched_directories': [d for d in search_dirs if os.path.exists(d)],
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Set proper content type
        mimetype = app.config['ALLOWED_EXTENSIONS'].get(ext, 'application/octet-stream')
        
        print(f"[MEDIA_SERVE] 📤 Serving: {file_found} as {mimetype}")
        return send_file(file_found, mimetype=mimetype)
        
    except Exception as e:
        logger.error(f"Error serving multimedia file {filename}: {str(e)}")
        print(f"[MEDIA_SERVE] ❌ Error: {str(e)}")
        return jsonify({
            'error': 'Failed to serve multimedia file',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/files/<path:filename>')
def serve_data_files(filename):
    """Serve data files from the data directory"""
    try:
        print(f"[FILE_SERVE] Requested file: {filename}")
        
        # Get file extension
        ext = get_file_extension(filename)
        if ext not in app.config['ALLOWED_EXTENSIONS']:
            print(f"[FILE_SERVE] ❌ File extension '{ext}' not allowed")
            return jsonify({
                'error': f'File type .{ext} not supported',
                'allowed_types': list(app.config['ALLOWED_EXTENSIONS'].keys()),
                'timestamp': datetime.now().isoformat()
            }), 400
        
        file_path = os.path.join(app.config['DATA_DIR'], filename)
        
        # Security check
        if not is_safe_path(app.config['DATA_DIR'], file_path):
            print(f"[FILE_SERVE] ⚠️ Unsafe path detected: {file_path}")
            return jsonify({
                'error': 'Invalid file path',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if not os.path.isfile(file_path):
            print(f"[FILE_SERVE] ❌ File not found: {file_path}")
            return jsonify({
                'error': f'File "{filename}" not found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Set proper content type
        mimetype = app.config['ALLOWED_EXTENSIONS'].get(ext, 'application/octet-stream')
        
        print(f"[FILE_SERVE] 📤 Serving: {file_path} as {mimetype}")
        return send_file(file_path, mimetype=mimetype)
        
    except Exception as e:
        logger.error(f"Error serving data file {filename}: {str(e)}")
        print(f"[FILE_SERVE] ❌ Error: {str(e)}")
        return jsonify({
            'error': 'Failed to serve data file',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/media/list')
def list_media_files():
    """List all available media files"""
    try:
        print("[MEDIA_LIST] Scanning for media files...")
        
        media_files = []
        
        # Search directories
        search_dirs = [
            app.config['MULTIMEDIA_DIR'],
            app.config.get('AUDIO_DIR', os.path.join(app.config['DATA_DIR'], 'audio')),
            app.config['DATA_DIR']
        ]
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            print(f"[MEDIA_LIST] Scanning directory: {search_dir}")
            
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    ext = get_file_extension(file)
                    if ext in app.config['ALLOWED_EXTENSIONS']:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, search_dir)
                        
                        # Generate URL paths
                        if search_dir == app.config['MULTIMEDIA_DIR'] or search_dir == app.config.get('AUDIO_DIR'):
                            url_path = f"/media/{file}"  # Direct file access for generated structure
                        else:
                            url_path = f"/media/{rel_path}"
                        
                        media_files.append({
                            'filename': file,
                            'path': rel_path,
                            'full_path': file_path,
                            'url': url_path,
                            'type': ext,
                            'mimetype': app.config['ALLOWED_EXTENSIONS'][ext],
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                            'directory': search_dir
                        })
        
        # Sort by modification time (newest first)
        media_files.sort(key=lambda x: x['modified'], reverse=True)
        
        print(f"[MEDIA_LIST] Found {len(media_files)} media files")
        
        return jsonify({
            'status': 'success',
            'count': len(media_files),
            'files': media_files,
            'file_types': list(app.config['ALLOWED_EXTENSIONS'].keys()),
            'server': 'Nexcaster Weather API v2.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listing media files: {str(e)}")
        print(f"[MEDIA_LIST] ❌ Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with helpful information"""
    return jsonify({
        'status': 'error',
        'error': 'Endpoint not found',
        'available_endpoints': {
            'weather_cards': '/',
            'weather_player': '/player',
            'api_health': '/api/health',
            'api_weather_list': '/api/weather/list',
            'api_weather_latest': '/api/weather/latest',
            'api_weather_file': '/api/weather/<filename>',
            'api_media_list': '/api/media/list',
            'serve_data_direct': '/data/<path:filename>',
            'serve_multimedia': '/media/<path:filename>',
            'serve_data_files': '/files/<path:filename>',
            'test_page': '/test'
        },
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

def initialize_app():
    """Initialize the application and check requirements"""
    print("🌤️  Nexcaster Weather Cards Application")
    print("=" * 60)
    print(f"📁 Data Directory: {os.path.abspath(app.config['DATA_DIR'])}")
    
    # Check if data directory exists
    if not os.path.exists(app.config['DATA_DIR']):
        print(f"⚠️  Warning: Data directory '{app.config['DATA_DIR']}' does not exist")
        os.makedirs(app.config['DATA_DIR'], exist_ok=True)
        print(f"✅ Created data directory: {app.config['DATA_DIR']}")
    
    # Check and create multimedia directories
    for dir_path in [app.config['MULTIMEDIA_DIR'], app.config.get('AUDIO_DIR')]:
        if dir_path:
            if not os.path.exists(dir_path):
                print(f"⚠️  Warning: Directory '{dir_path}' does not exist")
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            else:
                print(f"📁 Directory: {os.path.abspath(dir_path)}")
    
    # Check for weather cards HTML
    if os.path.exists('weather_cards.html'):
        print("✅ Weather cards HTML found")
    else:
        print("⚠️  Warning: weather_cards.html not found")
    
    # List available files
    files = find_weather_files()
    print(f"📊 Found {len(files)} weather data files")
    
    if files:
        print("\n📋 Available Weather Files:")
        for i, file_info in enumerate(files[:5]):  # Show first 5 files
            print(f"   {i+1}. {file_info['filename']} ({file_info['modified']})")
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more files")
    
    # Display supported file types
    print(f"\n🎬 Supported Media Types: {', '.join(app.config['ALLOWED_EXTENSIONS'].keys())}")
    
    print("\n🚀 Starting Nexcaster Weather Application...")
    print("📡 Available Endpoints:")
    print("   GET /                           - Weather cards interface")
    print("   GET /player                     - Weather media player")
    print("   GET /api/health                 - Health check & status")
    print("   GET /api/weather/list          - List all weather files")
    print("   GET /api/weather/latest        - Get latest weather data")
    print("   GET /api/weather/<filename>    - Get specific weather file")
    print("   GET /api/weather/manifest      - Get weather manifest")
    print("   GET /api/media/list            - List all media files")
    print("   GET /data/<path:filename>      - Serve data files directly")
    print("   GET /media/<path:filename>     - Serve multimedia files (json,webm,mp4,mp3,png,jpg)")
    print("   GET /files/<path:filename>     - Serve data files")
    print("   GET /test                      - API test page")
    print(f"\n🌐 Server will be available at: http://localhost:{app.config['PORT']}")
    print(f"🎬 Weather Cards: http://localhost:{app.config['PORT']}/?data=api/weather/latest")
    print(f"🎭 Media Player: http://localhost:{app.config['PORT']}/player")
    print(f"🧪 Test Interface: http://localhost:{app.config['PORT']}/test")
    print(f"📁 Media Files List: http://localhost:{app.config['PORT']}/api/media/list")
    print(f"📋 Weather Manifest: http://localhost:{app.config['PORT']}/api/weather/manifest")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    initialize_app()
    
    # Run the Flask app
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        use_reloader=False  # Disable reloader to avoid duplicate startup messages
    ) 
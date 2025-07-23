#!/usr/bin/env python3
"""
Wav2Lip Quality Enhancer - Post-process Wav2Lip output for better quality
Applies sharpening, color correction, and high-quality encoding
"""

import cv2
import numpy as np
import argparse
import subprocess
import os
from pathlib import Path
import tempfile

def parse_args():
    parser = argparse.ArgumentParser(description='Enhance Wav2Lip output video quality')
    parser.add_argument('--input', type=str, required=True, help='Input video file from Wav2Lip')
    parser.add_argument('--output', type=str, required=True, help='Enhanced output video file')
    parser.add_argument('--sharpen_strength', type=float, default=0.5, help='Sharpening strength (0.0-2.0)')
    parser.add_argument('--contrast_factor', type=float, default=1.1, help='Contrast enhancement factor')
    parser.add_argument('--brightness', type=int, default=5, help='Brightness adjustment (-50 to 50)')
    parser.add_argument('--denoise', action='store_true', help='Apply noise reduction')
    parser.add_argument('--crf', type=int, default=18, help='Video quality (lower = better, 18-28)')
    parser.add_argument('--preset', type=str, default='slow', help='Encoding preset (ultrafast, fast, medium, slow, veryslow)')
    return parser.parse_args()

def apply_sharpening(frame, strength=0.5):
    """Apply unsharp mask sharpening"""
    # Create gaussian blur
    gaussian = cv2.GaussianBlur(frame, (0, 0), 2.0)
    
    # Apply unsharp mask
    sharpened = cv2.addWeighted(frame, 1.0 + strength, gaussian, -strength, 0)
    
    return np.clip(sharpened, 0, 255).astype(np.uint8)

def apply_contrast_brightness(frame, contrast=1.1, brightness=5):
    """Apply contrast and brightness adjustments"""
    # Convert to float for better precision
    frame_float = frame.astype(np.float32)
    
    # Apply contrast and brightness
    enhanced = frame_float * contrast + brightness
    
    return np.clip(enhanced, 0, 255).astype(np.uint8)

def apply_noise_reduction(frame):
    """Apply light noise reduction"""
    # Use bilateral filter for noise reduction while preserving edges
    denoised = cv2.bilateralFilter(frame, 9, 75, 75)
    return denoised

def enhance_face_region(frame, enhancement_factor=1.2):
    """Apply subtle enhancement to detected face regions"""
    # Simple face detection for enhancement
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    enhanced_frame = frame.copy()
    
    for (x, y, w, h) in faces:
        # Extract face region
        face_region = frame[y:y+h, x:x+w]
        
        # Apply subtle enhancement
        enhanced_face = apply_contrast_brightness(face_region, enhancement_factor, 2)
        enhanced_face = apply_sharpening(enhanced_face, 0.3)
        
        # Blend back into frame
        enhanced_frame[y:y+h, x:x+w] = enhanced_face
    
    return enhanced_frame

def process_video(input_path, output_path, args):
    """Process video with quality enhancements"""
    print(f"📹 Processing video: {input_path}")
    
    # Open video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {input_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video specs: {width}x{height} @ {fps}fps, {total_frames} frames")
    
    # Create temporary output for processed video
    temp_dir = tempfile.mkdtemp()
    temp_video = os.path.join(temp_dir, 'enhanced_temp.mp4')
    
    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Apply enhancements
            enhanced_frame = frame.copy()
            
            # Face region enhancement
            enhanced_frame = enhance_face_region(enhanced_frame)
            
            # Global contrast and brightness
            enhanced_frame = apply_contrast_brightness(
                enhanced_frame, 
                args.contrast_factor, 
                args.brightness
            )
            
            # Sharpening
            if args.sharpen_strength > 0:
                enhanced_frame = apply_sharpening(enhanced_frame, args.sharpen_strength)
            
            # Noise reduction
            if args.denoise:
                enhanced_frame = apply_noise_reduction(enhanced_frame)
            
            out.write(enhanced_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"🎬 Processed {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")
        
        print(f"✅ Processing complete: {frame_count} frames processed")
        
    finally:
        cap.release()
        out.release()
    
    # Extract audio from original video
    print("🎵 Extracting audio...")
    temp_audio = os.path.join(temp_dir, 'audio.aac')
    audio_cmd = [
        'ffmpeg', '-y', '-i', input_path, 
        '-vn', '-acodec', 'copy', temp_audio
    ]
    subprocess.run(audio_cmd, capture_output=True)
    
    # Combine enhanced video with original audio using high-quality encoding
    print("🎯 Final encoding with high quality...")
    final_cmd = [
        'ffmpeg', '-y',
        '-i', temp_video,
        '-i', temp_audio,
        '-c:v', 'libx264',
        '-crf', str(args.crf),
        '-preset', args.preset,
        '-c:a', 'aac',
        '-b:a', '192k',
        '-movflags', '+faststart',  # Better streaming
        output_path
    ]
    
    result = subprocess.run(final_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ FFmpeg error: {result.stderr}")
        raise RuntimeError("Failed to encode final video")
    
    # Cleanup
    try:
        os.remove(temp_video)
        os.remove(temp_audio)
        os.rmdir(temp_dir)
    except:
        pass
    
    print(f"🎉 Enhanced video saved to: {output_path}")

def main():
    args = parse_args()
    
    # Validate input
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print("🚀 Wav2Lip Quality Enhancer")
    print(f"🔧 Settings:")
    print(f"   - Sharpening: {args.sharpen_strength}")
    print(f"   - Contrast: {args.contrast_factor}")
    print(f"   - Brightness: {args.brightness}")
    print(f"   - Denoise: {args.denoise}")
    print(f"   - CRF: {args.crf}")
    print(f"   - Preset: {args.preset}")
    print()
    
    # Process video
    process_video(args.input, args.output, args)

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Wav2Lip Best Quality Pipeline
Runs Wav2Lip with optimal settings and applies post-processing for maximum quality
"""

import os
import subprocess
import argparse
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Run Wav2Lip with best quality settings')
    parser.add_argument('--face', type=str, required=True, help='Input video file')
    parser.add_argument('--audio', type=str, required=True, help='Input audio file')
    parser.add_argument('--output', type=str, required=True, help='Final output video file')
    parser.add_argument('--checkpoint_path', type=str, default='checkpoints/wav2lip.pth', help='Wav2Lip checkpoint path')
    
    # Wav2Lip parameters
    parser.add_argument('--resize_factor', type=int, default=1, help='Resize factor (1=no resize, 2=half size)')
    parser.add_argument('--chunk_size', type=int, default=25, help='Chunk size for processing')
    parser.add_argument('--wav2lip_batch_size', type=int, default=8, help='Wav2Lip batch size')
    
    # Quality enhancement parameters
    parser.add_argument('--sharpen_strength', type=float, default=0.6, help='Sharpening strength')
    parser.add_argument('--contrast_factor', type=float, default=1.15, help='Contrast factor')
    parser.add_argument('--brightness', type=int, default=8, help='Brightness adjustment')
    parser.add_argument('--crf', type=int, default=16, help='Video quality (lower=better)')
    parser.add_argument('--preset', type=str, default='slow', help='Encoding preset')
    
    # Skip enhancement option
    parser.add_argument('--skip_enhancement', action='store_true', help='Skip post-processing enhancement')
    
    return parser.parse_args()

def check_requirements():
    """Check if required files and dependencies exist"""
    required_files = [
        'wav2lip_test/Wav2Lip/inference_chunked.py',
        'wav2lip_quality_enhancer.py'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            return False
    
    return True

def run_wav2lip(args):
    """Run Wav2Lip with optimal settings"""
    print("🎬 Running Wav2Lip with optimal settings...")
    
    # Create intermediate output path
    intermediate_output = args.output.replace('.mp4', '_raw.mp4')
    
    # Construct Wav2Lip command
    wav2lip_cmd = [
        'python', 'wav2lip_test/Wav2Lip/inference_chunked.py',
        '--checkpoint_path', args.checkpoint_path,
        '--face', args.face,
        '--audio', args.audio,
        '--outfile', intermediate_output,
        '--wav2lip_batch_size', str(args.wav2lip_batch_size),
        '--resize_factor', str(args.resize_factor),
        '--chunk_size', str(args.chunk_size)
    ]
    
    print(f"🚀 Command: {' '.join(wav2lip_cmd)}")
    
    # Run Wav2Lip
    result = subprocess.run(wav2lip_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Wav2Lip failed with error:")
        print(result.stderr)
        return False, None
    
    print(f"✅ Wav2Lip completed successfully")
    return True, intermediate_output

def run_quality_enhancement(input_path, output_path, args):
    """Run quality enhancement post-processing"""
    print("✨ Applying quality enhancement...")
    
    # Construct enhancement command
    enhance_cmd = [
        'python', 'wav2lip_quality_enhancer.py',
        '--input', input_path,
        '--output', output_path,
        '--sharpen_strength', str(args.sharpen_strength),
        '--contrast_factor', str(args.contrast_factor),
        '--brightness', str(args.brightness),
        '--denoise',
        '--crf', str(args.crf),
        '--preset', args.preset
    ]
    
    print(f"🚀 Enhancement command: {' '.join(enhance_cmd)}")
    
    # Run enhancement
    result = subprocess.run(enhance_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Quality enhancement failed:")
        print(result.stderr)
        return False
    
    print(f"✅ Quality enhancement completed")
    return True

def main():
    args = parse_args()
    
    print("🎯 Wav2Lip Best Quality Pipeline")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Validate inputs
    if not os.path.exists(args.face):
        print(f"❌ Face video not found: {args.face}")
        sys.exit(1)
    
    if not os.path.exists(args.audio):
        print(f"❌ Audio file not found: {args.audio}")
        sys.exit(1)
    
    if not os.path.exists(args.checkpoint_path):
        print(f"❌ Checkpoint not found: {args.checkpoint_path}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"📹 Input video: {args.face}")
    print(f"🎵 Input audio: {args.audio}")
    print(f"🎬 Output video: {args.output}")
    print(f"🔧 Settings:")
    print(f"   - Resize factor: {args.resize_factor}")
    print(f"   - Chunk size: {args.chunk_size}")
    print(f"   - Batch size: {args.wav2lip_batch_size}")
    if not args.skip_enhancement:
        print(f"   - Sharpening: {args.sharpen_strength}")
        print(f"   - Contrast: {args.contrast_factor}")
        print(f"   - Brightness: {args.brightness}")
        print(f"   - CRF: {args.crf}")
        print(f"   - Preset: {args.preset}")
    print()
    
    # Step 1: Run Wav2Lip
    success, intermediate_path = run_wav2lip(args)
    if not success:
        sys.exit(1)
    
    # Step 2: Apply quality enhancement (unless skipped)
    if args.skip_enhancement:
        # Just rename the intermediate file
        os.rename(intermediate_path, args.output)
        print(f"✅ Raw Wav2Lip output saved to: {args.output}")
    else:
        success = run_quality_enhancement(intermediate_path, args.output, args)
        if not success:
            sys.exit(1)
        
        # Clean up intermediate file
        try:
            os.remove(intermediate_path)
        except:
            pass
    
    print()
    print("🎉 Best Quality Pipeline Complete!")
    print(f"📁 Final output: {args.output}")
    
    # Show file size
    if os.path.exists(args.output):
        file_size = os.path.getsize(args.output) / (1024 * 1024)  # MB
        print(f"📊 File size: {file_size:.1f} MB")

if __name__ == '__main__':
    main() 
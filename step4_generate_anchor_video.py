'''
python step4_generate_anchor_video.py --face test_video_newscaster.mp4 --checkpoint_path checkpoints/wav2lip.pth

python step4_generate_anchor_video.py --face test_video_newscaster.mp4 --checkpoint_path checkpoints/wav2lip.pth --max_workers 4
python step4_generate_anchor_video.py --face test_video_newscaster.mp4 --checkpoint_path checkpoints/wav2lip.pth --max_workers 8

python step4_generate_anchor_video.py --face test_video_newscaster.mp4 --checkpoint_path checkpoints/wav2lip.pth --max_workers 8 --exclude opening_greeting_1,opening_greeting_1
python step4_generate_anchor_video.py --face test_video_newscaster.mp4 --checkpoint_path checkpoints/wav2lip.pth --max_workers 8 --exclude opening_greeting_1

ps aux | grep inference_chunked.py
pkill -f inference_chunked.py
'''

import os
import glob
import subprocess
import argparse
import concurrent.futures

PYTHON_EXEC = '/Users/rickylenon/PROJECTX/nexcaster-news.v1/venv/bin/python'

def process_audio(mp3_path, args):
    audio_basename = os.path.splitext(os.path.basename(mp3_path))[0]
    if args.exclude and audio_basename in args.exclude:
        print(f"[EXCLUDE] {audio_basename}.mp3 is in exclude list, skipping.")
        return
    mp4_path = os.path.join('generated/anchor', f"{audio_basename}.mp4")
    if os.path.exists(mp4_path):
        print(f"[SKIP] {mp4_path} already exists.")
        return
    print(f"[START] Processing: {mp3_path} -> {mp4_path}")
    cmd = [
        PYTHON_EXEC, 'wav2lip_test/Wav2Lip/inference_chunked.py',
        '--checkpoint_path', args.checkpoint_path,
        '--face', args.face,
        '--audio', mp3_path,
        '--wav2lip_batch_size', str(args.wav2lip_batch_size),
        '--resize_factor', str(args.resize_factor),
        '--chunk_size', str(args.chunk_size)
    ]
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[DONE] {mp3_path} -> {mp4_path}")

def main():
    parser = argparse.ArgumentParser(description='Batch generate anchor videos from mp3s in generated/audio/')
    parser.add_argument('--face', type=str, required=True, help='Path to the face video/image')
    parser.add_argument('--checkpoint_path', type=str, required=True, help='Path to the Wav2Lip checkpoint')
    parser.add_argument('--wav2lip_batch_size', type=int, default=4)
    parser.add_argument('--resize_factor', type=int, default=2)
    parser.add_argument('--chunk_size', type=int, default=25)
    parser.add_argument('--max_workers', type=int, default=None, help='Maximum number of parallel processes (default: number of CPU cores)')
    parser.add_argument('--all', action='store_true', help='Delete all generated/anchor/*.mp4 before processing')
    parser.add_argument('--exclude', type=str, default='', help='Comma-separated list of audio basenames (without .mp3) to exclude')
    args = parser.parse_args()

    # Parse exclude list
    args.exclude = [x.strip() for x in args.exclude.split(',') if x.strip()] if args.exclude else []

    mp4_files = glob.glob('generated/anchor/*.mp4')
    if args.all:
        print(f"[CLEAN] Deleting {len(mp4_files)} mp4 files in generated/anchor/")
        for f in mp4_files:
            try:
                os.remove(f)
                print(f"[DELETED] {f}")
            except Exception as e:
                print(f"[ERROR] Could not delete {f}: {e}")

    mp3_files = glob.glob('generated/audio/*.mp3')
    print(f"Found {len(mp3_files)} mp3 files in generated/audio/")

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(process_audio, mp3, args) for mp3 in mp3_files]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"[ERROR] A process failed: {exc}")

    print("All videos generated.")

if __name__ == '__main__':
    main() 
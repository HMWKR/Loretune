"""Encode actual screencast frames at their recorded elapsed times."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

folder = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
if output.exists():
    raise SystemExit('Refusing to overwrite a prior recording')
record = json.loads((folder / 'recording.json').read_text())
frames = record['frames']
if not frames or record.get('captureError'):
    raise SystemExit('Missing or failed screencast')
start = record['startedAt'] / 1000
end = record['finishedAt'] / 1000
times = [max(start, min(end, f['capturedTimestamp'])) for f in frames]
if any(b < a for a, b in zip(times, times[1:])):
    raise SystemExit('Non-monotonic capture timestamps')
lines = ['ffconcat version 1.0']
for i, frame in enumerate(frames):
    path = folder / frame['filename']
    if hashlib.sha256(path.read_bytes()).hexdigest() != frame['sha256']:
        raise SystemExit('Capture frame changed')
    following = times[i + 1] if i + 1 < len(frames) else end
    beginning = start if i == 0 else times[i]
    duration = max(.001, following - beginning)
    if "'" in str(path):
        raise SystemExit('Unsupported quote in task evidence path')
    lines += [f"file '{path}'", f'duration {duration:.6f}']
lines.append(f"file '{folder / frames[-1]['filename']}'")
listing = folder / 'frames.ffconcat'
listing.write_text('\n'.join(lines) + '\n')
command = ['ffmpeg', '-nostdin', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(listing),
           '-t', str(record['elapsedSeconds']), '-vf', 'fps=24', '-c:v', 'libx264', '-preset', 'fast',
           '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)]
result = subprocess.run(command, capture_output=True, timeout=180)
(folder / 'encode.stderr.log').write_bytes(result.stderr)
if result.returncode:
    raise SystemExit(f'Encoding failed: {result.returncode}')
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)], capture_output=True, check=True)
metadata = json.loads(probe.stdout)
decode = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(output), '-f', 'null', '-'], capture_output=True, timeout=180)
duration = float(metadata['format']['duration'])
if decode.returncode or abs(duration - record['elapsedSeconds']) > 1/24 + .002:
    raise SystemExit('Recording decode or elapsed-time verification failed')
receipt = {'command': command, 'encode_exit_code': result.returncode, 'decode_exit_code': decode.returncode,
           'output': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
           'probe': metadata, 'recorded_elapsed_seconds': record['elapsedSeconds'], 'output_duration': duration,
           'edited': False, 'sped_up': False, 'omitted_intervals': [], 'audio': record['audio'],
           'playback_and_content_review': 'Pending actual browser playback and frame inspection.'}
(folder / 'encode-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'output': str(output), 'duration': duration, 'actual_capture_frames': len(frames), 'decode_exit_code': decode.returncode}))

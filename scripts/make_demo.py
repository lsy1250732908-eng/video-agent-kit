#!/usr/bin/env python3
"""Create a synthetic one-second test clip; no network or AI service."""
import argparse
from pathlib import Path
import shutil
import subprocess
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
a = p.parse_args()
if not a.ffmpeg:
    p.error('FFmpeg is required')
a.output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([a.ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-f', 'lavfi', '-i', 'color=c=blue:s=160x90:r=24', '-t', '1', '-c:v', 'mpeg4', '-pix_fmt', 'yuv420p', str(a.output)], check=True)

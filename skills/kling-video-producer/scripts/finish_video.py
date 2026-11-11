#!/usr/bin/env python3
"""Validate a local downloaded MP4, save without overwrite, and report evidence."""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import struct
from pathlib import Path


def check_boxes(path):
    """Reject truncated top-level MP4 boxes before invoking a decoder."""
    total = path.stat().st_size
    seen = set()
    with path.open('rb') as f:
        pos = 0
        while pos < total:
            f.seek(pos)
            raw = f.read(8)
            if len(raw) != 8:
                raise ValueError('Truncated MP4 box header')
            length, kind = struct.unpack('>I4s', raw)
            minimum = 8
            if length == 1:
                extended = f.read(8)
                if len(extended) != 8:
                    raise ValueError('Truncated extended box header')
                length = struct.unpack('>Q', extended)[0]
                minimum = 16
            elif length == 0:
                length = total - pos
            if length < minimum or pos + length > total:
                raise ValueError('Invalid or truncated MP4 box length')
            seen.add(kind)
            pos += length
    if not {b'ftyp', b'moov', b'mdat'}.issubset(seen):
        raise ValueError('MP4 lacks ftyp/moov/mdat boxes')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    ap.add_argument('--expected-duration', type=float)
    ap.add_argument('--tolerance', type=float, default=0.25)
    args = ap.parse_args()
    src = Path(args.input).resolve()
    out = Path(args.output).absolute()
    report = out.with_suffix('.verification.json')
    if not args.ffmpeg:
        ap.error('FFmpeg unavailable; supply --ffmpeg. No files changed.')
    if not math.isfinite(args.tolerance) or args.tolerance < 0:
        ap.error('tolerance must be finite and nonnegative')
    if args.expected_duration is not None and (not math.isfinite(args.expected_duration) or args.expected_duration <= 0):
        ap.error('expected-duration must be finite and positive')
    if out.suffix.lower() != '.mp4':
        ap.error('output must have .mp4 suffix')
    if not src.is_file():
        ap.error('input is not a file')
    if out.exists() or out.is_symlink() or report.exists() or report.is_symlink():
        ap.error('output/report already exists; choose a new versioned filename')
    with src.open('rb') as f:
        header = f.read(12)
    if len(header) < 12 or header[4:8] != b'ftyp':
        ap.error('input lacks expected MP4 ftyp header; may be HTML/error content')
    check_boxes(src)
    # Explicit video mapping requires a video stream; audio is optional.
    proc = subprocess.run([
        args.ffmpeg, '-hide_banner', '-nostdin', '-v', 'info', '-xerror',
        '-i', str(src), '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'
    ], capture_output=True, text=True, timeout=300)
    if proc.returncode:
        raise RuntimeError('Full decode failed; input preserved, no final video saved:\n' + proc.stderr[-6000:])
    m = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', proc.stderr)
    if not m:
        raise RuntimeError('Could not read container duration; input preserved')
    duration = int(m[1])*3600 + int(m[2])*60 + float(m[3])
    if args.expected_duration is not None and abs(duration-args.expected_duration) > args.tolerance:
        raise RuntimeError('Duration %.3fs differs from requested %.3fs (tolerance %.3fs); input preserved' % (duration,args.expected_duration,args.tolerance))
    evidence = {
        'schema_version': 1, 'output': str(out),
        'container_duration_seconds_reported_by_ffmpeg': duration,
        'duration_precision_note': 'Parsed FFmpeg display; typically rounded to hundredths of a second.',
        'expected_duration_seconds': args.expected_duration,
        'duration_tolerance_seconds': args.tolerance,
        'decode_exit_code': proc.returncode,
        'visual_review': 'Not performed by this script',
        'ffmpeg_diagnostics': proc.stderr,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        digest = hashlib.sha256()
        size = 0
        with out.open('xb') as dst:
            created.append(out)
            with src.open('rb') as inp:
                while True:
                    block = inp.read(1024*1024)
                    if not block:
                        break
                    dst.write(block)
                    digest.update(block)
                    size += len(block)
        evidence.update(file_bytes=size, sha256=digest.hexdigest())
        with report.open('x', encoding='utf-8') as f:
            created.append(report)
            json.dump(evidence, f, ensure_ascii=False, indent=2)
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    print(json.dumps({'video':str(out),'report':str(report),'bytes':size,'sha256':digest.hexdigest(),'duration':duration},ensure_ascii=False))


if __name__ == '__main__':
    main()

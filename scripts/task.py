#!/usr/bin/env python3
"""Local task journal. Never submits, downloads or spends credits."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

NEXT = {
    'prepared': {'submitting'},
    'submitting': {'submitted', 'uncertain'},
    'uncertain': {'submitted', 'prepared'},
    'submitted': {'generating', 'generated', 'failed'},
    'generating': {'generated', 'failed'},
    'generated': {'downloaded'},
    'downloaded': {'verified'},
    'verified': {'delivered'},
    'delivered': set(), 'failed': set(),
}

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def locked(path):
    lock = path.with_name(path.name + '.lock')
    fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()

def save(path, data):
    fd, name = tempfile.mkstemp(prefix='.task-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def resume(data):
    state = data['state']
    if state in ('submitting', 'uncertain'):
        return 'Reconcile provider history. Do not resubmit. Record task ID or evidence of no submission.'
    if state in ('submitted', 'generating'):
        return 'Poll the existing provider task; do not create another.'
    if state == 'generated':
        return 'Download the existing result; do not regenerate.'
    if state == 'downloaded':
        return 'Run finish_video.py and inspect the visible action.'
    if state == 'verified':
        return 'Deliver the saved MP4 using host-supported media rendering.'
    if state == 'delivered':
        return 'Complete. Reuse the saved artifact.'
    if state == 'failed':
        return 'Provider failure recorded. Any new paid attempt needs its own authorized task.'
    return 'Review prompt, references, actual settings and authorization before submission.'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('file', type=Path)
    init.add_argument('--brief', required=True, type=Path)
    step = sub.add_parser('advance')
    step.add_argument('file', type=Path)
    step.add_argument('state', choices=NEXT)
    step.add_argument('--task-id')
    step.add_argument('--evidence', required=True)
    for cmd in ('status', 'resume'):
        sub.add_parser(cmd).add_argument('file', type=Path)
    args = parser.parse_args()
    path = args.file.absolute()
    if args.command == 'init':
        brief = json.loads(args.brief.read_text(encoding='utf-8'))
        for key in ('goal', 'references', 'prompt', 'requested_settings', 'output_dir', 'acceptance', 'authorization_scope'):
            if not brief.get(key):
                parser.error('Missing or empty brief field: ' + key)
        if not isinstance(brief['references'], list):
            parser.error('references must be a list')
        path.parent.mkdir(parents=True, exist_ok=True)
        with locked(path):
            if path.exists() or path.is_symlink():
                parser.error('Task already exists')
            data = dict(schema_version=1, state='prepared', brief=brief,
                        provider_task_id=None, history=[dict(state='prepared', at=now())])
            save(path, data)
    elif args.command == 'advance':
        with locked(path):
            data = json.loads(path.read_text(encoding='utf-8'))
            old, new = data['state'], args.state
            if new not in NEXT[old]:
                parser.error('Invalid transition: ' + old + ' -> ' + new)
            if not args.evidence.strip():
                parser.error('Evidence cannot be blank')
            prior = data.get('provider_task_id')
            if args.task_id and prior and args.task_id != prior:
                parser.error('Cannot replace an existing provider task ID')
            if new == 'submitted' and not (args.task_id or prior):
                parser.error('submitted requires --task-id')
            data['provider_task_id'] = args.task_id or prior
            data['state'] = new
            data['history'].append(dict(state=new, at=now(), evidence=args.evidence))
            save(path, data)
    else:
        data = json.loads(path.read_text(encoding='utf-8'))
    print(json.dumps(data if args.command != 'resume' else dict(state=data['state'], next_action=resume(data)), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

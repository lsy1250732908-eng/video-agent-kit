import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / 'scripts/task.py'
FINISH = ROOT / 'skills/kling-video-producer/scripts/finish_video.py'
FFMPEG = os.environ.get('FFMPEG') or shutil.which('ffmpeg')

def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)

class TaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'task.json'
        self.assertEqual(run(TASK, 'init', self.path, '--brief', ROOT/'examples/brief.json').returncode, 0)
    def advance(self, state, *extra):
        return run(TASK, 'advance', self.path, state, '--evidence', 'test observation', *extra)
    def test_uncertain_does_not_resubmit(self):
        self.assertEqual(self.advance('submitting').returncode, 0)
        self.assertIn('Do not resubmit', run(TASK, 'resume', self.path).stdout)
        self.assertEqual(self.advance('uncertain').returncode, 0)
        before=self.path.read_bytes()
        self.assertNotEqual(self.advance('submitting').returncode, 0)
        self.assertEqual(before,self.path.read_bytes())
        self.assertNotEqual(self.advance('submitted').returncode, 0)
        self.assertEqual(self.advance('submitted', '--task-id', 'demo-id').returncode, 0)
    def test_download_recovery_preserves_task(self):
        for state, extra in [('submitting',()),('submitted',('--task-id','demo-id')),('generated',())]:
            self.assertEqual(self.advance(state,*extra).returncode,0)
        self.assertIn('do not regenerate',run(TASK,'resume',self.path).stdout)
        self.assertNotEqual(self.advance('downloaded','--task-id','different').returncode,0)
        for state in ['downloaded','verified','delivered']:
            self.assertEqual(self.advance(state).returncode,0)
        self.assertNotEqual(self.advance('submitting').returncode,0)
    def test_existing_task_and_lock_protected(self):
        before=self.path.read_bytes()
        self.assertNotEqual(run(TASK,'init',self.path,'--brief',ROOT/'examples/brief.json').returncode,0)
        self.path.with_name('task.json.lock').touch()
        self.assertNotEqual(self.advance('submitting').returncode,0)
        self.assertEqual(before,self.path.read_bytes())

@unittest.skipUnless(FFMPEG, 'FFmpeg required for media integration tests')
class MediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.src=self.dir/'demo.mp4'
        p=run(ROOT/'scripts/make_demo.py','--output',self.src,'--ffmpeg',FFMPEG)
        self.assertEqual(p.returncode,0,p.stderr)
        self.out=self.dir/'final.mp4'
    def finish(self, src=None, duration='1'):
        return run(FINISH,'--input',src or self.src,'--output',self.out,'--ffmpeg',FFMPEG,'--expected-duration',duration)
    def test_valid_and_no_overwrite(self):
        p=self.finish(); self.assertEqual(p.returncode,0,p.stderr)
        report=json.loads(self.out.with_suffix('.verification.json').read_text())
        self.assertEqual(report['sha256'],hashlib.sha256(self.src.read_bytes()).hexdigest())
        self.assertEqual(self.src.read_bytes(),self.out.read_bytes())
        self.assertNotEqual(self.finish().returncode,0)
        self.assertEqual(self.src.read_bytes(),self.out.read_bytes())
    def test_html_rejected(self):
        bad=self.dir/'html.mp4';bad.write_text('<html>Not a video</html>')
        self.assertNotEqual(self.finish(bad).returncode,0)
        self.assertFalse(self.out.exists())
    def test_truncated_rejected(self):
        bad=self.dir/'truncated.mp4';bad.write_bytes(self.src.read_bytes()[:-9])
        self.assertNotEqual(self.finish(bad).returncode,0)
        self.assertFalse(self.out.exists())
    def test_duration_rejected(self):
        self.assertNotEqual(self.finish(duration='8').returncode,0)
        self.assertFalse(self.out.exists())
    def test_report_collision(self):
        report=self.out.with_suffix('.verification.json');report.write_text('keep')
        self.assertNotEqual(self.finish().returncode,0)
        self.assertEqual(report.read_text(),'keep');self.assertFalse(self.out.exists())
    def test_broken_symlink_protected(self):
        self.out.symlink_to(self.dir/'missing')
        self.assertNotEqual(self.finish().returncode,0)
        self.assertTrue(self.out.is_symlink())
    def test_nonfinite_duration(self):
        self.assertNotEqual(self.finish(duration='nan').returncode,0)
        self.assertFalse(self.out.exists())

class PackageTests(unittest.TestCase):
    def test_relative_markdown_links(self):
        for path in ROOT.rglob('*.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                if '://' not in target and not target.startswith(('/', '#')):
                    self.assertTrue((path.parent/target.split('#')[0]).exists(),str(path)+': '+target)
    def test_no_private_assets_or_local_paths(self):
        for path in ROOT.rglob('*'):
            if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts or 'runs' in path.parts:
                continue
            self.assertNotIn(path.suffix.lower(),['.mp4','.mov','.png','.jpg','.zip'])
            text=path.read_text()
            for marker in ['/Users/'+'l/', 'xsec_'+'token=', 'material'+'Id=', 'gh'+'p_']:
                self.assertNotIn(marker,text,str(path))

if __name__ == '__main__':
    unittest.main()

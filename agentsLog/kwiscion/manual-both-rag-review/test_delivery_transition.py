"""No-network independent launcher delivery transition check."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1]/'manual-final-prep/launcher.py'
spec = importlib.util.spec_from_file_location('review_launcher', path)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class DeliveryTransition(unittest.TestCase):
    def test_finalizing_backup_delivers_validated_answers_without_archive(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            exam = out/'package/exam'
            exam.mkdir(parents=True)
            doc = {'exam_id': 'synthetic', 'answers': [{'id': 'id/arbitrary', 'answer': 'Completed'}]}
            raw = json.dumps(doc).encode()
            (exam/'answers-template.json').write_bytes(raw)
            now = datetime.datetime.now(datetime.timezone.utc)
            state = {'run_id': '20260927T075706-fbdc2cd3', 'phase': 'RUNNING',
                     'started_utc': now.isoformat(),
                     'local_target_utc': (now+datetime.timedelta(minutes=60)).isoformat()}
            status = {'status': 'FINALIZING_BACKUP', 'terminal': {
                'answers_present': True, 'answers_sha256': hashlib.sha256(raw).hexdigest()}}
            transfers = []
            def transfer(source, dest):
                transfers.append(source)
                self.assertTrue(source.endswith('/package/results/answers.json'))
                Path(dest).write_bytes(raw)
            with patch.object(launcher, 'ssh', return_value=status) as remote, \
                 patch.object(launcher, 'transfer', side_effect=transfer), \
                 patch.object(launcher, 'wslpath', side_effect=str), \
                 patch.object(launcher.time, 'sleep', side_effect=AssertionError('must not wait for backup')):
                self.assertEqual(launcher.workflow(out, state), 0)
            self.assertEqual((out/'answers.json').read_bytes(), raw)
            self.assertTrue((out/'validation.json').is_file())
            self.assertEqual(state['phase'], 'FETCHED')
            self.assertEqual(len(transfers), 1)
            self.assertEqual(remote.call_count, 2)


if __name__ == '__main__':
    unittest.main()

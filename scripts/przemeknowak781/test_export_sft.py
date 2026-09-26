import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import export_sft
import strict_eligibility as strict


class StrictExportTests(unittest.TestCase):
    def test_committed_artifact_matches_both_recorded_lenses(self):
        rows = strict.reviewed_records()
        self.assertEqual(len(rows), 24)
        self.assertEqual(rows, strict.read_rows(strict.ROOT / strict.BASE / 'train_strict.jsonl'))
        self.assertTrue(all('legacy_audit' in row for row in rows))

    def assert_isolated(self, rows):
        output = export_sft.render_exports(rows)
        groups = {part: {row['source_group_id'] for row in output[f'grounded_{part}']}
                  for part in ('train', 'holdout')}
        self.assertTrue(groups['train'])
        self.assertTrue(groups['holdout'])
        self.assertFalse(groups['train'] & groups['holdout'])
        for part, other in (('train', 'holdout'), ('holdout', 'train')):
            foreign_claims = {e['claim'] for row in rows if row['source_group_id'] in groups[other]
                              for e in row['evidence']}
            local_claims = [e['claim'] for row in rows if row['source_group_id'] in groups[part]
                            for e in row['evidence']]
            # General facts can independently occur in both source groups. Test foreign-only
            # passages, plus exact provenance membership above, rather than banning shared facts.
            foreign_claims = {claim for claim in foreign_claims
                              if not any(claim in local for local in local_claims)}
            for row in output[f'grounded_{part}']:
                self.assertTrue(set(row['context_source_group_ids']) <= groups[part])
                context = row['messages'][1]['content'].split('\n\nPytanie:', 1)[0]
                self.assertFalse(any(claim in context for claim in foreign_claims))
        return output

    def test_real_strict_split_and_all_context_are_disjoint(self):
        out = self.assert_isolated(strict.reviewed_records())
        self.assertEqual(len(out['grounded_train']), 22)
        self.assertEqual(len(out['grounded_holdout']), 2)

    def test_regression_on_legacy_197_split_previously_leaked_18_rows(self):
        # Exercise selection only; these rows are explicitly not export-eligible.
        rows = [r for r in strict.read_rows(strict.ROOT / strict.TRAIN)
                if r['audit']['status'] == 'verified']
        self.assertEqual(len(rows), 197)
        self.assert_isolated(rows)

    def test_missing_strict_default_and_legacy_override_fail_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(export_sft, 'BASE', root):
                self.assertEqual(export_sft.main(['--output-dir', str(root / 'out')]), 1)
            self.assertFalse((root / 'out').exists())
            self.assertEqual(export_sft.main(['--input', str(strict.ROOT / strict.TRAIN),
                                              '--output-dir', str(root / 'out')]), 1)
            self.assertFalse((root / 'out').exists())

    def test_changed_answer_cannot_reuse_passing_id(self):
        rows = copy.deepcopy(strict.reviewed_records())
        rows[0]['answer'] += ' Unsupported added statement.'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'changed.jsonl'
            path.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'not the reviewed strict version'):
                strict.eligible_input(path)

    def test_changed_verdict_snapshot_requires_rereview(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path = strict.BASE / 'strict_provenance.json'
            manifest = json.loads((strict.ROOT / manifest_path).read_text(encoding='utf-8'))
            for name in [str(manifest_path), *manifest['files']]:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(strict.ROOT / name, destination)
            with (root / strict.LENSES[0]).open('a', encoding='utf-8') as stream:
                stream.write('\n')
            with self.assertRaisesRegex(ValueError, 'evidence changed'):
                strict.reviewed_records(root)


if __name__ == '__main__':
    unittest.main()

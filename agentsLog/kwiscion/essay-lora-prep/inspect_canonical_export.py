"""Read only the authorized original-curriculum export from pinned Git; no clearance."""
import hashlib,json,subprocess
from pathlib import Path
import prepare as p
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
REV='401e1bc'
PREFIX='agentsLog/Bukareszt/essay_corpus/export_v1/'
def read(name):return subprocess.check_output(['git','-c','safe.directory='+str(REPO).replace('\\','/'),'show',REV+':'+PREFIX+name],cwd=REPO)
def main():
    train_raw=read('train_sft.jsonl');eval_raw=read('eval16_input.jsonl');manifest=json.loads(read('export_manifest.json'))
    train=[json.loads(x) for x in train_raw.splitlines()];evaluations=[json.loads(x) for x in eval_raw.splitlines()]
    assert p.sha(train_raw)==manifest['train_sha256'];assert p.sha(eval_raw)==manifest['eval_sha256']
    edges=manifest['component_of_group'];groups={r['source_group_id'] for r in train+evaluations}
    def component(g):
        seen=set()
        while g in edges:
            if g in seen:raise ValueError('Grouping cycle')
            seen.add(g);g=edges[g]
        return g
    mapping={g:component(g) for g in sorted(groups)}
    assert not {mapping[r['source_group_id']] for r in train}&{mapping[r['source_group_id']] for r in evaluations}
    report={'git_revision':REV,'train_records':len(train),'essay_count':sum(r['task_type']=='essay' for r in train),'repair_count':sum(r['task_type']=='essay_repair' for r in train),'eval_inputs':len(evaluations),'train_sha256_git_blob':p.sha(train_raw),'eval_sha256_git_blob':p.sha(eval_raw),'train_fields':sorted(train[0]),'eval_fields':sorted(evaluations[0]),'role_sequences':sorted({tuple(m['role'] for m in r['messages']) for r in train}),'target_word_count_range':[min(len(r['messages'][-1]['content'].split()) for r in train),max(len(r['messages'][-1]['content'].split()) for r in train)],'canonical_group_map':mapping,'component_edges':edges,'known_dev_overlap':manifest['train_groups_overlapping_pewciu6_dev'],'rights_review':'PENDING_ROOT_AUDIT','independent_data_audit':'PENDING','training_clearance_granted':False,'note':'Git blob hashes are LF bytes; actual Windows working-file bytes need separate clearance binding.'}
    (ROOT/'canonical-export-inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

"""CPU-only, answer-only masked handoff; never reads reasoning or official keys."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets


def read(path):return json.loads(path.read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(root,output,source_item_id):
    if output.exists():raise ValueError('Fresh grading output required')
    output.mkdir(parents=True)
    stage=root/'bundle/agentsLog/kwiscion/private/branch-wave'
    first=read(root/'drafts-source/branching-manifest.json')
    expected=[(x['id'],x['role'],x['topic'],'drafts-runtime') for x in first['routes']]
    expected.append((first['original_item_id'],'selector_final',None,'selector-runtime'))
    rows=[];key=[];evidence={}
    for item,role,topic,label in expected:
        result=stage/label/'results';answer='';error=None;state={}
        if (result/'answers.json').exists():
            receipt=read(result/'terminal.json')
            if receipt['answers_sha256']!=sha(result/'answers.json'):raise ValueError('Terminal answer hash mismatch')
            matches=[x for x in read(result/'answers.json')['answers'] if x['id']==item]
            if len(matches)!=1:raise ValueError('Expected exact unique output ID')
            answer=matches[0]['answer'];state=read(result/'engine/answer-status.json')['items'][item]
            if state['placeholder']:error='explicit_runtime_placeholder'
            evidence[label]={'answers_sha256':sha(result/'answers.json'),'terminal_sha256':sha(result/'terminal.json')}
        else:error='stage_produced_no_terminal_answer'
        opaque=secrets.token_hex(8);digest=hashlib.sha256(answer.encode('utf8')).hexdigest()
        rows.append(dict(id=opaque,source_item_id=source_item_id,answer=answer,error=error,
                         incomplete_partial=state.get('incomplete_partial',False),answer_sha256=digest))
        key.append(dict(id=opaque,role=role,forced_topic=topic,stage_item_id=item,answer_sha256=digest,submitted_status=state))
    secrets.SystemRandom().shuffle(rows)
    for name,items in [('grading-masked.jsonl',rows),('grading-arm-key.jsonl',key)]:
        with (output/name).open('x',encoding='utf8',newline='\n') as f:
            for row in items:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    report={'status':'ANSWER_ONLY_FROZEN','rows':len(rows),'evidence':evidence,
        'masked_sha256':sha(output/'grading-masked.jsonl'),'key_sha256':sha(output/'grading-arm-key.jsonl'),
        'submitted_wave_answer_sha256':sha(root/'answers.json') if (root/'answers.json').exists() else None,
        'note':'Grade these exact stage finals once. Oracle comparison is retrospective only; do not replace selector output. Operational wave fallback remains separate.'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);p.add_argument('--source-item-id',required=True);a=p.parse_args()
    print(json.dumps(extract(a.root,a.output,a.source_item_id)))

"""Structural checks only: never certifies historical correctness or rights clearance."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(name): return [json.loads(x) for x in (ROOT/name).read_text(encoding='utf-8').splitlines()]
def main():
    essays=load('essays.jsonl'); repairs=load('repairs.jsonl'); sources=load('sources.jsonl'); errors=[]
    ids={e['id']:e for e in essays}
    for r in essays+repairs:
        if not 400<=len(r['response'].split())<=500: errors.append(r['id']+': word count')
        if r['body_word_count']!=len(r['response'].split()): errors.append(r['id']+': stale count')
        if r['split'] is not None or r['status']!='synthetic_draft_pending_independent_review': errors.append(r['id']+': review gate')
        if len(r['response'].split('\n\n'))!=5: errors.append(r['id']+': expected five paragraphs')
        if hashlib.sha256(r['response'].encode()).hexdigest()!=r['response_sha256']: errors.append(r['id']+': response hash')
    for r in repairs:
        parent=ids[r['parent_essay_id']]
        if r['response']!=parent['response'] or r['source_group_id']!=parent['source_group_id']: errors.append(r['id']+': pair mismatch')
        if 'Wskazany temat: '+parent['topic'] not in r['prompt']: errors.append(r['id']+': selected topic absent')
        if 'underlength' in r['defects'] and len(r['corrupted_response'].split())>=300: errors.append(r['id']+': negative not underlength')
    for s in sources:
        path=ROOT/s['local_path']
        if not path.exists() or 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()!=s['revision_or_sha256']: errors.append(s['source_id']+': source hash')
        if not s['revision_id'] or not s['license_footer_present']: errors.append(s['source_id']+': revision/license evidence absent')
        text_path=path.with_suffix('.txt')
        if hashlib.sha256(text_path.read_text(encoding='utf-8').encode()).hexdigest()!=s['text_sha256']: errors.append(s['source_id']+': normalized text hash')
        if hashlib.sha256(text_path.read_bytes()).hexdigest()!=s['text_file_sha256']: errors.append(s['source_id']+': raw text file hash')
    review_state='pending_independent_review'
    review_path=ROOT/'independent-review.json'
    if review_path.exists():
        reviewed={r['id']:r for r in json.loads(review_path.read_text(encoding='utf-8'))['records']}
        for r in essays+repairs:
            audit=reviewed.get(r['id'],{})
            if hashlib.sha256(r['response'].encode()).hexdigest()!=audit.get('response_sha256'): errors.append(r['id']+': independent target hash')
            if hashlib.sha256(r['prompt'].encode()).hexdigest()!=audit.get('prompt_sha256'): errors.append(r['id']+': independent prompt hash')
        review_state='content accepted with limitations; canonical export pending'
    report=dict(structural_pass=not errors,essays=len(essays),repairs=len(repairs),sources=len(sources),errors=errors,historical_accuracy=review_state,cross_corpus_source_group_dedup='pending',rights_and_export_check='pending',accepted_training_records=0)
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    sums=[]
    for path in sorted(ROOT.iterdir()):
        if path.is_file() and path.name!='SHA256SUMS.txt': sums.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name)
    (ROOT/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    print(json.dumps(report)); raise SystemExit(bool(errors))
if __name__=='__main__': main()

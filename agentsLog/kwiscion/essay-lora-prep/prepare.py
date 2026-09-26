"""CPU-only fail-closed preparation. No training, model loading or network access."""
import argparse, hashlib, importlib.metadata, importlib.util, json, math, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CHECKS=('independent_content_review','rights_export_review','source_group_alias_dedup','benchmark_exclusion_audit')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(row): return json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def require(ok,message):
    if not ok: raise ValueError(message)

def messages(row):
    if 'messages' in row:
        result=row['messages']
        roles=[m['role'] for m in result]
        require(roles in (['user','assistant'],['system','user','assistant']), 'Only one text user/assistant pair, optionally system, is allowed')
        require(all(isinstance(m.get('content'),str) and m['content'].strip() for m in result),'Empty or multimodal message')
    else:
        result=[{'role':'user','content':row['prompt']},{'role':'assistant','content':row.get('response',row.get('answer',''))}]
    require(400<=len(result[-1]['content'].split())<=500,'Target outside current 400–500 word contract')
    require(not any(x in m['content'] for m in result for x in ('<|turn>','<turn|>','<|channel>','<channel|>')),'Reserved control token in source text')
    return result

def validate_data(train,holdout,clearance,files,eval_inputs=None):
    require(clearance.get('schema')=='essay_lora_clearance_v1','Clearance schema missing or unsupported')
    require(all(clearance.get('checks',{}).get(k) is True for k in CHECKS),'Independent data/export gates incomplete')
    require(bool(train) and (bool(holdout) if eval_inputs is None else bool(eval_inputs)),'Need train and independently grouped target holdout or eval inputs')
    if eval_inputs is not None:
        require(not holdout,'Cannot mix target holdout with eval-input-only mode')
        require(clearance.get('checks',{}).get('evaluation_inputs_group_audit') is True,'Evaluation-input group audit incomplete')
    for split,path in files.items():
        require(clearance.get('files',{}).get(split,{}).get('sha256')==sha(path.read_bytes()),'Clearance does not bind exact '+split+' file')
    seen=set(); partitions={'train':set(),'holdout':set()}; source_parts={}; responses={}
    groupmap=clearance.get('canonical_group_map',{})
    reviewed=clearance.get('accepted_records',{})
    for split,rows in [('train',train),('holdout',holdout)]:
        for row in rows:
            ident=row.get('id'); require(isinstance(ident,str) and ident not in seen,'Missing/duplicate record ID');seen.add(ident)
            require(row.get('task_type') in ('essay','essay_repair'),'Non-essay record')
            require(row.get('split',split)==split,'Record split conflicts with file')
            require('draft' not in str(row.get('status','')).lower(),'Explicit DRAFT row cannot be exported')
            review=reviewed.get(ident,{})
            require(review.get('status')=='accepted' and review.get('record_sha256')==sha(canonical(row)),'Missing exact accepted-record binding: '+ident)
            require(bool(review.get('independent_review_reference')),'Missing independent review provenance')
            msgs=messages(row); response_hash=sha(msgs[-1]['content'].encode())
            require(response_hash not in responses or responses[response_hash]==split,'Same target response across train/holdout')
            responses[response_hash]=split
            groups=[row.get('source_group_id')]+row.get('additional_source_group_dependencies',[])+row.get('context_source_group_ids',[])
            require(all(isinstance(g,str) and g in groupmap for g in groups),'Unmapped source-group dependency')
            partitions[split].update(groupmap[g] for g in groups)
            source_ids=row.get('source_ids',[])
            require(bool(source_ids),'Missing source IDs')
            for source in source_ids:
                require(source not in source_parts or source_parts[source]==split,'Same source across train/holdout')
                source_parts[source]=split
    require(not partitions['train']&partitions['holdout'],'Canonical source component crosses train/holdout')
    require(set(reviewed)==seen,'Clearance accepted-record set differs from export')
    if eval_inputs is not None:
        eval_components=set()
        for row in eval_inputs:
            require(isinstance(row.get('id'),str) and row['id'] not in seen,'Missing/duplicate evaluation ID');seen.add(row['id'])
            require(isinstance(row.get('prompt'),str) and bool(row['prompt'].strip()),'Missing evaluation input')
            require(not any(k in row for k in ('answer','response','messages','labels')),'Input-only evaluation must not contain target fields')
            groups=[row.get('source_group_id')]+row.get('additional_source_group_dependencies',[])
            require(all(isinstance(g,str) and g in groupmap for g in groups),'Unmapped evaluation group')
            eval_components.update(groupmap[g] for g in groups)
            require(not (set(row.get('source_ids',[]))&set(source_parts)),'Evaluation source shared with training')
        require(not eval_components&partitions['train'],'Evaluation component overlaps training')
        partitions['external_eval']=eval_components
    return {'train_records':len(train),'holdout_records':len(holdout),'external_eval_input_count':len(eval_inputs or []),'evaluation_loss_enabled':eval_inputs is None,'early_stopping_enabled':False,'frozen_epochs':3,'canonical_components':{k:sorted(v) for k,v in partitions.items()},'max_optimizer_steps':min(120,3*math.ceil(len(train)/8))}

def tokenized_record(row,tokenizer,max_length):
    """Use actual canonical nonthinking inference prefix, not full-chat assistant rendering."""
    msgs=messages(row)
    prefix=tokenizer.apply_chat_template(msgs[:-1],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    require(prefix.endswith('<|turn>model\n<|channel>thought\n<channel|>'),'Unexpected nonthinking generation prefix')
    end='<turn|>'
    full=prefix+msgs[-1]['content']+end
    prefix_ids=tokenizer(prefix,add_special_tokens=False)['input_ids']
    full_ids=tokenizer(full,add_special_tokens=False)['input_ids']
    require(full_ids[:len(prefix_ids)]==prefix_ids,'Tokenizer changed prompt/answer boundary; no guessed mask')
    require(len(full_ids)<=max_length,'Oversized record: '+row['id']+' '+str(len(full_ids)))
    require(len(full_ids)>len(prefix_ids),'No completion tokens')
    end_ids=tokenizer(end,add_special_tokens=False)['input_ids']
    require(len(end_ids)==1 and full_ids[-1]==end_ids[0],'Turn terminator is not one recognized token')
    return {'id':row['id'],'input_ids':full_ids,'attention_mask':[1]*len(full_ids),'mm_token_type_ids':[0]*len(full_ids),'labels':[-100]*len(prefix_ids)+full_ids[len(prefix_ids):],'prompt_tokens':len(prefix_ids),'completion_tokens':len(full_ids)-len(prefix_ids)}

def inspect_environment():
    report={}
    for name in ('torch','transformers','peft','tokenizers','safetensors','jinja2'):
        available=importlib.util.find_spec(name) is not None
        try:version=importlib.metadata.version(name) if available else None
        except importlib.metadata.PackageNotFoundError:version='unknown'
        report[name]={'available':available,'version':version}
    return report

def verify_metadata(base,cfg):
    require(sha((base/'config.json').read_bytes())==cfg['config_sha256'],'Base config differs from pinned metadata')
    evidence=json.loads((ROOT/'evidence-manifest.json').read_text(encoding='utf-8'))
    for local,evidence_name in [('chat_template.jinja','hf-chat_template.jinja'),('tokenizer_config.json','hf-tokenizer_config.json'),('processor_config.json','hf-processor_config.json')]:
        entry=next(x for x in evidence['files'] if x['file']==evidence_name)
        require(sha((base/local).read_bytes())==entry['sha256'],'Pinned metadata mismatch: '+local)

SUBMISSION_WEIGHT_LIMIT=8_800_000_000

def check_artifacts(paths,limit=SUBMISSION_WEIGHT_LIMIT):
    """Count the entire declared submission inventory, not one route's model.

    The caller must list every submitted weight, including adapters/projectors.
    This byte gate does not establish inventory completeness or runtime support.
    """
    require(type(limit) is int and 0<limit<=SUBMISSION_WEIGHT_LIMIT,'Invalid aggregate limit')
    require(bool(paths),'Nonempty complete submitted weight list required')
    resolved=[Path(p).resolve(strict=True) for p in paths]
    require(len(set(resolved))==len(resolved),'Duplicate artifact')
    for i,path in enumerate(resolved):
        require(path.is_file() and path.stat().st_size>0,'Nonempty regular weight file required: '+str(path))
        require(not any(path.samefile(prior) for prior in resolved[:i]),'Duplicate artifact through file alias')
    total=sum(path.stat().st_size for path in resolved)
    require(total<=limit,'Aggregate submitted weights exceed byte limit')
    sizes=[]
    for path in resolved:
        with path.open('rb') as f:
            if path.suffix.lower()=='.gguf':require(f.read(4)==b'GGUF','Not a GGUF: '+str(path))
            f.seek(0);h=hashlib.sha256()
            for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
        sizes.append({'path':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest()})
    final_total=sum(x['bytes'] for x in sizes)
    require(final_total==total and final_total<=limit,'Weight files changed during size check')
    return {'files':sizes,'total_bytes':total,'limit_bytes':limit,'remaining_bytes':limit-total,
            'scope':'ALL_SUBMITTED_MODEL_WEIGHTS_INCLUDING_ADAPTERS_AND_PROJECTORS',
            'byte_limit_pass':True,'inventory_completeness':'CALLER_MUST_VERIFY_AGAINST_FINAL_SUBMISSION',
            'runtime_load_adapter_support_and_matching_projector':'NOT_CHECKED'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('environment')
    data=sub.add_parser('data');data.add_argument('--train',type=Path,required=True);evaluation=data.add_mutually_exclusive_group(required=True);evaluation.add_argument('--holdout',type=Path);evaluation.add_argument('--eval-inputs',type=Path);data.add_argument('--clearance',type=Path,required=True);data.add_argument('--local-base',type=Path);data.add_argument('--output',type=Path)
    size=sub.add_parser('size');size.add_argument('artifacts',type=Path,nargs='+')
    args=ap.parse_args();cfg=json.loads((ROOT/'candidate.json').read_text(encoding='utf-8'))
    if args.command=='environment':result=inspect_environment()
    elif args.command=='size':result=check_artifacts(args.artifacts)
    else:
        train=read_jsonl(args.train);holdout=read_jsonl(args.holdout) if args.holdout else [];evaluations=read_jsonl(args.eval_inputs) if args.eval_inputs else None;clear=json.loads(args.clearance.read_text(encoding='utf-8'))
        files={'train':args.train,('holdout' if args.holdout else 'eval_inputs'):(args.holdout or args.eval_inputs)}
        result=validate_data(train,holdout,clear,files,eval_inputs=evaluations)
        result['tokenization']='NOT_RUN'
        if args.local_base:
            require(args.output is not None,'Tokenization needs a fresh output directory');require(not args.output.exists(),'Refusing overwrite')
            verify_metadata(args.local_base,cfg)
            from transformers import AutoTokenizer
            tokenizer=AutoTokenizer.from_pretrained(str(args.local_base),local_files_only=True,trust_remote_code=False)
            encoded={k:[tokenized_record(r,tokenizer,cfg['max_sequence_length']) for r in rows] for k,rows in [('train',train),('holdout',holdout)] if rows}
            args.output.mkdir(parents=True)
            for split,rows in encoded.items():
                with (args.output/(split+'.jsonl')).open('x',encoding='utf-8',newline='\n') as f:
                    for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            result['tokenization']='PASS';result['max_sequence_tokens']=max(len(r['input_ids']) for rows in encoded.values() for r in rows)
            result['source_files']={k:sha(p.read_bytes()) for k,p in {**files,'clearance':args.clearance}.items()}
            if args.eval_inputs:(args.output/'eval-inputs.jsonl').write_bytes(args.eval_inputs.read_bytes())
            (args.output/'preparation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

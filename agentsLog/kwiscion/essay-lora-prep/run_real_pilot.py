"""Finite real-base synthetic probe / cleared history pilot. No generation or downloads.

Default validates a frozen stage manifest only. --execute requires a declared
deadline, exact local pins and fresh output. External owner supplies sole-worker
supervision and a hard subprocess timeout; this process also uses SIGALRM.
"""
import argparse,datetime as dt,hashlib,importlib.util,json,math,os,re,signal,time,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE_SHA='5a84cb313260ac447237b890387116dfa8682e49a6b44bc585ae8353abbff18d'
TOKENIZER_SHA='cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def require_multimodal_inventory(inventory):
    require(bool(inventory),'Empty frozen multimodal tensor inventory')
def groups(count,epochs=3,size=8):
    require(type(count) is int and 0<count<=320,'Bounded row count')
    return [list(range(i,min(i+size,count))) for _ in range(epochs) for i in range(0,count,size)]
def validate_manifest(m):
    require(m['mode'] in ('synthetic_probe','history'),'Stage mode')
    require(m['max_optimizer_steps']==(1 if m['mode']=='synthetic_probe' else 36),'Exact stage step bound')
    require(m['max_seconds']==(600 if m['mode']=='synthetic_probe' else 1500),'Exact stage wall bound')
    require(m['base_weight_sha256']==BASE_SHA and m['inference_calls']==0,'Base/inference controls')
    require(m['mode']!='history' or m['train_records']==90,'Cleared90-row pilot only')
    require(all(str(ROOT/name) in m['files'] for name in ('run_real_pilot.py','prepare.py','candidate.json','evidence-manifest.json')),'Pin every governing script/config')
    if m['mode']=='history':
        require(all(m[k] in m['files'] for k in ('train','eval_inputs','clearance','control_serving_report','synthetic_probe_report')),'Pin history inputs and qualification')
    return m
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('manifest',type=Path);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    m=validate_manifest(json.loads(a.manifest.read_text()));print(json.dumps({'mode':m['mode'],'execute':a.execute}),flush=True)
    if not a.execute:return
    require(m['status']=='DECLARED','Root-declared manifest required')
    now=dt.datetime.now(dt.timezone.utc);end=dt.datetime.fromisoformat(m['deadline_utc'].replace('Z','+00:00'))
    remaining=min(m['max_seconds'],(end-now).total_seconds());require(remaining>0,'Expired deadline')
    import fcntl
    lock=Path(m['lock_file']).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def gpu_idle(allow_self=False):
        pids=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).splitlines()
        require(all(allow_self and int(x.strip())==os.getpid() for x in pids if x.strip()),'Competing GPU process; do not stop/adopt it')
    gpu_idle()
    out=Path(m['output']);require(not out.exists(),'Fresh output only');out.mkdir(parents=True)
    def timeout(*_):raise TimeoutError('Stage hard deadline')
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,remaining)
    started=time.monotonic();steps=0;report={'status':'FAIL','mode':m['mode'],'history_optimizer_steps':0,'synthetic_optimizer_steps':0,
        'manifest_sha256':sha(a.manifest),'base_weight_sha256':BASE_SHA,'tokenizer_sha256':TOKENIZER_SHA,
        'driver_sha256':sha(Path(__file__)),'candidate_sha256':sha(ROOT/'candidate.json'),'pinned_files':m['files']}
    try:
        for filename,digest in m['files'].items():require(sha(Path(filename))==digest,'Frozen file: '+filename)
        base=Path(m['base']);require(sha(base/'model.safetensors')==BASE_SHA,'Full base weights')
        require(sha(base/'tokenizer.json')==TOKENIZER_SHA,'Full tokenizer vocab')
        cfg=json.loads((ROOT/'candidate.json').read_text())
        spec=importlib.util.spec_from_file_location('pilot_prepare',ROOT/'prepare.py');prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
        prep.verify_metadata(base,cfg)
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
        import torch,transformers,peft
        from transformers import AutoTokenizer,Gemma4UnifiedForConditionalGeneration
        from peft import LoraConfig,get_peft_model
        report['versions']={'torch':torch.__version__,'cuda':torch.version.cuda,'transformers':transformers.__version__,'peft':peft.__version__}
        require(torch.__version__.split('+')[0]=='2.8.0' and torch.version.cuda=='12.8','Pinned Torch/CUDA build')
        require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(),'CUDA BF16 required')
        # Bind actual installed source code, not only mutable version strings.
        evidence=json.loads((ROOT/'evidence-manifest.json').read_text())
        for pkg,rel in [(transformers,'models/gemma4_unified/modeling_gemma4_unified.py'),(transformers,'models/gemma4_unified/configuration_gemma4_unified.py'),(peft,'tuners/lora/layer.py'),(peft,'tuners/lora/model.py')]:
            name=pkg.__name__+'-src_'+pkg.__name__+'_'+rel.replace('/','_')
            expected=next(x['sha256'] for x in evidence['files'] if x['file']==name)
            require(sha(Path(pkg.__file__).parent/rel)==expected,'Installed source pin')
        tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True,trust_remote_code=False)
        if m['mode']=='history':
            probe=json.loads(Path(m['synthetic_probe_report']).read_text())
            require(probe['status']=='PASS' and probe['mode']=='synthetic_probe' and probe['synthetic_optimizer_steps']==1,'Real-base synthetic backward qualification')
            require(all(probe[k]==report[k] for k in ('base_weight_sha256','tokenizer_sha256','driver_sha256','candidate_sha256')),'Probe provenance differs')
            train=prep.read_jsonl(Path(m['train']));ev=prep.read_jsonl(Path(m['eval_inputs']));clear=json.loads(Path(m['clearance']).read_text())
            proof=prep.validate_data(train,[],clear,{'train':Path(m['train']),'eval_inputs':Path(m['eval_inputs'])},eval_inputs=ev)
            require(proof['train_records']==90 and proof['max_optimizer_steps']==36,'Cleared pilot size')
            # Serving evidence must be independently reviewed and pinned in this stage manifest.
            qualification=json.loads(Path(m['control_serving_report']).read_text())
            require(qualification['status']=='PASS' and qualification['scope']=='matched_unmodified_export_text_image','Export control qualification')
            rows=[prep.tokenized_record(x,tokenizer,4096) for x in train]
        else:
            prompt='Syntetyczna kontrola uczenia. Zwróć słowo gotowe.'
            prefix=tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=True,add_generation_prompt=True,enable_thinking=False)
            answer=tokenizer.encode('gotowe<turn|>',add_special_tokens=False)
            rows=[{'input_ids':prefix+answer,'labels':[-100]*len(prefix)+answer}]
        require(all(0<len(x['input_ids'])<=4096 and len(x['input_ids'])==len(x['labels']) for x in rows),'No truncation')
        torch.manual_seed(42);torch.cuda.reset_peak_memory_stats()
        model=Gemma4UnifiedForConditionalGeneration.from_pretrained(base,local_files_only=True,trust_remote_code=False,dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda')
        original_shapes={n:tuple(v.shape) for n,v in model.state_dict().items()}
        def multimodal_hashes(obj):
            return {n:hashlib.sha256(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
                    for n,v in obj.state_dict().items() if 'embed_vision' in n or 'embed_audio' in n}
        multimodal_before=multimodal_hashes(model)
        require_multimodal_inventory(multimodal_before)
        report['multimodal_before_sha256']=multimodal_before
        matched=[n for n,_ in model.named_modules() if re.fullmatch(cfg['lora']['target_modules'],n)];require(len(matched)==88,'Exact88 text q/v modules')
        model=get_peft_model(model,LoraConfig(**{k:v for k,v in cfg['lora'].items() if v is not None}))
        params=[p for n,p in model.named_parameters() if p.requires_grad]
        require(sum(p.numel() for p in params)==5193728,'Exact r8 trainable count')
        require(all('lora_' in n and 'language_model.layers.' in n for n,p in model.named_parameters() if p.requires_grad),'Text-only LoRA')
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads();model.config.use_cache=False;model.train()
        optimizer=torch.optim.AdamW(params,lr=1e-4,weight_decay=0.0)
        batches=[[0]] if m['mode']=='synthetic_probe' else groups(len(rows))
        require(len(batches)<=m['max_optimizer_steps']<=120,'Optimizer cap')
        for group in batches:
            gpu_idle(allow_self=True)
            optimizer.zero_grad(set_to_none=True);losses=[]
            for index in group:
                row=rows[index];ids=torch.tensor([row['input_ids']],device='cuda');labels=torch.tensor([row['labels']],device='cuda')
                loss=model(input_ids=ids,attention_mask=torch.ones_like(ids),mm_token_type_ids=torch.zeros_like(ids),labels=labels,use_cache=False).loss
                require(bool(torch.isfinite(loss)),'Nonfinite loss');(loss/len(group)).backward();losses.append(float(loss.detach()))
            grads=[p.grad for p in params if p.grad is not None]
            require(grads and all(bool(torch.isfinite(x).all()) for x in grads) and any(bool(torch.count_nonzero(x)) for x in grads),'Finite nonzero gradients')
            before=[p.detach().clone() for p in params]
            optimizer.step();steps+=1;require(all(bool(torch.isfinite(p).all()) for p in params),'Nonfinite updated adapter')
            delta=max(float((p.detach()-old).abs().max()) for p,old in zip(params,before));require(delta>0,'Zero optimizer parameter update')
            del before
            with (out/'steps.jsonl').open('a') as f:f.write(json.dumps({'optimizer_step':steps,'examples':len(group),'mean_loss':sum(losses)/len(losses),'max_parameter_delta':delta})+'\n');f.flush();os.fsync(f.fileno())
        if m['mode']=='history':
            model.save_pretrained(out/'adapter',safe_serialization=True)
            # Export only ONE merged deployment candidate; original development base is preserved.
            merged=model.merge_and_unload(safe_merge=True)
            require({n:tuple(v.shape) for n,v in merged.state_dict().items()}==original_shapes,'Merge state keys/shapes')
            multimodal_after=multimodal_hashes(merged);report['multimodal_after_sha256']=multimodal_after
            require(multimodal_after==multimodal_before,'Multimodal tensors changed')
            merged.save_pretrained(out/'merged-bf16',safe_serialization=True);tokenizer.save_pretrained(out/'merged-bf16')
            import shutil
            for name in ('processor_config.json','chat_template.jinja','generation_config.json'):
                shutil.copyfile(base/name,out/'merged-bf16'/name)
        report.update(status='PASS',trainable_parameters=5193728,matched_modules=88,max_sequence_tokens=max(len(x['input_ids']) for x in rows),peak_cuda_bytes=torch.cuda.max_memory_allocated(),inference_calls=0)
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);report['elapsed_seconds']=time.monotonic()-started;report['history_optimizer_steps' if m['mode']=='history' else 'synthetic_optimizer_steps']=steps
        if 'torch' in locals() and torch.cuda.is_initialized():
            report['peak_cuda_allocated_bytes']=torch.cuda.max_memory_allocated();report['peak_cuda_reserved_bytes']=torch.cuda.max_memory_reserved()
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

"""NEXT-STAGE synthetic CPU compatibility probe. Opt-in; no downloads, no CUDA.

Not executed during preparation. This creates random tiny weights, performs one
backward/optimizer step, and checks LoRA merge numerically. It does not qualify
12B memory, throughput, generation, tokenizer, projector or GGUF conversion.
"""
import argparse,json,os,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-synthetic',action='store_true');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if not a.execute_synthetic:raise SystemExit('No execution: explicit --execute-synthetic required for next-stage probe')
    if a.output.exists():raise SystemExit('Refusing overwrite')
    os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    started=time.monotonic()
    import torch,transformers,peft
    from transformers import Gemma4UnifiedConfig,Gemma4UnifiedForConditionalGeneration
    from peft import LoraConfig,get_peft_model
    torch.set_num_threads(2);torch.manual_seed(42)
    cfg=json.loads((ROOT/'candidate.json').read_text(encoding='utf-8'))
    tiny=Gemma4UnifiedConfig(
        text_config=dict(vocab_size=128,hidden_size=32,intermediate_size=64,num_hidden_layers=6,num_attention_heads=4,num_key_value_heads=2,head_dim=8,global_head_dim=16,num_global_key_value_heads=1,num_kv_shared_layers=0,layer_types=['sliding_attention']*5+['full_attention'],sliding_window=32,max_position_embeddings=128,attention_k_eq_v=True,hidden_size_per_layer_input=0,use_cache=False,rope_parameters={'sliding_attention':{'rope_type':'default','rope_theta':10000.0},'full_attention':{'rope_type':'proportional','rope_theta':1000000.0,'partial_rotary_factor':0.25}}),
        vision_config=dict(mm_embed_dim=32,output_proj_dims=32,mm_posemb_size=16,model_patch_size=6,patch_size=2,pooling_kernel_size=3,num_soft_tokens=4),
        audio_config=dict(audio_embed_dim=8,hidden_size=8,output_proj_dims=8,audio_samples_per_token=8),
        image_token_id=100,audio_token_id=101,video_token_id=102,boi_token_id=103,eoi_token_id=104,boa_token_id=105,eoa_token_index=106)
    tiny._attn_implementation='eager'
    base=Gemma4UnifiedForConditionalGeneration(tiny).cpu()
    original_shapes={k:tuple(v.shape) for k,v in base.state_dict().items()}
    frozen_multimodal={k:v.detach().clone() for k,v in base.state_dict().items() if 'embed_vision' in k or 'embed_audio' in k}
    matched=[n for n,m in base.named_modules() if re.fullmatch(cfg['lora']['target_modules'],n)]
    assert len(matched)==11,matched
    lora=LoraConfig(**{k:v for k,v in cfg['lora'].items() if v is not None})
    model=get_peft_model(base,lora)
    trainable=[n for n,p in model.named_parameters() if p.requires_grad]
    assert trainable and all('lora_' in n and 'language_model.layers.' in n for n in trainable)
    trainable_count=sum(p.numel() for p in model.parameters() if p.requires_grad)
    ids=torch.tensor([[2,10,11,12,13,14,15,16]],dtype=torch.long)
    labels=ids.clone();labels[:,:4]=-100
    batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),mm_token_type_ids=torch.zeros_like(ids),labels=labels,use_cache=False)
    model.train();out=model(**batch);assert torch.isfinite(out.loss)
    out.loss.backward()
    grads=[p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
    assert grads and all(torch.isfinite(g).all() for g in grads) and any(torch.count_nonzero(g) for g in grads)
    torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=1e-4).step()
    model.eval()
    with torch.no_grad():before=model(**batch).logits.clone()
    merged=model.merge_and_unload(safe_merge=True);merged.eval()
    assert {k:tuple(v.shape) for k,v in merged.state_dict().items()}==original_shapes
    for k,v in frozen_multimodal.items():assert torch.equal(v,merged.state_dict()[k]),k
    with torch.no_grad():after=merged(**batch).logits
    delta=(before-after).abs().max().item();assert torch.allclose(before,after,atol=2e-5,rtol=2e-4),delta
    report=dict(status='PASS',scope='random tiny CPU attach/backward/one-step/merge only',seconds=time.monotonic()-started,versions=dict(torch=torch.__version__,transformers=transformers.__version__,peft=peft.__version__),matched_modules=matched,trainable_parameters=trainable_count,initial_loss=out.loss.item(),merge_max_abs_logit_delta=delta,full_12b_runtime_export='NOT_TESTED')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

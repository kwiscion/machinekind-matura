"""Pinned-source evidence checks only; AST/text inspection is not runtime proof."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    manifest=json.loads((ROOT/'evidence-manifest.json').read_text(encoding='utf-8'));directory=ROOT/'evidence-private'
    for entry in manifest['files']:
        assert entry['status']=='acquired',entry
        assert hashlib.sha256((directory/entry['file']).read_bytes()).hexdigest()==entry['sha256'],entry['file']
    config=json.loads((directory/'hf-config.json').read_text());assert config['architectures']==['Gemma4UnifiedForConditionalGeneration']
    conversion=(directory/'llama.cpp-conversion_gemma.py').read_text(encoding='utf-8')
    assert conversion.count('@ModelBase.register("Gemma4UnifiedForConditionalGeneration")')==2
    assert 'class Gemma4UnifiedModel(Gemma4Model)' in conversion and 'class Gemma4UnifiedVisionAudioModel(Gemma4VisionAudioModel)' in conversion
    model=(directory/'transformers-src_transformers_models_gemma4_unified_modeling_gemma4_unified.py').read_text(encoding='utf-8')
    assert 'self.q_proj = nn.Linear(' in model and 'self.v_proj = (' in model
    assert 'self.language_model = language_model' in model
    cfg=json.loads((ROOT/'candidate.json').read_text());pattern=cfg['lora']['target_modules'];matches=[];params=0
    text=config['text_config'];rank=cfg['lora']['r']
    for i,kind in enumerate(text['layer_types']):
        qdim=text['num_attention_heads']*(text['head_dim'] if kind=='sliding_attention' else text['global_head_dim'])
        for name,dim in [('q_proj',qdim)]+([('v_proj',text['num_key_value_heads']*text['head_dim'])] if kind=='sliding_attention' else []):
            module=f'model.language_model.layers.{i}.self_attn.{name}';assert re.fullmatch(pattern,module)
            matches.append(module);params+=rank*(text['hidden_size']+dim)
    assert len(matches)==88
    for negative in ['model.embed_vision.patch_dense','model.embed_audio.embedding_projection','lm_head','model.language_model.embed_tokens']:assert not re.fullmatch(pattern,negative)
    report=dict(status='PASS_STATIC_SOURCE_CHECK',architecture=config['architectures'][0],model_type=config['model_type'],layers=text['num_hidden_layers'],sliding_layers=text['layer_types'].count('sliding_attention'),full_layers=text['layer_types'].count('full_attention'),unified_text_converter_registered=True,unified_projector_converter_registered=True,lora_module_count_expected=88,lora_parameters_arithmetic=params,bf16_adapter_tensor_bytes_arithmetic=2*params,git_pins=manifest['git_pins'],runtime_attach_backward_merge_export='NOT_EXECUTED')
    (ROOT/'source-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

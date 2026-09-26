"""Fetch small public metadata/source files only. Never fetch weights or execute them."""
import hashlib,json,urllib.request
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
HF_REV='707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'MaturaLoRAPrep/1.0'})
    with urllib.request.urlopen(req,timeout=35) as r:
        data=r.read(5_000_001)
        if len(data)>5_000_000: raise ValueError('Metadata limit exceeded')
        return data
def main():
    out=ROOT/'evidence-private';out.mkdir(exist_ok=True); rows=[]; pins={}
    for repo,branch in [('huggingface/transformers','main'),('huggingface/peft','main'),('ggml-org/llama.cpp','master')]:
        info=json.loads(get(f'https://api.github.com/repos/{repo}/commits/{branch}'));pins[repo]=info['sha']
    urls={
      'hf-config.json':f'https://huggingface.co/google/gemma-4-12B-it/resolve/{HF_REV}/config.json',
      'hf-tokenizer_config.json':f'https://huggingface.co/google/gemma-4-12B-it/resolve/{HF_REV}/tokenizer_config.json',
      'hf-chat_template.jinja':f'https://huggingface.co/google/gemma-4-12B-it/resolve/{HF_REV}/chat_template.jinja',
      'hf-processor_config.json':f'https://huggingface.co/google/gemma-4-12B-it/resolve/{HF_REV}/processor_config.json',
      'hf-README.md':f'https://huggingface.co/google/gemma-4-12B-it/resolve/{HF_REV}/README.md',
    }
    paths={
      'huggingface/transformers':['src/transformers/models/gemma4_unified/modeling_gemma4_unified.py','src/transformers/models/gemma4_unified/configuration_gemma4_unified.py','src/transformers/__init__.py','pyproject.toml'],
      'huggingface/peft':['src/peft/tuners/lora/layer.py','src/peft/utils/constants.py','src/peft/tuners/lora/model.py','pyproject.toml'],
      'ggml-org/llama.cpp':['conversion/gemma.py','convert_hf_to_gguf.py','requirements.txt','conversion/base.py'],
    }
    for repo,files in paths.items():
        for file in files: urls[repo.split('/')[1]+'-'+file.replace('/','_')]=f'https://raw.githubusercontent.com/{repo}/{pins[repo]}/{file}'
    for name,url in urls.items():
        try:
            raw=get(url);(out/name).write_bytes(raw)
            rows.append(dict(file=name,url=url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),retrieved_at=datetime.now(timezone.utc).isoformat(),status='acquired'))
        except Exception as e: rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
        print(name,rows[-1]['status'],flush=True)
    (ROOT/'evidence-manifest.json').write_text(json.dumps(dict(model_revision=HF_REV,git_pins=pins,files=rows),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

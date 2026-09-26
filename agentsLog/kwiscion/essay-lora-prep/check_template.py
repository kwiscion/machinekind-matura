"""Render the real pinned Jinja template on synthetic text; no tokenizer or weights."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'evidence-private/python-deps'))
from jinja2 import Environment
from jinja2.sandbox import ImmutableSandboxedEnvironment
import jinja2,markupsafe

def main():
    path=ROOT/'evidence-private/hf-chat_template.jinja'
    env=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True)
    env.globals['raise_exception']=lambda message:(_ for _ in ()).throw(ValueError(message))
    template=env.from_string(path.read_text(encoding='utf-8'))
    messages=[{'role':'user','content':'SYNTHETIC PROMPT'}]
    common=dict(bos_token='<bos>',enable_thinking=False,tools=None)
    prefix=template.render(messages=messages,add_generation_prompt=True,**common)
    ordinary=template.render(messages=messages+[{'role':'assistant','content':'SYNTHETIC ANSWER'}],add_generation_prompt=False,**common)
    assert prefix=='<bos><|turn>user\nSYNTHETIC PROMPT<turn|>\n<|turn>model\n<|channel>thought\n<channel|>'
    assert ordinary=='<bos><|turn>user\nSYNTHETIC PROMPT<turn|>\n<|turn>model\nSYNTHETIC ANSWER<turn|>\n'
    system=template.render(messages=[{'role':'system','content':'SYNTHETIC SYSTEM'}]+messages,add_generation_prompt=True,**common)
    assert system.startswith('<bos><|turn>system\nSYNTHETIC SYSTEM<turn|>\n')
    report=dict(status='PASS',scope='Jinja rendering only; actual tokenizer boundary check remains pending',jinja2_version=jinja2.__version__,template_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),nonthinking_prefix=prefix,ordinary_full_chat=ordinary,ordinary_full_chat_has_empty_thought=False,preparation_rule='Exact nonthinking prefix + original answer + <turn|>; prefix labels masked; no extra BOS/EOS')
    (ROOT/'template-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

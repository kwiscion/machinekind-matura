"""Closed Qwen9B profile; no arbitrary model or control overrides."""
import copy,json,types
MODEL='qwen3.5:9b'
DIGEST='6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7'
WEIGHT={'mediaType':'application/vnd.ollama.image.model','digest':'sha256:dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c','size':6594462816}
SAMPLING={'temperature':1,'top_p':0.95,'top_k':64}
PROFILE='qwen35_9b_thinking_v1'

def install(engine,original_step):
 engine.MODEL=MODEL
 def step(*args,**kwargs):
  body,settings=original_step(*args,**kwargs)
  body['options'].update(SAMPLING)
  return body,settings
 engine.step=step

def wrap_guard(base):
 pins=dict(base.CANONICAL,model=MODEL,native_manifest_sha256=DIGEST,context_length=65536)
 def inventory(root,unused):
  root=base.root_path(root);name='manifests/registry.ollama.ai/library/qwen3.5/9b';files=base.files_under(root)
  base.require(name in files,'Pinned Qwen manifest missing');fp=base.fingerprint(files[name]);base.require(fp['sha256']==DIGEST,'Qwen manifest pin')
  doc=base.read_json(files[name]);weights=[x for x in doc['layers'] if x.get('mediaType') in ('application/vnd.ollama.image.model','application/vnd.ollama.image.projector')]
  base.require(weights==[WEIGHT],'Exact single Qwen container required')
  rows=[dict(path=name,purpose='metadata',**fp)]
  for item in [doc['config'],*doc['layers']]:
   digest=item['digest'];base.require(len(digest)==71 and digest.startswith('sha256:') and all(c in '0123456789abcdef' for c in digest[7:]),'Blob digest')
   row=dict(path='blobs/'+digest.replace(':','-'),purpose='model' if item==WEIGHT else 'metadata',bytes=item['size'],sha256=digest[7:]);base.pin(row);rows.append(row)
  base.require(len({x['path'] for x in rows})==len(rows),'Duplicate blob entry')
  return {'schema':'final_weight_inventory_v1','files':rows}
 def snapshot(s,p,loaded=False):
  base.require(s['version']['version']==pins['runtime_version'],'Runtime version')
  tags=s['tags']['models'];base.require(len(tags)==1 and tags[0]['name']==MODEL and tags[0]['digest']==DIGEST,'Exact isolated Qwen tag')
  models=s['ps']['models'];base.require(len(models)<=1 and (models or not loaded),'Missing/unexpected loaded model')
  for x in models:base.require(x['name']==MODEL and x['digest']==DIGEST and x['context_length']==65536,'Qwen loaded identity/context')
 attrs={k:getattr(base,k) for k in dir(base) if not k.startswith('__')}
 attrs.update(CANONICAL=pins,native_inventory=inventory,verify_snapshot=snapshot)
 return types.SimpleNamespace(**attrs)

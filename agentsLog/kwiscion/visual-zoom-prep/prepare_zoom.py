"""Source-independent full-page plus overlapping-quadrant preparation; CPU only."""
import argparse,copy,hashlib,importlib.util,json,math,shutil
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
SELECTED=('5.1','18','23.2','25')
NOTE=('Pierwsze obrazy zachowują wszystkie pełne oryginalne strony. Następnie dla każdej strony '
      'dodano cztery nakładające się fragmenty w kolejności: lewy górny, prawy górny, lewy dolny, prawy dolny. '
      'To powiększone widoki tych samych materiałów, a nie nowe źródła. Nakładające się obszary powtarzają treść; '
      'nie traktuj powtórzeń jako dodatkowego dowodu. Czytaj fragmenty w kontekście pełnych stron.')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def boxes(width,height):
 if width<2 or height<2:raise ValueError('Image too small')
 # Each tile covers55% of each dimension: central overlap10% (rounding outward).
 x0=width*45//100;x1=(width*55+99)//100;y0=height*45//100;y1=(height*55+99)//100
 return [(0,0,x1,y1),(x0,0,width,y1),(0,y0,x1,height),(x0,y0,width,height)]
def build_exam(source,dest,selected=SELECTED):
 if dest.exists():raise ValueError('Fresh output required')
 adapter=load('zoom_adapter',REPO/'scripts/Bukareszt/matura_package.py');package=adapter.load_package(source)
 by={x['id']:x for x in package['exam']['items']};dest.mkdir(parents=True);items=[];provenance=[];tiles={}
 for index,id in enumerate(selected):
  original=by[id]
  if not original.get('images'):raise ValueError('Every selected case needs original images')
  tile_refs=[]
  for ref in original['images']:
   path=adapter.safe_relative(ref['path'],id);src=source/path;target=dest/path;target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():shutil.copyfile(src,target)
   if sha(target)!=ref['sha256']:raise ValueError('Original image changed')
   if ref['path'] not in tiles:
    tiles[ref['path']]=[]
    with Image.open(src) as image:
     for number,box in enumerate(boxes(*image.size)):
      name='images/tiles/'+sha(src)[:16]+'-'+str(number)+'.png';out=dest/name;out.parent.mkdir(parents=True,exist_ok=True)
      image.crop(box).save(out,format='PNG')
      tiles[ref['path']].append({'path':name,'sha256':sha(out),'box':list(box),'original_dimensions':list(image.size)})
   tile_refs.extend({'path':x['path'],'sha256':x['sha256']} for x in tiles[ref['path']])
  order=('control','zoom') if index%2==0 else ('zoom','control')
  for arm in order:
   item=copy.deepcopy(original);item['id']=id+'-'+arm
   if arm=='zoom':item['images'].extend(tile_refs);item['image_layout_note']=NOTE
   for field in original:
    if field not in ('id','images'):assert item[field]==original[field]
   assert item['images'][:len(original['images'])]==original['images']
   items.append(item);provenance.append({'slot_id':item['id'],'source_id':id,'arm':arm,'original_image_count':len(original['images']),'total_image_count':len(item['images']),'question_sha256':hashlib.sha256(original['question'].encode()).hexdigest(),'source_text_sha256':hashlib.sha256(original.get('source_text','').encode()).hexdigest()})
 exam=copy.deepcopy(package['exam']);exam['items']=items;exam['exam_id']='visual-zoom-known-validation-v1'
 if 'max_points' in exam:exam['max_points']=sum(x['max_points'] for x in items)
 template={'exam_id':exam['exam_id'],'answers':[{'id':x['id'],'answer':''} for x in items]}
 for name,data in [('exam.json',exam),('answers-template.json',template)]:
  (dest/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
 adapter.load_package(dest)
 return {'algorithm':'full originals first, then TL/TR/BL/BR per original;55% dimensions;10% central overlap; no resizing','slots':provenance,'tiles':tiles,'source_exam_sha256':sha(source/'exam.json'),'prepared_exam_sha256':sha(dest/'exam.json'),'note_sha256':hashlib.sha256(NOTE.encode()).hexdigest()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime-reference',type=Path,required=True);a=p.parse_args()
 private=(REPO/'agentsLog/kwiscion/private').resolve();root=a.output.resolve()
 if not root.is_relative_to(private) or root.exists():raise ValueError('Fresh project private output')
 root.mkdir();provenance=build_exam(a.source.resolve(),root/'exam')
 (root/'source-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf8')
 prep=load('zoom_recovery_prepare',REPO/'agentsLog/kwiscion/final-package-prep/prepare_recovery_package.py');reference=json.loads(a.runtime_reference.read_text(encoding='utf8'))
 from types import SimpleNamespace
 options=SimpleNamespace(exam_dir=root/'exam',output=root/'package-v1',essay_id=None,no_essay=True,cache=reference['cache'],binary=reference['binary'],lock=reference['lock'],minutes=60,inject_faults=False)
 m=prep.prepare(options)
 assert m['max_calls']==32 and m['max_requested_tokens']==1179648
 public={'schema':'visual_zoom_preparation_v1','status':'PREPARED_NOT_AUTHORIZED','selected_source_ids':list(SELECTED),'slots':provenance['slots'],'algorithm':provenance['algorithm'],'note':NOTE,'note_sha256':provenance['note_sha256'],'code_sha256':sha(Path(__file__)),'scheduler_sha256':m['files']['recovery_harness.py'],'prepared_manifest_sha256':sha(root/'package-v1/launch.json'),'max_calls':32,'max_requested_tokens':1179648,'max_seconds':3600,'context':65536,'initial_output_cap':32768,'thinking':True,'temperature':'omitted','model':m['model'],'weights_model_plus_projector_bytes':7556497632,'aggregate_limit_bytes':8800000000,'quality_scope':'Four deliberately selected known-validation source items; no whole-exam gain claim'}
 (root/'public-preparation.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({'manifest_sha256':public['prepared_manifest_sha256'],'slots':len(m['ids']),'model_calls':0}))
if __name__=='__main__':main()

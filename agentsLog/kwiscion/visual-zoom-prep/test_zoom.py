import importlib.util,json,tempfile,unittest,hashlib
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('zoom',Path(__file__).with_name('prepare_zoom.py'));z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
class Tests(unittest.TestCase):
 def test_coverage_and_overlap(self):
  for w,h in ((100,100),(101,103)):
   boxes=z.boxes(w,h);self.assertEqual(boxes[0][:2],(0,0));self.assertEqual(boxes[-1][2:],(w,h));self.assertGreaterEqual(boxes[0][2]-boxes[1][0],w*.1);self.assertGreaterEqual(boxes[0][3]-boxes[2][1],h*.1)
   self.assertTrue(all(any(a<=x<c and b<=y<d for a,b,c,d in boxes) for x in range(w) for y in range(h)))
 def test_matched_originals_and_generic_only_note(self):
  with tempfile.TemporaryDirectory() as td:
   source=Path(td)/'source';source.mkdir();(source/'images').mkdir();image=Image.new('RGB',(100,100),(20,40,60));image.save(source/'images/page.png');digest=z.sha(source/'images/page.png')
   items=[{'id':id,'max_points':1,'question':'Invented neutral question '+id,'source_text':'Original synthetic material','answer_format':'A short answer','images':[{'path':'images/page.png','sha256':digest}]} for id in ('a','b','c','d')]
   exam={'exam_id':'synthetic','instructions':'Original shared instruction','items':items};template={'exam_id':'synthetic','answers':[{'id':x['id'],'answer':''} for x in items]}
   (source/'exam.json').write_text(json.dumps(exam));(source/'answers-template.json').write_text(json.dumps(template));out=Path(td)/'built';meta=z.build_exam(source,out,('a','b','c','d'));got=json.loads((out/'exam.json').read_text(encoding='utf8'))
   self.assertEqual([x['id'] for x in got['items']],['a-control','a-zoom','b-zoom','b-control','c-control','c-zoom','d-zoom','d-control']);self.assertEqual(got['instructions'],exam['instructions']);self.assertEqual(z.sha(out/'images/page.png'),digest)
   by={x['id']:x for x in items}
   for item,slot in zip(got['items'],meta['slots']):
    before=by[slot['source_id']]
    for field in ('question','source_text','answer_format'):self.assertEqual(item[field],before[field])
    self.assertEqual(item['images'][0],before['images'][0]);self.assertEqual(len(item['images']),5 if slot['arm']=='zoom' else 1)
    self.assertEqual(item.get('image_layout_note'),z.NOTE if slot['arm']=='zoom' else None)
   with Image.open(out/meta['tiles']['images/page.png'][0]['path']) as tile:self.assertEqual(tile.size,(55,55))
   with self.assertRaises(ValueError):z.build_exam(source,out,('a','b','c','d'))
 def test_only_canonical_gemma_pair_under_limit(self):
  g=z.load('zoom_weight_guard',z.REPO/'agentsLog/kwiscion/final-package-prep/guard.py');p=g.CANONICAL
  self.assertEqual(p['model'],'gemma4:12b-it-q4_K_M');self.assertEqual(p['model_weight']['bytes']+p['projector']['bytes'],7556497632);self.assertLess(7556497632,8800000000)
if __name__=='__main__':unittest.main()

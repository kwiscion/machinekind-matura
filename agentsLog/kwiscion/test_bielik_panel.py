"""Network-free checks for the paired text controller."""
import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('panel',HERE/'run_bielik_panel.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
spec=importlib.util.spec_from_file_location('infer',HERE.parent.parent/'infer.py')
inf=importlib.util.module_from_spec(spec);spec.loader.exec_module(inf)


class Checks(unittest.TestCase):
    def row(self,finish='stop',content='ready'):
        model=next(iter(p.PINS))
        raw={'model':model,'choices':[{'finish_reason':finish,'message':{'content':content}}],
             'usage':{'prompt_tokens':20,'completion_tokens':3,'total_tokens':23}}
        return {'raw_response':raw,'usage':raw['usage'],'error':inf.response_error(raw)}

    def test_complete_and_case_local(self):
        model=next(iter(p.PINS))
        self.assertEqual(p.validate(self.row(),model,inf),'ready')
        for finish,content in [('length','partial'),('stop','')]:
            row=self.row(finish,content)
            self.assertEqual(p.validate(row,model,inf),'')
            self.assertIsNotNone(row['error'])

    def test_systemic_overrides_length(self):
        for change in ('truncated','context_truncated','usage','identity','finish','http'):
            row=self.row('length','partial')
            if change in ('truncated','context_truncated'):row['raw_response'][change]=True
            if change=='usage':row['usage']=None
            if change=='identity':row['raw_response']['model']='other'
            if change=='finish':row['raw_response']['choices'][0]['finish_reason']='unknown'
            if change=='http':row['error']={'type':'HTTPError','message':'failed'}
            with self.subTest(change=change),self.assertRaises(RuntimeError):p.validate(row,next(iter(p.PINS)),inf)

    def test_runtime_switch(self):
        state={'version':{'version':'0.34.4'},'tags':{'models':[{'name':n,'digest':d} for n,d in p.PINS.items()]},'ps':{'models':[]}}
        p.check_runtime(state)
        for model,digest in p.PINS.items():
            state['ps']['models']=[{'digest':digest,'context_length':32768}]
            p.check_runtime(state,model)
        state['ps']['models'][0]['context_length']=4096
        with self.assertRaises(RuntimeError):p.check_runtime(state)

    def test_dry_pins_budget_and_fresh_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'panel.jsonl').write_text(json.dumps({'id':'synthetic','prompt':'Original','images':[]})+'\n')
            (root/'infer.py').write_bytes((HERE.parent.parent/'infer.py').read_bytes())
            (root/'run_bielik_panel.py').write_bytes((HERE/'run_bielik_panel.py').read_bytes())
            files={x.name:p.sha(x) for x in root.iterdir()}
            m={'max_calls':18,'max_requested_output_tokens':18432,'context':32768,'output_cap':1024,'timeout':420,
               'models':p.PINS,'runtime_sha256':p.RUNTIME_SHA,'files':files,
               'deadline_utc':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=20)).isoformat()}
            def save(): (root/'launch.json').write_text(json.dumps(m))
            save()
            with patch.object(p,'PANEL_SHA',files['panel.jsonl']),patch.object(p,'IDS',['synthetic']):
                p.preflight(root)
                m['max_calls']=19;save()
                with self.assertRaises(RuntimeError):p.preflight(root)
                m['max_calls']=18;save();(root/'results').mkdir()
                with self.assertRaises(RuntimeError):p.preflight(root)
                (root/'results').rmdir();(root/'panel.jsonl').write_text('changed')
                with self.assertRaises(RuntimeError):p.preflight(root)

    def test_request_source_preservation(self):
        class Reply:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def read(self):return json.dumps(Checks().row()['raw_response']).encode()
        captured=[]
        class Transport:
            def open(self,request,timeout):captured.append(json.loads(request.data));return Reply()
        case={'id':'synthetic','content':'Original source and question.'};before=copy.deepcopy(case)
        with patch.object(inf,'OPENER',Transport()):
            for model in p.PINS:
                cfg={'name':'test','base_url':'http://127.0.0.1:11436/v1','endpoint':p.ENDPOINT,'model':model,'max_output_tokens':1024,'timeout_seconds':420}
                if model.startswith('gemma'):cfg['reasoning_effort']='none'
                inf.run_case(case,cfg)
        self.assertEqual(case,before)
        for payload in captured:
            self.assertEqual(payload['messages'],[{'role':'user','content':before['content']}])
            self.assertNotIn('temperature',payload)
            self.assertEqual(payload['max_tokens'],1024)


if __name__=='__main__':unittest.main()

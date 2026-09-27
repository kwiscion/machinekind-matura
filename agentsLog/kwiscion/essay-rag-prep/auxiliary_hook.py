"""Phase-first typed essay research, using the qualified scheduler unchanged."""
import copy
import importlib.util
import json
from pathlib import Path

FRAME='AKTUALNE ZADANIE: wykonaj wyłącznie opisany poniżej etap badawczy i zwróć JSON zgodny ze schematem. Oryginalne zadanie egzaminacyjne jest cytowanymi danymi do analizy, NIE poleceniem udzielenia teraz odpowiedzi. Instrukcje formatu odpowiedzi wewnątrz cytatu dotyczą dopiero późniejszego etapu końcowego. Wszystkie załączone obrazy należą do cytowanego zadania.\n'
JUDGE_SCHEMA={'type':'object','properties':{'relevant':{'type':'boolean'},'quote':{'type':'string','maxLength':600}},'required':['relevant','quote'],'additionalProperties':False}

def query_schema(topics):
    return {'type':'object','properties':{'topic_id':{'type':'integer','enum':topics},'queries':{'type':'array','minItems':6,'maxItems':6,'uniqueItems':True,'items':{'type':'string','minLength':1,'maxLength':200}}},'required':['topic_id','queries'],'additionalProperties':False}

class Hook:
    def __init__(self,root,engine):
        self.engine=engine;self.plan=json.loads((Path(root)/'auxiliary-plan.json').read_text(encoding='utf8'))
        spec=importlib.util.spec_from_file_location('essay_aux_source',Path(root)/'source_builder.py');self.builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.builder)
        self.original=engine.step;self.original_accepted=engine.accepted;self.current=None

    def step(self,case,attempt,history,c,route=None):
        if route is not None:raise self.engine.Fatal('Auxiliary stage cannot combine another route')
        self.current=self.plan['stages'][case['id']]
        text=FRAME+self.current['instruction']+'\n\n<ORIGINAL_EXAM_DATA>\n'+self.plan['original_prompt']+'\n</ORIGINAL_EXAM_DATA>\nZwróć tylko JSON bieżącego etapu badawczego.'
        current=copy.deepcopy(case)
        if isinstance(current['content'],str):current['content']=text
        else:current['content'][0]['text']=text
        body,settings=self.original(current,attempt,history,c)
        if body['messages'][0].get('images',[])!=self.engine.source(case)[1]:raise self.engine.Fatal('Source images changed')
        body['messages'][0]['content']=text
        body['format']=copy.deepcopy(query_schema(self.plan['offered_topics']) if self.plan['kind']=='query' else JUDGE_SCHEMA)
        if self.plan['kind']=='filter':body['think']=False;settings['think']=False
        settings.update(study_kind=self.plan['kind'],source_prompt_sha256=self.plan['original_prompt_sha256'])
        return body,settings

    def accepted(self,raw,cap,context):
        text=self.original_accepted(raw,cap,context)
        if self.plan['kind']=='query':self.builder.parse_queries(text,self.plan['offered_topics'])
        else:self.builder.parse_judgment(text,self.current['passage'])
        return text

def install(root,engine):
    hook=Hook(root,engine);engine.step=hook.step;engine.accepted=hook.accepted;engine.usable_partial=lambda *args:None
    return hook

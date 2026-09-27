"""Essay-specific staged retrieval using unchanged research/filter/writer prompts."""
import copy,json,re
import source_builder as builder
import auxiliary_hook as auxiliary

TOPIC_LINE=re.compile(r'^\s*(?:(Temat)\s+)?([1-9][0-9]*)[.)]\s+(.+)$',re.M)

def offered_topics(item):
    text=item['question'];matches=list(TOPIC_LINE.finditer(text))
    choices=all(bool(row[1]) for row in matches) if matches else False
    choices=choices or bool(re.search(r'wybierz\s+(?:jeden|jeden\s+z)|choose\s+one|trzy\s+tematy|dwa\s+tematy',text,re.I))
    if choices and len(matches) in (2,3) and [int(row[2]) for row in matches]==list(range(1,len(matches)+1)) and len({bool(row[1]) for row in matches})==1:
        return list(range(1,len(matches)+1))
    # Explicitly typed single-topic essays have one implicit topic. This ID is
    # internal research metadata, never an added organizer task or renamed ID.
    if not choices:
        return [1]
    raise ValueError('Ambiguous offered essay topics; preserve direct')

def is_essay(item):
    tags=[item.get(name) for name in ('type','kind','task_type','answer_type')]
    if any(isinstance(tag,str) and tag.casefold() in ('essay','wypracowanie','long_form','long-form','extended_response') for tag in tags):return True
    text=item.get('question','')
    return len(list(TOPIC_LINE.finditer(text))) in (2,3) and bool(re.search(r'wypracowani|essay|(?:wypowiedź|wypowiedzi|write)[\s\S]{0,200}(?:300|400|500)|(?:300|400|500)\s*(?:wyraz|słów|words)',text,re.I))

class EssaySupport:
    def __init__(self,hook):self.hook=hook;self.plans={}
    def plan(self,source):
        return builder.parse_queries(self.hook.answer('essay_query:'+source),offered_topics(self.hook.items[source]))
    def retrieval(self,source):
        h=self.hook;path=h.out/(source+'.essay-retrieval.json')
        if path.exists():return builder.read(path)
        h.ensure_index();plan=self.plan(source);rows=[];traces=[]
        for index,query in enumerate(plan['queries']):
            h.check_optional_clock()
            before=h.index.stat()
            if (before.st_ino,before.st_size,before.st_mtime_ns)!=(h.index_stat.st_ino,h.index_stat.st_size,h.index_stat.st_mtime_ns):raise h.engine.Fatal('Full index changed')
            found=h.search.retrieve(h.index,query,k=5,seconds=min(20,max(1,h.active_deadline-h.current_clock()-15)))
            traces.append({k:v for k,v in found.items() if k!='passages'})
            for rank,row in enumerate(found['passages'],1):rows.append(dict(row,query_index=index,rank=rank,text_sha256=builder.tsha(row['text'])))
        packet=dict(snapshot_revision=builder.REVISION,index_sha256=h.plan['index_sha256'],query_module_sha256=builder.sha(h.root/'search_query.py'),full_snapshot_complete=True,queries=plan['queries'],passages=rows,traces=traces,topic_id=plan['topic_id'])
        builder.validate_retrieval(packet,plan['queries'],h.plan['index_sha256'],builder.sha(h.root/'search_query.py'))
        from deadline_runtime import atomic
        atomic(path,packet);return packet
    def suffix(self,stage):
        h=self.hook;source=stage['source_id'];kind=stage['kind']
        if kind=='essay_query':return builder.QUERY+'\nDozwolone numery tematów: '+json.dumps(offered_topics(h.items[source]))
        packet=self.retrieval(source);rows=packet['passages'];plan=self.plan(source)
        if kind=='essay_judge':
            rank=stage['rank'];row=rows[rank] if rank<len(rows) else None
            return builder.FILTER+(json.dumps(dict(chosen_topic_id=plan['topic_id'],research_question=plan['queries'][row['query_index']],**row),ensure_ascii=False) if row else 'Brak fragmentu; zwróć {"relevant":false,"quote":""}.')
        path=h.out/(source+'.essay-admission.json')
        if path.exists():accepted=builder.read(path)['accepted']
        else:
            accepted=[];seen=set();decisions=[]
            for rank,row in enumerate(rows):
                answer=h.answer('essay_judge:'+str(rank)+':'+source);quote=builder.useful_quote(answer,row['text']) if isinstance(answer,str) else None;key=(row['article_id'],row['start'],row['end'],row['text_sha256'])
                decisions.append(dict(rank=rank,answer=answer,accepted=quote is not None))
                if quote and key not in seen:accepted.append(dict(row,verified_literal_quote=quote));seen.add(key)
            from deadline_runtime import atomic
            # Optional evidence alone is trimmed; the original prompt and images
            # remain byte-exact. Keep highest-ranked accepted passages.
            removed=[]
            while accepted and len((builder.WRITER+json.dumps(dict(chosen_topic_id=plan['topic_id'],research_questions=plan['queries'],evidence=accepted),ensure_ascii=False)).encode('utf8'))>14000:removed.append(accepted.pop())
            atomic(path,dict(accepted=accepted,decisions=decisions,removed_for_optional_byte_budget=removed))
        return builder.WRITER+json.dumps(dict(chosen_topic_id=plan['topic_id'],research_questions=plan['queries'],evidence=accepted),ensure_ascii=False) if accepted else ''
    def step(self,case,attempt,history,config,route=None):
        h=self.hook;stage=h.current;kind=stage['kind'];source=stage['source_id'];suffix=self.suffix(stage);original=h.rows[source]['prompt'];aux=kind!='essay_final'
        text=auxiliary.FRAME+suffix+'\n\n<ORIGINAL_EXAM_DATA>\n'+original+'\n</ORIGINAL_EXAM_DATA>\nZwróć tylko JSON bieżącego etapu badawczego.' if aux else original+suffix
        current=copy.deepcopy(case)
        if isinstance(current['content'],str):current['content']=text
        else:current['content'][0]['text']=text
        body,settings=h.original(current,attempt,history,config,route)
        if body['messages'][0].get('images',[])!=h.engine.source(case)[1]:raise h.engine.Fatal('Essay source images changed')
        if aux:
            cap=(768 if kind=='essay_query' else 384) if attempt==0 else 1024
            body.update(think=False,format=auxiliary.query_schema(offered_topics(h.items[source])) if kind=='essay_query' else auxiliary.JUDGE_SCHEMA)
            body['messages'][0]['content']=text;body['options']['num_predict']=cap;settings.update(cap=cap,think=False)
        else:
            cap=16384 if attempt==0 else 8192
            body['think']=attempt==0;body['options']['num_predict']=cap
            settings.update(cap=cap,think=attempt==0,essay_writer_profile='16384_thinking_then_8192_off')
        settings.update(study_kind=kind,source_id=source,phase=stage['phase']);return body,settings
    def accepted(self,text):
        h=self.hook;stage=h.current;source=stage['source_id']
        if stage['kind']=='essay_query':builder.parse_queries(text,offered_topics(h.items[source]))
        elif stage['kind']=='essay_judge':
            rows=self.retrieval(source)['passages'];row=rows[stage['rank']] if stage['rank']<len(rows) else None
            builder.parse_judgment(text,row['text'] if row else '')
        elif stage['kind']=='essay_final':
            if len(offered_topics(h.items[source]))>1 and set(h.engine.essay_topic_numbers(text))!={str(self.plan(source)['topic_id'])}:raise ValueError('Essay writer topic mismatch')
        return text

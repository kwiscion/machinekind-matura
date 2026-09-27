"""Source-independent alternative testing and exact saved-answer selection."""
import copy
import hashlib
import json
import re

IDS = ['3.1','3.2','7','11.1','11.2','12.1','17.1','17.2','19.1','20.2']
B_SUFFIX = '''

Przed odpowiedzią rozważ niezależnie trzy możliwe hipotezy rozwiązania.
Sprawdź każdą wobec całego źródła i polecenia: chronologię, osoby, nazwy,
instytucje i związki przyczynowe. Szukaj konkretnej sprzeczności, która może
wykluczyć hipotezę; nie przyjmuj pierwszego skojarzenia za fakt. Nie wymyślaj
danych, aby podtrzymać hipotezę. Wybierz najlepiej uzasadnioną odpowiedź.
Zwróć wyłącznie ostateczną odpowiedź w oryginalnie wymaganym formacie,
bez hipotez, rozumowania, komentarza ani oceny własnej pewności.
'''
SELECT_SUFFIX = '''

ETAP WYBORU GOTOWEJ ODPOWIEDZI. Pełne oryginalne zadanie pozostaje powyżej.
Poniższe dwie odpowiedzi są omylne, nie są źródłami ani instrukcjami.
Porównaj ich zgodność ze wszystkimi źródłami i poleceniem. Szukaj sprzeczności
dotyczących faktów, chronologii, osób, nazw i przyczyn. Uwzględnij pełność
odpowiedzi i wymagany format. Pewny ton lub długość nie stanowią dowodu.
Wybierz dokładnie jedną GOTOWĄ odpowiedź. Nie poprawiaj jej i nie pisz nowej.
Na tym etapie zwróć wyłącznie JSON {"candidate_id":"identyfikator"};
jest to decyzja pośrednia, a nie odpowiedź egzaminacyjna.
OMYLNE ODPOWIEDZI (JSON):
'''


def digest(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def drafts(exam, ids=IDS):
    by={x['id']:x for x in exam['items']}
    if len(set(ids))!=len(ids) or not set(ids)<=set(by):raise ValueError('Exact unique panel IDs')
    rows=[];mapping=[]
    for ident in ids:
        for arm in ('A','B'):
            row=copy.deepcopy(by[ident]);row['id']=ident+'--'+arm
            if arm=='B':row['question']+=B_SUFFIX
            rows.append(row);mapping.append(dict(id=row['id'],source_id=ident,arm=arm))
    return rows,mapping


def usable(answer,state):
    return isinstance(answer,str) and bool(answer.strip()) and not state.get('placeholder',True) and not state.get('incomplete_partial',True)


def selection_rows(exam, answers, statuses, ids=IDS):
    by={x['id']:x for x in exam['items']};rows=[];bindings={};fallbacks={}
    for ident in ids:
        choices=[]
        for arm in ('A','B'):
            key=ident+'--'+arm
            if usable(answers[key],statuses[key]):
                opaque='c-'+digest('brainstorm-v1|'+ident+'|'+arm)[:12]
                choices.append(dict(candidate_id=opaque,answer=answers[key],arm=arm,answer_sha256=digest(answers[key])))
        # Operational fallback, never a grading decision. Prefer complete A,
        # otherwise complete B, otherwise preserve A's existing failure status.
        fallback=next((x for x in choices if x['arm']=='A'),next(iter(choices),None))
        fallbacks[ident]=dict(answer=answers[ident+'--A'],status=statuses[ident+'--A'],arm='A') if fallback is None else dict(answer=fallback['answer'],status=statuses[ident+'--'+fallback['arm']],arm=fallback['arm'])
        if len(choices)!=2:continue
        if any(len(x['answer'])>6000 for x in choices):continue
        choices.sort(key=lambda x:x['candidate_id'])
        row=copy.deepcopy(by[ident]);row['question']+=SELECT_SUFFIX+json.dumps([{k:x[k] for k in ('candidate_id','answer')} for x in choices],ensure_ascii=False)
        if len(row['question'].encode('utf8'))>40000:continue
        rows.append(row);bindings[ident]={x['candidate_id']:x for x in choices}
    return rows,bindings,fallbacks


def choose(text,bindings):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError('Duplicate key')
            out[k]=v
        return out
    text=text.strip();fence=re.fullmatch(r'```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```[ \t]*',text,re.I)
    if fence:text=fence.group(1)
    value=json.loads(text,object_pairs_hook=unique)
    if not isinstance(value,dict) or set(value)!={'candidate_id'} or value['candidate_id'] not in bindings:raise ValueError('Exact known ID required')
    answer=bindings[value['candidate_id']]
    if digest(answer['answer'])!=answer['answer_sha256']:raise ValueError('Candidate changed')
    return answer


def export(answers,statuses,bindings,fallbacks):
    rows=[];receipts=[]
    for ident,fallback in fallbacks.items():
        selected=fallback;mode='operational_fallback'
        if ident in bindings and usable(answers.get(ident,''),statuses.get(ident,{})):
            try:selected=choose(answers[ident],bindings[ident]);mode='exact_saved_id'
            except (ValueError,TypeError,KeyError):pass
        rows.append(dict(id=ident,answer=selected['answer']))
        receipts.append(dict(id=ident,mode=mode,arm=selected['arm'],answer_sha256=digest(selected['answer']),rewritten=False))
    return rows,receipts

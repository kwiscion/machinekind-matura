"""Build draft records from original prose and source-specific fact cards."""
import hashlib, json, re, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent
STATUS='synthetic_draft_pending_independent_review'

TOPICS=[
('augustus','antiquity','Wyjaśnij, dlaczego zachowanie instytucji republikańskich nie oznaczało odtworzenia republiki za Augusta. Rozważ podstawy militarne, prawne i społeczne pryncypatu.'),
('investiture','middle_ages','Oceń znaczenie sporu o inwestyturę dla relacji władzy duchownej i świeckiej. Uwzględnij interesy uczestników, Canossę i kompromis wormacki.'),
('augsburg','early_modern','Oceń osiągnięcia i ograniczenia pokoju augsburskiego jako rozwiązania konfliktu wyznaniowego. Rozróżnij prawa władców i sytuację poddanych.'),
('vienna','nineteenth_century','Wyjaśnij, jak kongres wiedeński godził prawa dynastii z równowagą mocarstw. Przeanalizuj trzy konkretne rozstrzygnięcia polityczne.'),
('industrial','nineteenth_century','Wyjaśnij, jak mechanizacja, nowe źródła energii i organizacja pracy zmieniły gospodarkę oraz społeczeństwo podczas brytyjskiej rewolucji przemysłowej.'),
('meiji','nineteenth_century','Oceń znaczenie przemian okresu Meiji dla budowy nowoczesnego państwa japońskiego. Rozważ centralizację władzy, przemiany społeczne oraz rozwój gospodarczy.'),
('league','twentieth_century','Wyjaśnij ograniczenia bezpieczeństwa zbiorowego realizowanego przez Ligę Narodów. Rozważ konstrukcję organizacji, interesy państw oraz reakcje na agresję.'),
('marshall','twentieth_century','Oceń gospodarcze i polityczne znaczenie planu Marshalla dla powojennej Europy. Rozważ mechanizm pomocy, współpracę państw i podział kontynentu.'),
]

# Actor/event/date/consequence cards were assembled from the acquired general references.
# Consequences marked fact_and_inference combine cited events with original reasoning.
FACTS={
'augustus':[
('Oktawian i Antoniusz','Klęska sił Antoniusza pod Akcjum, następnie zajęcie Egiptu.','31–30 BCE','Usunięcie najgroźniejszego rywala.','War with Antony and Cleopatra',[2]),
('August i senat','Przyznanie Augustowi zarządu prowincji z większością legionów; zachowanie prowincji senatorskich.','27 BCE','Asymetria siły mimo formalnego podziału kompetencji.','First settlement / Control of provinces',[2]),
('August','Tytuł Augusta w 27 BCE, rezygnacja z nieprzerwanego konsulatu w 23 BCE; władza trybuńska i nadrzędna prokonsularna.','27–23 BCE','Dominacja nie wymagała piastowania każdego urzędu.','Title of Augustus; Second settlement; Powers of the tribune',[3]),
('August i senatorowie','Zachowane kariery senatorskie, większy dostęp innych senatorów do konsulatu po rezygnacji Augusta.','23 BCE onward','Włączenie elit ułatwiało trwałość ustroju; interpretacja autora.','Resignation from the consulship; Control of provinces',[4]),
],
'investiture':[
('Biskupi i monarchowie','Biskupi łączyli godności kościelne z rolą właścicieli ziemi i uczestników władzy świeckiej.','11th century','Nominacje dotyczyły religii i politycznego zaplecza monarchii.','Background',[2]),
('Grzegorz VII i Henryk IV','Ekskomunika Henryka oraz zwolnienie poddanych z przysięgi wierności.','1076','Sankcja religijna wzmacniała politycznych przeciwników króla.','Henry IV and Pope Gregory VII',[3]),
('Henryk IV i Grzegorz VII','Pojednanie w Canossie, potem odnowienie konfliktu; opozycja wybiera Rudolfa.','1077 onward','Canossa nie była ostatecznym zakończeniem sporu.','Henry IV and Pope Gregory VII',[3]),
('Henryk V i Kalikst II','Konkordat wormacki: rezygnacja z inwestytury pierścieniem i pastorałem, zachowanie więzi świeckich i roli cesarza w wyborach w Niemczech.','1122','Rozróżnienie kompetencji, nie nowoczesny rozdział państwa i Kościoła.','Concordat of Worms (1122)',[4]),
],
'augsburg':[
('Ferdynand, Karol V, stany Rzeszy','Pokój uznał katolicyzm i luteranizm; Ferdynand negocjował w imieniu Karola.','1555','Legalne współistnienie wyznań w cesarstwie.','Overview',[2]),
('Władcy terytorialni i poddani','Władcy decydowali o wyznaniu terytorium; przewidziano emigrację niezgadzających się poddanych, z ograniczeniami stanowymi.','1555','Rozwiązanie nie gwarantowało każdemu wolnej praktyki wyznania w miejscu zamieszkania.','Overview; Main principles',[3]),
('Wyznania reformowane','Kalwinizm nie otrzymał odrębnego równorzędnego statusu w ugodzie.','1555','Nie objęto całej różnorodności reformacji; źródło wskazuje złożoność praktyki wobec zwolenników Variata.','Overview; Problems',[4]),
('Zwierzchnicy księstw kościelnych','Zastrzeżenie kościelne nakazywało ustąpienie konwertującego zwierzchnika; późniejszy konflikt koloński ujawnił napięcia.','1555; 1583–1588','Wyjątek od zasady religii władcy miał chronić katolickie terytoria.','Main principles; Aftermath',[4]),
],
'vienna':[
('Mocarstwa i Talleyrand','Kongres po upadku Napoleona; francuska dyplomacja wróciła do głównego grona negocjatorów.','1814–1815','Legitymizm służył również obronie interesów Francji.','The four great powers and Bourbon France; Talleyrand',[1,2]),
('Rosja, Prusy, Austria, Wielka Brytania, Francja','Spór o Księstwo Warszawskie i Saksonię zakończony podziałem terytoriów: Królestwo Polskie związane z carem, Poznańskie pruskie, wolny Kraków, zachowana część Saksonii.','1815','Ograniczenie maksymalnych roszczeń; aspiracje narodowe podporządkowane mocarstwom.','Polish-Saxon question; Final Act',[3]),
('Prusy i Niderlandy','Zjednoczone Niderlandy oraz pruskie nabytki nad Renem wzmacniały otoczenie Francji.','1815','Funkcja równoważenia siły; interpretacja autora.','Final Act',[4]),
('Państwa niemieckie i Austria','Związek Niemiecki z 39 państw; Austria otrzymała Lombardię i Wenecję.','1815','Nie odtworzono po prostu mapy przednapoleońskiej.','Final Act',[4]),
],
'industrial':[
('Hargreaves i Arkwright','Wielowrzecionowa przędzarka Hargreavesa była używana także w domach; napęd wodny Arkwrighta stosowano w zakładzie w Cromford.','1760s–1770s','Mechanizacja miała zróżnicowane formy i sprzyjała większej skali produkcji.','Textile manufacture',[2]),
('James Watt i przemysł brytyjski','Rozwój zastosowań pary i koksu przy dalszym znaczeniu energii wodnej.','late 18th–early 19th century','Stopniowe ograniczanie zależności przemysłu od cieków wodnych; sektory wzmacniały wzajemny popyt.','Steam power; Iron industry',[3]),
('Robotnicy i przedsiębiorcy','System fabryczny i migracja do ośrodków przemysłowych, w tym Manchesteru.','late 18th–19th century','Zmiana organizacji pracy, wzrost miast i problemy warunków życia.','Factories and urbanisation; Housing',[4]),
('Dzieci, pracodawcy i parlament','Praca dzieci w niebezpiecznych warunkach; regulacje fabryczne z 1833 roku.','1833; preceding industrialization','Wzrost produkcji nie usuwał automatycznie kosztów społecznych.','Child labour',[4]),
],
'meiji':[
('Cesarz Meiji i przeciwnicy Tokugawów','Restauracja cesarska po obaleniu siogunatu.','1868','Otwarcie drogi do przebudowy państwa pod presją zewnętrzną.','Lead; January Proclamation, 1868',[1,2]),
('Rząd i panowie domen','Zniesienie domen w 1871 roku, organizacja prefektur; część elit przeszła do nowej arystokracji i biurokracji.','1871–1872','Centralizacja nie oznaczała całkowitego usunięcia dawnych elit.','Abolition of the Domains, 1868–1873',[2]),
('Samurajowie i rząd','Pobór w 1873 roku oraz likwidacja przywilejów i zamiana świadczeń na obligacje; opór samurajski.','1873–1870s','Budowa armii masowej wiązała się z naruszeniem pozycji dawnych wojowników.','Abolition of the samurai class',[3]),
('Rząd, przedsiębiorcy i rolnicy','Zakłady przemysłowe, kolej i zagraniczne technologie; eksport jedwabiu i obciążenia podatkowe rolników finansowały rozwój.','Meiji era','Modernizacja łączyła nowe przemysły z zasobami sektora rolnego.','Industrial growth',[4]),
],
'league':[
('Liga Narodów i członkowie','Brak własnych sił zbrojnych; jednomyślność z wyjątkami; USA nie przystąpiły.','1920 onward','Instytucje zależały od zgody i zasobów państw.','Permanent organs; General weaknesses',[2]),
('Japonia, Chiny i komisja Lyttona','Agresja w Mandżurii od 1931; raport 1932 i stanowisko Ligi nie doprowadziły do wycofania Japonii, która zdecydowała o wystąpieniu.','1931–1933','Potępienie nie było równoznaczne ze skutecznym egzekwowaniem prawa.','Mukden Incident',[3]),
('Włochy, Etiopia i Liga','Włoska napaść; sankcje nie objęły ropy, nie zamknięto Kanału Sueskiego.','1935–1936','Ograniczony zakres presji nie powstrzymał podboju.','Italian invasion of Abyssinia',[4]),
('Państwa wykonujące sankcje','Interesy mocarstw i obawy przed eskalacją ograniczały wspólne działanie.','1930s','Bezpieczeństwo zbiorowe wymagało gotowości ponoszenia kosztów; synteza autora.','General weaknesses; Italian invasion of Abyssinia',[1,4,5]),
],
'marshall':[
('George Marshall i USA','Zapowiedź pomocy w 1947 roku, rozpoczęcie programu w 1948.','1947–1948','Odbudowa Europy oraz polityczna stabilizacja stanowiły powiązane cele.','Lead; Marshall speech',[1]),
('Gospodarki europejskie i USA','Dostawy, inwestycje i modernizacja wspierały odbudowę; część produkcji odradzała się wcześniej, skala dodatkowego efektu pozostaje dyskutowana.','1940s–early 1950s','Plan był jednym z czynników, nie jedynym źródłem wzrostu.','Wartime destruction; Effects and legacy; Criticism',[2]),
('OEEC i państwa uczestniczące','OEEC koordynowała alokację pomocy i przepływ dóbr; celem było również ograniczanie barier.','from 1948','Praktyka współpracy nie była jeszcze jednolitym rynkiem.','Expenditures; Lead',[3]),
('USA, ZSRR i państwa Europy Wschodniej','USA dążyły do ograniczenia wpływów komunistycznych; ZSRR odmówił udziału i blokował go państwom swojego bloku, w tym Polsce.','1947 onward','Program utrwalał więzi Zachodu i pogłębiał istniejący podział; synteza autora.','Soviet negotiations; Lead',[4]),
],
}

ALIASES={
'augustus':['August','Oktawian August','Octavian','pryncypat Augusta','Augustan principate'],
'investiture':['spór o inwestyturę','Investiturstreit','Canossa','Concordat of Worms','konkordat wormacki'],
'augsburg':['pokój augsburski','Augsburger Religionsfrieden','Augsburg Settlement','cuius regio eius religio'],
'vienna':['kongres wiedeński','Vienna Congress','Wiener Kongress','ład wiedeński'],
'industrial':['rewolucja przemysłowa w Wielkiej Brytanii','British Industrial Revolution','industrializacja brytyjska'],
'meiji':['restauracja Meiji','reformy Meiji','Meiji Ishin','Meiji Restoration'],
'league':['Liga Narodów','League of Nations','Société des Nations','bezpieczeństwo zbiorowe Ligi Narodów'],
'marshall':['plan Marshalla','European Recovery Program','ERP','Marshall Plan'],
}

def digest(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()
def normalize(value): return ' '.join(unicodedata.normalize('NFKC',value).lower().split())
def dump(name, rows): (ROOT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

def main():
    sources={r['source_id']:r for r in map(json.loads,(ROOT/'sources.jsonl').read_text(encoding='utf-8').splitlines())}
    essays=[]; cards=[]; groups=[]
    for key,era,topic in TOPICS:
        path=ROOT/f'essay-{key}.txt'
        if not path.exists(): continue
        body=path.read_text(encoding='utf-8').strip(); source=sources['wiki-'+key]; group=source['source_group_id']
        claims=[]
        for i,(actor,event,date,consequence,locator,paragraphs) in enumerate(FACTS[key],1):
            claim=dict(claim_id=f'{key}-claim-{i:02}',actor=actor,event=event,date=date,consequence=consequence,evidence_locator=f'wiki-{key}#{locator}',support_type='fact_and_inference',essay_paragraphs=paragraphs,source_ids=['wiki-'+key],source_group_id=group,review_status='generator_checked_pending_independent_review',source_revision=source['revision_id'],source_content_sha256=source['revision_or_sha256'],evidence_note='Event and date are reference facts; causal and evaluative consequence is original synthesis to be independently checked. Source is a licensed secondary reference, not primary proof.')
            claims.append(claim); cards.append(claim)
        prompt=topic+' Napisz jedno spójne wypracowanie liczące 400–500 słów, z tezą, trzema rozwiniętymi argumentami i wnioskiem. Zwróć wyłącznie tekst wypracowania.'
        essays.append(dict(id='sol-corpus-essay-'+key,source_group_id=group,prompt=prompt,response=body,body_word_count=len(body.split()),fact_claims=claims,source_ids=['wiki-'+key],synthetic_model='OpenAI Codex delegated session; parent requested Sol; exact serving model snapshot not independently verified',generation_date='2026-09-26',status=STATUS,era=era,task_type='essay',split=None,normalized_prompt_sha256=digest(normalize(prompt)),response_sha256=digest(body),topic=topic))
        groups.append(dict(source_group_id=group,canonical_source_url=source['url'],canonical_revision_url=source['permalink'],source_ids=['wiki-'+key],aliases=[source['title'],source['url'],source['permalink'],source['history_url']]+ALIASES[key],alias_note='Text aliases are declared semantic grouping labels, not claims of separately acquired translation pages.',split=None,status='draft_pending_cross_corpus_alias_dedup',policy='All essay and repair variants must stay together. Cross-corpus connected-component grouping and held-out evaluation assignment remain pending.'))
    repairs=[]
    for i,e in enumerate(essays):
        paras=e['response'].split('\n\n'); mode=i%4
        if mode==0: negative='Oczywiście, oto wypracowanie:\n\n'+e['response']+'\n\nMam nadzieję, że ta odpowiedź pomoże.'; defects=['preamble','closing_meta_comment']
        elif mode==1: negative='\n\n'.join(paras[:2]); defects=['underlength','missing_arguments_and_conclusion']
        elif mode==2: negative='Temat wybrany: '+e['topic']+'\n\n'+e['response']+'\n\nDrugi temat, którego nie wybrano:\n'+essays[(i+1)%len(essays)]['response'].split('\n\n')[0]; defects=['multiple_topics','topic_label_wrapper']
        else: negative='Plan odpowiedzi:\n1. Wstęp\n2. Argumenty\n3. Wniosek\n\n'+'\n\n'.join(paras[1:3])+'\n\nDalszą część dopiszę później.'; defects=['planning_wrapper','underlength','closing_meta_comment']
        prompt='Popraw szkic tak, aby odpowiadał wyłącznie wskazanemu tematowi. Usuń obce tematy, plan i komentarze; uzupełnij argumentację do 400–500 słów. Zwróć wyłącznie gotowe wypracowanie.\n\nWskazany temat: '+e['topic']+'\n\nSzkic do poprawy:\n'+negative
        repair={**e,'id':e['id'].replace('-essay-','-repair-'),'prompt':prompt,'task_type':'essay_repair','normalized_prompt_sha256':digest(normalize(prompt)),'parent_essay_id':e['id'],'defects':defects,'corrupted_response':negative,'corrupted_response_word_count_including_wrappers':len(negative.split()),'construction':'Deterministic corruption of this original target; any off-topic passage is another original target in this owned batch. No external or benchmark model output.'}
        if mode==2: repair['off_topic_parent_essay_id']=essays[(i+1)%len(essays)]['id']; repair['additional_source_group_dependencies']=[essays[(i+1)%len(essays)]['source_group_id']]
        repairs.append(repair)
    dump('essays.jsonl',essays); dump('repairs.jsonl',repairs); dump('evidence-cards.jsonl',cards); dump('source-groups.jsonl',groups)
    print(json.dumps({'essays':len(essays),'repairs':len(repairs),'word_counts':{e['id']:e['body_word_count'] for e in essays}},ensure_ascii=False))

if __name__=='__main__': main()

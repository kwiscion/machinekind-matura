"""One-runtime RAG extension; original direct payloads remain unchanged."""
import copy
import hashlib
import json
from pathlib import Path
import time

import deadline_runtime as schedule
import study_hook as base
import study_hook_v2 as v2
import essay_support


class Hook(v2.Hook):
    def __init__(self, root, engine, runtime=None):
        # Deliberately defer optional index verification until all direct work ends.
        self.root = Path(root)
        self.engine = engine
        self.runtime = runtime
        self.plan = schedule.read(self.root / 'study.json')
        self.base_out = self.root / 'results/study'
        self.out = self.base_out / 'main'
        self.scope = 'main'
        self.current = None
        self.original = engine.step
        self.original_accepted = engine.accepted
        self.original_partial = engine.usable_partial
        self.original_export = engine.export
        source_rows = {row['id']: row for row in map(json.loads,
            (self.root / 'input.jsonl').read_text(encoding='utf8').splitlines())}
        source_items = {item['id']: item for item in schedule.read(self.root / 'source-exam-original.json')['items']}
        self.rows = {key: source_rows[item] for key, item in self.plan['sources'].items()}
        self.items = {key: source_items[item] for key, item in self.plan['sources'].items()}
        self.optional_deadline = None
        self.index_ready = False
        self.skipped = set()
        self.essay = essay_support.EssaySupport(self)
        self.current_clock = time.time
        self.active_deadline = None
        self.essay_deadline = None

    def check_optional_clock(self):
        if self.active_deadline is not None and self.current_clock()>=self.active_deadline-15:
            raise self.engine.Fatal('Optional evidence preparation deadline')

    def suffix(self,stage):
        return self.essay.suffix(stage) if stage['kind'].startswith('essay_') else base.Hook.suffix(self,stage)

    def accepted(self,raw,cap,context):
        if self.current['kind'].startswith('essay_'):
            return self.essay.accepted(self.original_accepted(raw,cap,context))
        return super().accepted(raw,cap,context)

    def partial(self,raw,cap,context):
        return None if self.current['kind'] in ('query','judge','essay_query','essay_judge','essay_final') else self.original_partial(raw,cap,context)

    def answer(self, slot):
        return base.Hook.answer(self, self.plan['slot_prefix'] + slot)

    def ensure_index(self):
        if self.index_ready:
            return
        import search_query
        self.search = search_query
        self.index = Path(self.plan['index_path'])
        self.index_stat = self.index.stat()
        proof = schedule.read(self.root / 'index-proof.json')
        actual = {name: getattr(self.index_stat, name) for name in proof['stat']}
        import socket
        if (proof['hostname'] != socket.gethostname()
                or proof['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
                or any(Path(str(self.index)+suffix).exists() for suffix in ('-wal','-shm','-journal'))):
            raise self.engine.Fatal('Index host/boot or immutable SQLite assumption changed')
        if (proof['index_path'] != str(self.index) or proof['sha256'] != self.plan['index_sha256']
                or proof['bytes'] != self.plan['index_bytes'] or proof['stat'] != actual):
            raise self.engine.Fatal('Pre-acquisition full index proof changed; optional RAG stopped')
        self.index_ready = True

    def retrieval(self, source):
        self.ensure_index()
        return base.Hook.retrieval(self, source)

    def step(self, case, attempt, history, config, route=None):
        stage = self.plan['stages'][case['id']]
        self.current = stage
        if stage['kind'] == 'direct':
            # Keep exact baseline prompt, complete images, recovery and settings.
            return self.original(case, attempt, history, config, route)
        if stage['kind'].startswith('essay_'):
            return self.essay.step(case,attempt,history,config,route)
        body, settings = super().step(case, attempt, history, config, route)
        if stage['kind'] in ('query', 'judge'):
            cap = (512 if stage['kind'] == 'query' else 384) if attempt == 0 else 1024
            body['think'] = False
            body['options']['num_predict'] = cap
            settings.update(think=False, cap=cap, auxiliary_profile='fast_thinking_off_v1',
                            name='auxiliary_fast' if attempt==0 else 'auxiliary_fast_retry', escalation_note=None)
        return body, settings

    def barrier(self, unresolved, states, deadline, clock):
        self.current_clock=clock
        self.model_deadline=deadline
        direct = [case for case in unresolved if self.plan['stages'][case['id']]['kind'] == 'direct']
        if direct:
            return direct
        if not unresolved:
            return []
        now = clock()
        if self.optional_deadline is None:
            self.optional_deadline = min(now + schedule.OPTIONAL_SECONDS, deadline - schedule.RESERVE_SECONDS)
            available=max(0,self.optional_deadline-now)
            ordinary_reserve=min(300,available*.25) if self.plan['eligible_count'] else 0
            self.essay_deadline=min(now+900,self.optional_deadline-ordinary_reserve)
            if self.runtime is not None:
                self.runtime.optional_deadline = self.optional_deadline
            schedule.atomic(self.base_out / 'optional-window.json', dict(start=now,
                deadline=self.optional_deadline, model_deadline=deadline,
                maximum_seconds=schedule.OPTIONAL_SECONDS, reserve_seconds=schedule.RESERVE_SECONDS,
                essay_deadline=self.essay_deadline,ordinary_reserved_seconds=ordinary_reserve,
                direct_attempts={item: states[item]['attempts'] for item in self.plan['original_ids']}))
        if now >= self.optional_deadline - 15:
            schedule.atomic(self.base_out / 'optional-stop.json', dict(reason='optional wall budget exhausted', time=now))
            return []
        while True:
            eligible = [case for case in unresolved if case['id'] not in self.skipped]
            if not eligible:
                return []
            phase = min(self.plan['stages'][case['id']]['phase'] for case in eligible)
            selected = [case for case in eligible if self.plan['stages'][case['id']]['phase'] == phase]
            first = self.plan['stages'][selected[0]['id']]
            self.active_deadline=self.essay_deadline if first['kind'].startswith('essay_') else self.optional_deadline
            if self.runtime is not None:self.runtime.optional_deadline=self.active_deadline
            if first['kind'].startswith('essay_') and clock()>=self.essay_deadline-15:
                self.skipped.update(slot for slot,stage in self.plan['stages'].items() if stage['kind'].startswith('essay_'))
                schedule.atomic(self.base_out/'essay-time-stop.json',dict(reason='Essay reserved phase ended; retain direct and proceed to ordinary RAG',time=clock()))
                continue
            if first['kind'].startswith('essay_'):
                try:
                    essay_support.offered_topics(self.items[first['source_id']])
                    if first['kind']!='essay_query':self.essay.plan(first['source_id'])
                except (ValueError,TypeError,AttributeError):
                    self.skipped.update(slot for slot,stage in self.plan['stages'].items() if stage['source_id']==first['source_id'] and stage['kind'].startswith('essay_'))
                    schedule.atomic(self.base_out/'skipped-essay.json',dict(slots=sorted(self.skipped),reason='Invalid or absent research plan; preserve direct'))
                    continue
                if first['kind']=='essay_judge':
                    count=len(self.essay.retrieval(first['source_id'])['passages'])
                    self.skipped.update(case['id'] for case in selected if self.plan['stages'][case['id']]['rank']>=count)
                    selected=[case for case in selected if case['id'] not in self.skipped]
                    if not selected:continue
            if first['kind'] in ('final','essay_final') and not self.suffix(first):
                self.skipped.add(selected[0]['id'])
                schedule.atomic(self.base_out / 'skipped-finals.json', dict(
                    slots=sorted(self.skipped), reason='No admitted evidence; retain saved direct without rerun'))
                continue
            return selected

    def timeout(self, case, proposed, deadline, clock):
        if self.plan['stages'][case['id']]['kind'] == 'direct':
            return proposed
        # Applied after runtime warm-load timeout adjustment; it cannot extend RAG.
        cutoff=self.essay_deadline if self.plan['stages'][case['id']]['kind'].startswith('essay_') else self.optional_deadline
        return min(proposed, max(0, cutoff - clock() - 15))

    def response_deadline(self, case, clock):
        cutoff=self.essay_deadline if self.plan['stages'][case['id']]['kind'].startswith('essay_') else self.optional_deadline
        if self.plan['stages'][case['id']]['kind'] != 'direct' and clock() >= cutoff:
            if clock()>=self.model_deadline:raise self.engine.Fatal('Response after model deadline')
            raise self.engine.Failed('Optional response arrived after route cutoff; saved direct retained')

    def expired(self,case,clock):
        stage=self.plan['stages'][case['id']]
        if stage['kind']=='direct':return False
        cutoff=self.essay_deadline if stage['kind'].startswith('essay_') else self.optional_deadline
        return clock()>=cutoff-15

    def export(self, out, template, states, stop=None):
        result = self.original_export(out, template, states, stop)
        schedule.export_original(self.root, states, stop)
        return result


def install(root, engine, runtime=None):
    hook = Hook(root, engine, runtime)
    engine.step = hook.step
    engine.accepted = hook.accepted
    engine.usable_partial = hook.partial
    engine.stage_barrier = hook.barrier
    engine.stage_timeout = hook.timeout
    engine.stage_response_deadline = hook.response_deadline
    engine.stage_expired=hook.expired
    engine.export = hook.export
    return hook

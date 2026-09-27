"""Typed semantic stages using the injected, already reviewed owned runtime.

No transport, service, guardian, package exporter or execution authorization lives
here. All native calls share engine/events.jsonl and the absolute operation clock.
"""
from __future__ import annotations

import copy
import time
from pathlib import Path

ARMS = ('strong_single', 'structured_routes')
SLOTS = {'control': 1, 'closed': 4, 'open': 3, 'image': 3, 'essay': 2}
# name, output kind, profile, semantic validator; suffix composition stays frozen
# in structured_routes.py and is bound by the caller's import-closure manifest.
STAGES = {
    'closed': [('candidate_1', 'final_answer', 'thinking', 'text'),
               ('candidate_2', 'final_answer', 'thinking', 'text'),
               ('candidate_3', 'final_answer', 'thinking', 'text'),
               ('selector', 'selection', 'thinking', 'selection')],
    'open': [('claims_evidence', 'intermediate', 'thinking', 'text'),
             ('draft', 'final_answer', 'direct', 'text'),
             ('coverage', 'final_answer', 'thinking', 'text')],
    'image': [('observations', 'intermediate', 'thinking', 'text'),
              ('interpretation', 'image_interpretation', 'thinking', 'image_interpretation'),
              ('targeted_revisit', 'final_answer', 'thinking', 'text')],
    'essay': [('essay_plan', 'intermediate', 'thinking', 'essay_plan'),
              ('essay_write', 'final_answer', 'direct', 'essay_final')],
}
EXPECTED = {'context_target': 65536, 'thinking_initial_cap': 32768,
            'thinking_escalated_cap': 49152,
            'thinking_recovery_caps': [32768, 49152, 8192, 8192],
            'direct_writer_cap': 4096,
            'direct_writer_recovery_caps': [4096, 4096, 4096, 4096],
            'max_retries_per_failed_stage': 3, 'primary_thinking_stages': 14,
            'primary_direct_writer_stages': 2, 'primary_max_calls': 16,
            'max_calls': 64, 'max_requested_tokens': 1409024,
            'nonessay_item_arm_seconds': 240, 'essay_item_arm_seconds': 600,
            'max_seconds': 3600, 'global_recovery_quiescence_reserve_seconds': 600}


class StageSession:
    def __init__(self, runtime, engine_dir, budget, deadline, cases, validator,
                 binding, recovery, clock=time.time):
        self.r, self.runtime, self.validator, self.clock = recovery, runtime, validator, clock
        self.out = Path(engine_dir)
        self.budget, self.deadline = copy.deepcopy(budget), deadline
        self.active = False
        self.stopped = None
        self.calls = self.tokens = self.logical_stages = 0
        self.profile_counts = {'thinking': 0, 'direct': 0}
        self.started = set()
        self.arm_deadlines, self.arm_stages = {}, {}
        if any(budget.get(k) != v for k, v in EXPECTED.items()):
            raise self.r.Fatal('Frozen typed-stage budget differs')
        if not isinstance(binding, dict) or not binding:
            raise self.r.Fatal('Frozen caller/import/source binding required')
        if not isinstance(deadline, (int, float)) or not 600 < deadline - clock() <= 3600:
            raise self.r.Fatal('Operation deadline outside declared study window')
        if [c['id'] for c in cases] != budget.get('items') or len(cases) != 4:
            raise self.r.Fatal('Exactly four frozen ordered source cases required')
        if len({c['id'] for c in cases}) != 4 or sorted(c['structured_route'] for c in cases) != ['closed', 'essay', 'image', 'open']:
            raise self.r.Fatal('One frozen case per route required')
        self.cases = {}
        for original in cases:
            for arm in ARMS:
                case = copy.deepcopy(original)
                case.update(id=original['id'] + '__' + arm,
                            source_case_id=original['id'], study_arm=arm)
                self.cases[case['id']] = case
        if self.out.exists() and any(self.out.iterdir()):
            raise self.r.Fatal('Existing or interrupted session cannot replay reservations')
        self.out.mkdir(parents=True, exist_ok=True)
        self.r.atomic(self.out / 'binding.json', {
            'schema': 'typed_stage_session_v1', 'caller': binding,
            'cases_sha256': self.r.digest(self.cases), 'budget_sha256': self.r.digest(budget),
            'deadline': deadline, 'model': self.r.MODEL,
        })

    def emit_semantic(self, event):
        self.r.append(self.out / 'semantic.jsonl', copy.deepcopy(event))

    def item_deadline(self, case_id):
        if case_id not in self.cases:
            raise self.r.Fatal('Unknown arm ID')
        if case_id not in self.arm_deadlines:
            case = self.cases[case_id]
            allowance = 600 if case.get('kind') == 'essay' else 240
            self.arm_deadlines[case_id] = min(self.clock() + allowance, self.deadline - 600)
            self.r.append(self.out / 'events.jsonl', {
                'event': 'item_window', 'id': case_id, 'deadline': self.arm_deadlines[case_id],
                'allowance_seconds': allowance, 'time': self.clock(),
            })
        return self.arm_deadlines[case_id]

    def _stage(self, case, stage):
        if case['id'] not in self.cases or case != self.cases[case['id']]:
            raise self.r.Fatal('Frozen arm/source case changed')
        required = {'name', 'output_kind', 'suffix', 'profile', 'validation'}
        if not required <= set(stage) or set(stage) - required - {'validation_context'}:
            raise self.r.Fatal('Unknown stage fields')
        if not isinstance(stage['suffix'], str):
            raise self.r.Fatal('Stage suffix must be text')
        route = 'control' if case['study_arm'] == 'strong_single' else case['structured_route']
        sequence = [('control', 'final_answer', 'thinking',
                     'essay_final' if case.get('kind') == 'essay' else 'text')] if route == 'control' else STAGES[route]
        index = self.arm_stages.get(case['id'], 0)
        if index >= len(sequence):
            raise self.r.Fatal('Too many semantic slots for arm')
        expected = sequence[index]
        if route == 'closed' and index == 3 and stage['name'] == 'selector_direct_fallback':
            expected = ('selector_direct_fallback', 'final_answer', 'thinking', 'text')
        if tuple(stage[k] for k in ('name', 'output_kind', 'profile', 'validation')) != expected:
            raise self.r.Fatal('Stage identity/profile/order differs from frozen routes')
        key = (case['id'], stage['name'])
        if key in self.started or self.logical_stages >= 16:
            raise self.r.Fatal('Logical-stage replay or cap')
        limit = 14 if stage['profile'] == 'thinking' else 2
        if self.profile_counts[stage['profile']] >= limit:
            raise self.r.Fatal('Typed profile slot cap')
        self.started.add(key)
        self.logical_stages += 1
        self.profile_counts[stage['profile']] += 1
        self.arm_stages[case['id']] = index + 1
        self.r.append(self.out / 'events.jsonl', {
            'event': 'stage_started', 'id': case['id'], 'source_case_id': case['source_case_id'],
            'study_arm': case['study_arm'], 'stage': copy.deepcopy(stage), 'time': self.clock(),
        })
        return route, index

    def _settings(self, stage, attempt, records):
        if stage['profile'] == 'direct':
            return {'cap': 4096, 'think': False, 'escalation_note': None}
        cap = (32768, 32768, 8192, 8192)[attempt]
        reason = None
        if attempt == 1:
            counts = [x['raw']['prompt_eval_count'] for x in records
                      if isinstance(x.get('raw'), dict) and type(x['raw'].get('prompt_eval_count')) is int]
            if counts and max(counts) + 49152 <= 65536:
                cap = 49152
            else:
                reason = 'Higher cap lacks observed context-fit evidence; retain32768'
        return {'cap': cap, 'think': attempt < 2, 'escalation_note': reason}

    def invoke(self, case, stage):
        records, partials = [], []
        result = {'ok': False, 'final': None, 'error': None, 'attempt_records': records}
        if self.stopped:
            return dict(result, fatal=True, error=self.stopped)
        if self.active:
            raise self.r.Fatal('Concurrent stage invocation forbidden')
        self.active = True
        try:
            route, index = self._stage(case, stage)
            item_end = self.item_deadline(case['id'])
            for attempt in range(4):
                now = self.clock()
                if now >= self.deadline - 600:
                    raise self.r.Fatal('Operation generation cutoff; global reserve preserved')
                left = item_end - now - 20
                if left <= 0:
                    result['error'] = 'item_deadline_exhausted_before_dispatch'
                    break
                obligations = (SLOTS[route] - index - 1) * 4 + 4 - attempt
                timeout = min(420, left / max(1, obligations))
                if hasattr(self.runtime, 'timeout_for'):
                    timeout = min(420, left, self.runtime.timeout_for(timeout, attempt))
                if timeout < 1:
                    result['error'] = 'item_window_cannot_fit_remaining_attempts'
                    break
                settings = self._settings(stage, attempt, records)
                cap = settings['cap']
                if self.calls >= 64 or self.tokens + cap > 1409024:
                    raise self.r.Fatal('Global call/token admission cap')
                self.runtime.verify(65536)
                text, images = self.r.source(case)
                msg = {'role': 'user', 'content': text + stage['suffix']}
                if images:
                    msg['images'] = images
                body = {'model': self.r.MODEL, 'stream': False, 'think': settings['think'],
                        'truncate': False, 'shift': False, 'messages': [msg],
                        'options': {'num_ctx': 65536, 'num_predict': cap}}
                identity = {'id': case['id'], 'source_case_id': case['source_case_id'],
                            'study_arm': case['study_arm'], 'stage_name': stage['name'], 'attempt': attempt}
                self.r.append(self.out / 'requests.jsonl', {**identity, 'payload': body,
                              'validation_context': copy.deepcopy(stage.get('validation_context'))})
                self.r.append(self.out / 'events.jsonl', {**identity, 'event': 'reserved',
                              'cap': cap, 'settings': settings, 'timeout': timeout,
                              'item_deadline': item_end, 'operation_deadline': self.deadline,
                              'request_sha256': self.r.digest(body), 'time': self.clock(),
                              'total_calls': self.calls + 1, 'total_requested_tokens': self.tokens + cap})
                self.calls += 1
                self.tokens += cap
                raw, final, error, fatal, semantic = None, None, None, None, None
                try:
                    raw = self.runtime.send(body, timeout)
                    self.runtime.verify(65536)
                    if self.clock() >= item_end or self.clock() >= self.deadline - 600:
                        raise self.r.Fatal('Response exceeded fixed item/operation deadline')
                    if isinstance(raw, dict) and raw.get('error') is not None:
                        raise self.r.Failed('Provider error: ' + str(raw['error']))
                    try:
                        final = self.r.accepted(raw, cap, 65536)
                    except self.r.Failed as exc:
                        if str(exc) == 'malformed usage':
                            raise self.r.Fatal('Untrusted native usage') from exc
                        raise
                    semantic = self.validator(case, stage, final)
                    if not isinstance(semantic, dict) or type(semantic.get('ok')) is not bool:
                        raise self.r.Fatal('Invalid semantic validation protocol')
                    if not semantic['ok']:
                        if stage['output_kind'] == 'final_answer' and semantic.get('partial_eligible'):
                            partials.append(final)
                        raise self.r.Failed(semantic.get('error') or 'Semantic output invalid')
                except self.r.Fatal as exc:
                    fatal = str(exc)
                    error = 'Fatal: ' + fatal
                    final = None
                except Exception as exc:
                    error = type(exc).__name__ + ': ' + str(exc)
                    final = None
                finally:
                    try:
                        if self.runtime.quiesce(self.deadline) is not True:
                            raise self.r.Fatal('Owned compute stop not proven')
                    except Exception as exc:
                        fatal = 'Cannot safely continue: ' + str(exc)
                        error, final = fatal, None
                if final is None and not fatal and stage['output_kind'] == 'final_answer':
                    partial = self.r.usable_partial(raw, cap, 65536)
                    if partial:
                        check = self.validator(case, stage, partial)
                        if check.get('ok') or check.get('partial_eligible'):
                            partials.append(partial)
                event = {**identity, 'event': 'completed', 'raw': raw, 'answer': final,
                         'error': error, 'semantic_validation': semantic, 'time': self.clock()}
                self.r.append(self.out / 'events.jsonl', event)
                records.append(event)
                result['error'] = error
                if fatal:
                    raise self.r.Fatal(fatal)
                if final is not None:
                    result.update(ok=True, final=final, error=None)
                    break
            if partials and not result['ok']:
                result['partial_final'] = max(partials, key=len)
        except Exception as exc:
            self.stopped = type(exc).__name__ + ': ' + str(exc)
            result.update(fatal=True, error=self.stopped, final=None, ok=False)
        finally:
            self.active = False
        return result

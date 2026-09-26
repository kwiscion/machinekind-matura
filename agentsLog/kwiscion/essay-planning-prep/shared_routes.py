"""Thin suffix-only hooks for the shared recovery harness; never performs I/O."""
import json
import planning_wave as w


def route_stage(item, stage, plan=None):
    think, cap = w.STAGES[stage]
    if stage == 'plan':
        suffix = w.PLAN_RULES + '\nWymagane nazwy aspektów: ' + json.dumps(item['aspects'], ensure_ascii=False)
    else:
        suffix = w.ESSAY_RULES
        if stage == 'write':
            w.need(plan is not None and w.parse_plan(plan, item), 'writer_without_valid_plan')
            suffix += '\n' + w.FALLIBLE_NOTES + '\nMAPA:\n' + plan
    return {'name': 'essay_' + stage, 'suffix': suffix, 'think': think, 'cap': cap}


def stage_result(item, stage, native_final, local_error=None):
    """The runtime has already checked native identity/usage/context/finish flags."""
    if local_error:
        return {'ok': False, 'error': local_error, 'final': '', 'next_stage': None}
    okay = w.parse_plan(native_final, item) if stage == 'plan' else w.essay_check(native_final, item)['ok']
    return {'ok': okay, 'error': None if okay else 'invalid_' + stage,
            'final': native_final if okay and stage != 'plan' else '',
            'plan': native_final if okay and stage == 'plan' else None,
            'next_stage': 'write' if okay and stage == 'plan' else None}

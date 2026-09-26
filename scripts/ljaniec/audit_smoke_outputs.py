#!/usr/bin/env python3
"""Audit private smoke JSONL without publishing prompts or responses.

Token-budget hits indicate possible truncation, not a proven finish reason.
Input labels are supplied explicitly; no exam split is inferred from IDs.
"""
import argparse
import hashlib
import json
import math
import pathlib
import statistics


def records(path, inputs=False):
    raw = pathlib.Path(path).read_bytes()
    rows = []
    for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            raise ValueError(f'Invalid JSON at line {number}') from None
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
            raise ValueError(f'Invalid record/id at line {number}')
        if inputs and not isinstance(row.get('prompt'), str):
            raise ValueError(f'Invalid input prompt at line {number}')
        if not inputs:
            if row.get('error') is not None and not isinstance(row['error'], str):
                raise ValueError(f'Invalid reported error at line {number}')
            if 'raw_response' not in row and not row.get('error'):
                raise ValueError(f'Record lacks response or reported error at line {number}')
            if row.get('raw_response') is not None and not isinstance(row['raw_response'], str):
                raise ValueError(f'Invalid response type at line {number}')
            if row.get('usage') is not None and not isinstance(row['usage'], dict):
                raise ValueError(f'Invalid usage at line {number}')
            for key in ('latency_s', 'wall_s', 'completion_tokens'):
                numeric(row.get(key), number, key, integer=key == 'completion_tokens')
            numeric((row.get('usage') or {}).get('completion_tokens'), number, 'usage.completion_tokens', integer=True)
        rows.append(row)
    if not rows:
        raise ValueError('Artifact has no records')
    return rows, hashlib.sha256(raw).hexdigest()


def numeric(value, number, key, integer=False):
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not math.isfinite(value) or value < 0
                              or (integer and not isinstance(value, int))):
        raise ValueError(f'Invalid {key} at line {number}')


def audit(path, token_budget, input_path=None, input_kind='unspecified'):
    if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget <= 0:
        raise ValueError('Token budget must be positive')
    rows, digest = records(path)
    ids = [r['id'] for r in rows]
    empty = [not isinstance(r.get('raw_response'), str) or not r['raw_response'].strip() for r in rows]
    errors = [r.get('error') is not None for r in rows]
    latencies = [r.get('latency_s') if r.get('latency_s') is not None else r.get('wall_s') for r in rows]
    measured = [v for v in latencies if v is not None]
    tokens = [r.get('completion_tokens') if r.get('completion_tokens') is not None
              else (r.get('usage') or {}).get('completion_tokens') for r in rows]
    measured_tokens = [v for v in tokens if v is not None]
    result = {
        'artifact_sha256': digest, 'record_count': len(rows), 'unique_id_count': len(set(ids)),
        'duplicate_id_record_count': len(ids) - len(set(ids)),
        'response_empty_count': sum(empty), 'response_nonempty_count': len(rows) - sum(empty),
        'reported_error_count': sum(errors),
        'empty_response_without_reported_error_count': sum(e and not err for e, err in zip(empty, errors)),
        'reported_error_or_empty_response_count': sum(e or err for e, err in zip(empty, errors)),
        'latency': {'denominator_records_with_latency': len(measured),
                    'sum_seconds': sum(measured) if measured else None,
                    'mean_seconds': statistics.mean(measured) if measured else None,
                    'median_seconds': statistics.median(measured) if measured else None},
        'completion_tokens': {'denominator_records_with_token_count': len(measured_tokens),
                              'sum': sum(measured_tokens) if measured_tokens else None,
                              'configured_budget': token_budget,
                              'records_at_or_above_budget': sum(v >= token_budget for v in measured_tokens),
                              'interpretation': 'Possible truncation only; token counts do not prove finish reason.'},
        'model_revision_present_count': sum(isinstance(r.get('model_revision'), str) and bool(r['model_revision'].strip()) for r in rows),
        'finish_reason_present_count': sum(isinstance(r.get('finish_reason'), str) and bool(r['finish_reason'].strip()) for r in rows),
        'input_kind': input_kind,
    }
    if input_path:
        inputs, input_digest = records(input_path, inputs=True)
        expected = {r['id']: r['prompt'] for r in inputs}
        if len(expected) != len(inputs):
            raise ValueError('Input catalog has duplicate IDs')
        result['input_comparison'] = {
            'input_sha256': input_digest, 'input_record_count': len(inputs),
            'exact_id_set_match': set(ids) == set(expected),
            'all_record_prompts_match_by_id': all(r['id'] in expected and r.get('prompt') == expected[r['id']] for r in rows),
            'exact_id_sequence_match': ids == [r['id'] for r in inputs],
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', required=True)
    parser.add_argument('--output', required=True, help='New aggregate JSON file; existing files are rejected')
    parser.add_argument('--token-budget', type=int, required=True)
    parser.add_argument('--input-catalog')
    parser.add_argument('--input-kind', choices=['synthetic-smoke', 'official-DEV', 'official-VALIDATION', 'unspecified'], default='unspecified')
    args = parser.parse_args()
    try:
        result = audit(args.raw, args.token_budget, args.input_catalog, args.input_kind)
        with open(args.output, 'x', encoding='utf-8') as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f'Audit failed: {exc}\n')


if __name__ == '__main__':
    main()

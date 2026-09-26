"""Prepare one private May 2024 review pass, reusing only byte-identical grades."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWN = ROOT / 'agentsLog/kwiscion'
PRIVATE = OWN / 'private'
PINS = {
    'answers': (OWN / 'model-answers/full-thinking-answers.json', '11057839c6cb04a9b83d8149750202b6b975390fff9433bc8c4425c66219ae49'),
    'grades': (OWN / '2026-09-26-full-thinking-score.json', '21de78a8a73666307eca867232707a308144aa3fe40085bfb2f9e159c231e781'),
    'keys': (ROOT / 'agentsLog/Pewciu6/private/validation_2024/eval_keys.jsonl', '279abe703dc1af4119a35624d6db893e310fc7afaffbef2a00e678f423706486'),
    'exam': (PRIVATE / 'full-thinking-20260926/recovered/full-thinking-20260926/exam/exam.json', '907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471'),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_pin(name):
    path, expected = PINS[name]
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError('Reference changed: ' + name)
    return [json.loads(line) for line in data.decode('utf-8').splitlines()] if path.suffix == '.jsonl' else json.loads(data)

def indexed(rows):
    result = {}
    for row in rows:
        if row['id'] in result:
            raise ValueError('Duplicate ID: ' + row['id'])
        result[row['id']] = row
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--answers', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(PRIVATE.resolve()) or output.exists():
        raise ValueError('Use a fresh directory within agentsLog/kwiscion/private')
    prior, grades, keys, exam = (read_pin(k) for k in ('answers', 'grades', 'keys', 'exam'))
    raw = args.answers.read_bytes()
    current = json.loads(raw)
    if set(current) != {'exam_id', 'answers'} or current['exam_id'] != prior['exam_id']:
        raise ValueError('Expected the exact May 2024 answer schema/exam ID')
    answers = indexed(current['answers'])
    old = indexed(prior['answers'])
    questions = indexed(exam['items'])
    marked = indexed(grades['items'])
    reference = indexed(keys)
    if set(answers) != set(old) or set(questions) != set(old):
        raise ValueError('Missing or unexpected answer/question IDs')
    review, reused = [], []
    for printed_id, answer in answers.items():
        if set(answer) != {'id', 'answer'} or not isinstance(answer['answer'], str):
            raise ValueError('Invalid answer entry: ' + printed_id)
        answer_hash = sha(answer['answer'].encode('utf-8'))
        stable_id = 'val2024-hist-z' + printed_id
        key, grade = reference[stable_id], marked[stable_id]
        if grade['max_points'] != key['max_points'] or grade['answer_sha256'] != sha(old[printed_id]['answer'].encode('utf-8')):
            raise ValueError('Reference grade/answer mismatch: ' + printed_id)
        if answer['answer'] == old[printed_id]['answer']:
            reused.append({'printed_id': printed_id, **grade, 'reuse_reason': 'exact_same_answer_and_frozen_source'})
        else:
            review.append({'id': stable_id, 'printed_id': printed_id, 'answer': answer['answer'], 'answer_sha256': answer_hash,
                           'question': questions[printed_id], 'evaluation_key': key})
    summary = {'exam_id': current['exam_id'], 'answer_sha256': sha(raw), 'items': len(answers), 'max_points': sum(x['max_points'] for x in marked.values()),
               'reused_items': len(reused), 'reused_points': sum(x['central'] for x in reused), 'items_requiring_one_review': len(review),
               'complete_score': sum(x['central'] for x in reused) if not review else None,
               'source_package': str(PINS['exam'][0].parent), 'reference_pins': {k: v[1] for k, v in PINS.items()},
               'policy': 'One fresh pass for changed answers; do not infer improvement until all items are scored. Placeholder/recovery metrics come from the run report, not grades.'}
    output.mkdir(parents=True)
    for name, value in [('summary.json', summary), ('reused-grades.json', reused)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / 'changed-private.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in review), encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('items', 'reused_items', 'items_requiring_one_review', 'complete_score')}))

if __name__ == '__main__':
    main()

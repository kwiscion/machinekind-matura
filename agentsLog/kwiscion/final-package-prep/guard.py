"""CPU-only exact staged-weight inventory and one-Gemma native-cache verifier."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

LIMIT = 8_800_000_000
CANONICAL = {
    'schema': 'single_gemma_pins_v1', 'model': 'gemma4:12b-it-q4_K_M',
    'native_manifest_sha256': '4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c',
    'model_weight': {'bytes': 7_381_382_048, 'sha256': '1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606'},
    'projector': {'bytes': 175_115_584, 'sha256': '675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842'},
    'runtime_version': '0.34.4', 'context_length': 32768,
    'runtime_binary_sha256': 'ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4',
}
PURPOSES = {'model', 'projector', 'adapter', 'metadata'}
def require(ok, message):
    if not ok: raise ValueError(message)
def unique_object(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'Duplicate JSON key: ' + key); out[key] = value
    return out
def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf8'), object_pairs_hook=unique_object)
def relative(value):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value, 'Invalid relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and value == p.as_posix() and all(x not in ('', '.', '..') for x in value.split('/')), 'Noncanonical/outside path')
    return value
def no_link(path):
    st = path.lstat()
    require(not stat.S_ISLNK(st.st_mode) and not (getattr(st, 'st_file_attributes', 0) & 0x400), 'Symlink/reparse point: ' + str(path))
    return st
def root_path(value):
    path = Path(value).absolute()
    for p in [path, *path.parents]: no_link(p)
    require(path.is_dir(), 'Missing stage directory')
    return path.resolve()
def files_under(root):
    result = {}
    def walk_error(error): raise error
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in dirs: no_link(Path(parent)/name)
        for name in files:
            p = Path(parent)/name; st = no_link(p)
            require(stat.S_ISREG(st.st_mode), 'Nonregular staged file')
            key = p.relative_to(root).as_posix(); relative(key)
            require(key.casefold() not in {n.casefold() for n in result}, 'Case-colliding stage paths')
            result[key] = p
    return result
def fingerprint(p):
    before = no_link(p)
    require(stat.S_ISREG(before.st_mode), 'Hash target must be a regular file')
    fd = os.open(p, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as f:
        opened = os.fstat(f.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), 'File replaced while opening')
        h = hashlib.sha256(); size = 0
        for block in iter(lambda: f.read(8*1024*1024), b''):
            size += len(block); h.update(block)
        after = os.fstat(f.fileno())
    final = no_link(p)
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    # Windows lstat ctime is creation time, while fstat may expose change time.
    require(signature(before) == signature(final) and signature(opened) == signature(after)
            and signature(before)[:4] == signature(after)[:4] and size == after.st_size, 'File changed during hash')
    return {'bytes': size, 'sha256': h.hexdigest()}
def pin(value):
    require(isinstance(value, dict) and type(value.get('bytes')) is int and value['bytes'] >= 0, 'Invalid byte pin')
    require(isinstance(value.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'Invalid SHA256 pin')
def verify_inventory(root, inventory, limit=LIMIT):
    require(type(limit) is int and 0 < limit <= LIMIT, 'Cannot expand aggregate cap')
    root = root_path(root)
    require(inventory.get('schema') == 'final_weight_inventory_v1' and isinstance(inventory.get('files'), list), 'Inventory schema')
    expected = {}; folded = set()
    for row in inventory['files']:
        name = relative(row['path']); require(name.casefold() not in folded, 'Duplicate inventory path'); folded.add(name.casefold())
        require(row.get('purpose') in PURPOSES, 'Weight/metadata directory only; runtime binaries belong elsewhere')
        pin(row); expected[name] = row
    require(expected, 'Empty inventory')
    actual = files_under(root)
    require(set(actual) == set(expected), 'Missing/unlisted staged files: ' + str(sorted(set(actual) ^ set(expected))))
    total = 0; verified = []; states = {}
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    for name in sorted(actual):
        states[name] = signature(no_link(actual[name]))
        got = fingerprint(actual[name]); row = expected[name]
        with actual[name].open('rb') as f: magic = f.read(4)
        require(not (magic == b'\x7fELF' or magic[:2] == b'MZ'), 'Runtime executable belongs outside weight directory: ' + name)
        if row['purpose'] != 'metadata':
            require(got['bytes'] > 0, 'Empty weight file: ' + name)
        require(got == {k: row[k] for k in ('bytes', 'sha256')}, 'Changed staged file: ' + name)
        total += got['bytes'] # Every directory entry counts, even hardlinks to the same inode.
        verified.append(dict(path=name, purpose=row['purpose'], **got))
    require(total <= limit, 'Aggregate submitted bytes exceed cap')
    require(root_path(root) == root, 'Stage root changed during verification')
    final_files = files_under(root)
    require(set(final_files) == set(expected), 'Stage changed during verification')
    require(all(signature(no_link(final_files[name])) == states[name] for name in states), 'Staged file changed after hash')
    return {'status': 'PASS', 'files': verified, 'counted_bytes': total, 'limit_bytes': limit, 'remaining_bytes': limit-total}
def validate_pins(pins):
    require(pins.get('schema') == 'single_gemma_pins_v1', 'Explicit pin schema')
    require(re.fullmatch(r'gemma4:[A-Za-z0-9_.-]+', pins.get('model', '')), 'One explicit Gemma tag required')
    require(re.fullmatch('[0-9a-f]{64}', pins.get('native_manifest_sha256', '')), 'Native manifest pin')
    pin(pins['model_weight']); pin(pins['projector'])
    require(pins['model_weight']['bytes'] + pins['projector']['bytes'] <= LIMIT, 'Pinned pair exceeds cap')
def native_inventory(root, pins):
    """Only the one Gemma manifest and its exact referenced blobs are permitted."""
    root = root_path(root); validate_pins(pins)
    model, tag = pins['model'].split(':')
    name = 'manifests/registry.ollama.ai/library/' + model + '/' + tag
    files = files_under(root); require(name in files, 'Pinned Gemma manifest missing')
    manifest_pin = fingerprint(files[name]); require(manifest_pin['sha256'] == pins['native_manifest_sha256'], 'Native manifest changed')
    doc = read_json(files[name]); require(isinstance(doc.get('layers'), list) and isinstance(doc.get('config'), dict), 'Native structure')
    rows = [{'path': name, 'purpose': 'metadata', **manifest_pin}]; seen = set(); found = {}
    kinds = {'application/vnd.ollama.image.model': 'model', 'application/vnd.ollama.image.projector': 'projector'}
    metadata = {'application/vnd.docker.container.image.v1+json', 'application/vnd.ollama.image.template', 'application/vnd.ollama.image.system', 'application/vnd.ollama.image.params', 'application/vnd.ollama.image.license', 'application/vnd.ollama.image.messages'}
    for item in [doc['config'], *doc['layers']]:
        digest = item.get('digest', ''); require(re.fullmatch('sha256:[0-9a-f]{64}', digest), 'Native blob digest')
        kind = kinds.get(item.get('mediaType'))
        require(kind is not None or item.get('mediaType') in metadata, 'Unknown native layer purpose')
        name = 'blobs/' + digest.replace(':', '-'); row = dict(path=name, purpose=kind or 'metadata', bytes=item.get('size'), sha256=digest[7:]); pin(row)
        if kind:
            require(kind not in found, 'Multiple model/projector layers')
            expected = pins['model_weight' if kind == 'model' else 'projector']
            require({k: row[k] for k in ('bytes', 'sha256')} == expected, 'Explicit pair pin mismatch'); found[kind] = True
        if name not in seen: rows.append(row); seen.add(name)
    require(set(found) == {'model', 'projector'}, 'Model/projector pair incomplete')
    return {'schema': 'final_weight_inventory_v1', 'files': rows}
def verify_snapshot(snapshot, pins, require_loaded=False):
    validate_pins(pins)
    require(snapshot['version']['version'] == pins['runtime_version'], 'Runtime version changed')
    tags = snapshot['tags']['models']
    require(len(tags) == 1 and tags[0]['name'] == pins['model'] and tags[0]['digest'] == pins['native_manifest_sha256'], 'Isolated single-Gemma tags required')
    loaded = snapshot['ps']['models']; require(len(loaded) <= 1 and (bool(loaded) or not require_loaded), 'Unexpected/missing loaded model')
    for item in loaded:
        require(item['name'] == pins['model'] and item['digest'] == pins['native_manifest_sha256'] and item['context_length'] == pins['context_length'], 'Loaded identity/context changed')
def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    inv=sub.add_parser('inventory'); inv.add_argument('root',type=Path); inv.add_argument('inventory',type=Path)
    nat=sub.add_parser('native'); nat.add_argument('root',type=Path); nat.add_argument('--pins',type=Path); nat.add_argument('--write-inventory',type=Path)
    snap=sub.add_parser('snapshot');snap.add_argument('snapshot',type=Path);snap.add_argument('--pins',type=Path);snap.add_argument('--runtime-binary',type=Path,required=True);snap.add_argument('--require-loaded',action='store_true')
    a=ap.parse_args();pins=read_json(a.pins) if getattr(a,'pins',None) else CANONICAL
    if a.command=='inventory':
        require(not a.inventory.resolve().is_relative_to(a.root.resolve()),'Keep inventory outside weight directory')
        report=verify_inventory(a.root,read_json(a.inventory))
    elif a.command=='native':
        inventory=native_inventory(a.root,pins);report=verify_inventory(a.root,inventory)
        if a.write_inventory:
            require(not a.write_inventory.resolve().is_relative_to(a.root.resolve()),'Inventory output must be outside cache')
            with a.write_inventory.open('x',encoding='utf8') as f:json.dump(inventory,f,indent=2);f.write('\n')
    else:
        require(fingerprint(a.runtime_binary)['sha256']==pins['runtime_binary_sha256'],'Runtime binary pin')
        verify_snapshot(read_json(a.snapshot),pins,a.require_loaded);report={'status':'PASS','scope':'saved snapshot only; not live process ownership or offline proof'}
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

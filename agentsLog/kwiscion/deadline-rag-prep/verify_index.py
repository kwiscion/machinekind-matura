"""Run on the final host BEFORE final acquisition; CPU-only full index hash proof."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import socket
import time

INDEX_SHA = '5bf93ceca9715170f7a3b6497746cd00dac4dd80f7fe0b53fd0a3f981d88bb36'
INDEX_BYTES = 10464555008
FIELDS = ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')


def verify(path, output):
    started = time.monotonic()
    if path.is_symlink() or output.exists():
        raise ValueError('Regular full index and fresh receipt required')
    path = path.resolve()
    if any(Path(str(path)+suffix).exists() for suffix in ('-wal','-shm','-journal')):
        raise ValueError('Frozen SQLite DB must have no WAL, SHM or journal sidecar')
    before = path.stat()
    if before.st_size != INDEX_BYTES:
        raise ValueError('Full corpus index size differs')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
            digest.update(chunk)
    after = path.stat()
    if any(getattr(before,name)!=getattr(after,name) for name in FIELDS) or digest.hexdigest()!=INDEX_SHA:
        raise ValueError('Index changed or full hash differs')
    receipt=dict(schema='pre_acquisition_full_index_v1',index_path=str(path),sha256=digest.hexdigest(),
        bytes=before.st_size,stat={name:getattr(before,name) for name in FIELDS},
        hostname=socket.gethostname(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        immutable_assumption='No writers, replacements or SQLite sidecars until final run completes; retrieval uses mode=ro',
        verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        elapsed_seconds=time.monotonic()-started)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf8') as stream:
        json.dump(receipt,stream,indent=2)
        stream.write('\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.index,args.output)))

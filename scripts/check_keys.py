#!/usr/bin/env python3
"""Check that rebuilt answer keys are the ones the reference results were scored with (sha256 of canonical JSON)."""
import hashlib
import json
import pathlib
import sys

EXPECTED = json.loads((pathlib.Path(__file__).with_name("key_hashes.json")).read_text())
K = pathlib.Path(sys.argv[1]).expanduser()
bad = 0
for rel, h in EXPECTED.items():
    p = K / rel
    if not p.exists():
        print(f"MISSING  {rel}")
        bad += 1
        continue
    got = hashlib.sha256(json.dumps(json.loads(p.read_text()), sort_keys=True).encode()).hexdigest()
    ok = got == h
    bad += not ok
    print(f"{'ok      ' if ok else 'MISMATCH'} {rel}")
sys.exit(1 if bad else 0)

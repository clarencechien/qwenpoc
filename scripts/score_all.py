#!/usr/bin/env python3
"""Score runs and print the comparison with the reference results and the report's verdict.

    python3 scripts/score_all.py --runs runs/onprem --keys ~/qwenpoc-keys
        scores every runs/onprem/<stage>-r<k>/ that has been submitted, writes runs/onprem/summary.{json,md}

    python3 scripts/score_all.py --verify-reference --keys ~/qwenpoc-keys
        re-scores the reference runs (copies in a temp dir) and checks the totals match the recorded ones

Verdict (same as the report): a model passes only if every stage reaches 80 % of its maximum AND
the weighted total (correctness 70 by stage weight + efficiency 30) reaches 80. Efficiency per stage =
fastest time / own time, where "fastest" is taken over this run and the Opus reference.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stages import NATIVE_CTX, OPUS_SECONDS, PASS, REFERENCE, STAGES  # noqa: E402


def run_score(sid: str, run: pathlib.Path, keys: pathlib.Path) -> float | None:
    title, ph, w, mx, init, runner, cmd, out = STAGES[sid]
    c = cmd.format(RUN=str(run), KEY=str(keys))
    p = subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True)
    f = run / out
    if not f.exists():
        print(f"  [{sid}] scorer wrote nothing: {p.stderr.strip()[-400:]}", file=sys.stderr)
        return None
    d = json.loads(f.read_text())
    return d.get("total", d.get("auto_total_40"))


SUSPECT = ("reference", "qwenpoc-keys", "asbuilt.json", "target.json", "scene.json", "ref.json", "layout.json", "../", "/home", "/root", "/mnt", "/data")


def audit(run: pathlib.Path) -> list[str]:
    """Blender exec code is not sandboxed: list scripts that mention paths outside the run directory or key files."""
    hits = []
    log = run / "bench_log.jsonl"
    if not log.exists():
        return hits
    for i, l in enumerate(log.read_text().splitlines()):
        e = json.loads(l)
        code = (e.get("code") or "").replace(str(run.resolve()), "RUN").replace(str(run), "RUN")
        found = sorted({s for s in SUSPECT if s in code and not (s == "layout.json" and "inputs/layout.json" in code)})
        if found:
            hits.append(f"bench_log line {i + 1}: {', '.join(found)}")
    return hits


def summary_of(run: pathlib.Path) -> dict:
    s = run / "run_summary.json"
    return json.loads(s.read_text()) if s.exists() else {}


def verify_reference(keys: pathlib.Path) -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for sid, pair in REFERENCE.items():
            for rel in pair:
                src = ROOT / "reference" / rel
                rec = json.loads((src / STAGES[sid][7]).read_text())
                rec = rec.get("total", rec.get("auto_total_40"))
                dst = pathlib.Path(td) / rel
                shutil.copytree(src, dst)
                (dst / STAGES[sid][7]).unlink()
                got = run_score(sid, dst, keys)
                ok = got is not None and abs(got - rec) < 0.01
                bad += not ok
                print(f"{'ok      ' if ok else 'MISMATCH'} {sid:8s} {rel:42s} recorded {rec:g}  re-scored {got}")
    return bad


def weighted(rows: list[dict], key: str) -> tuple[float, float, bool]:
    corr = sum(r["w"] * r[key] / r["max"] for r in rows) / sum(r["w"] for r in rows) * 70
    eff = sum(min(r["opus_sec"], r[key + "_sec"]) / r[key + "_sec"] for r in rows) / len(rows) * 30
    gate = all(r[key] / r["max"] >= PASS for r in rows)
    return corr, eff, gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", help="directory holding <stage>-r<k>/ run directories")
    ap.add_argument("--keys", default=str(pathlib.Path.home() / "qwenpoc-keys"))
    ap.add_argument("--verify-reference", action="store_true")
    a = ap.parse_args()
    keys = pathlib.Path(a.keys).expanduser().resolve()
    if a.verify_reference:
        sys.exit(1 if verify_reference(keys) else 0)
    base = pathlib.Path(a.runs).resolve()
    rows = []
    for sid, (title, ph, w, mx, *_rest) in STAGES.items():
        runs = sorted(p for p in base.glob(f"{sid}-r*") if p.is_dir())
        if not runs:
            continue
        o_rel, q_rel = REFERENCE[sid]
        ref = lambda rel: (lambda d: d.get("total", d.get("auto_total_40")))(json.loads((ROOT / "reference" / rel / STAGES[sid][7]).read_text()))
        qs = summary_of(ROOT / "reference" / q_rel)
        for run in runs:
            sc = run_score(sid, run, keys)
            s = summary_of(run)
            flags = audit(run)
            for f in flags:
                print(f"  AUDIT {sid}/{run.name}: {f}  <- read the code in bench_log.jsonl and judge", file=sys.stderr)
            rows.append(dict(stage=sid, run=run.name, title=title, w=w, max=mx, new=sc if sc is not None else 0.0,
                             new_sec=s.get("seconds") or 1e9, reason=s.get("reason"), calls=s.get("bench_calls"),
                             peak=s.get("peak_prompt_tokens"), cost=s.get("cost_usd"),
                             opus=ref(o_rel), opus_sec=OPUS_SECONDS[sid], cloud=ref(q_rel), cloud_sec=qs.get("seconds"),
                             cloud_peak=qs.get("peak_prompt_tokens"), audit=flags))
    if not rows:
        sys.exit(f"no runs under {base}")
    lines = ["| stage | run | score | cloud Qwen | Opus | end | seconds (cloud Qwen / Opus) | calls | peak prompt tokens (cloud) | audit |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        pk = f"{r['peak']:,}" if r["peak"] else "-"
        pk += f" ({r['cloud_peak']:,})" if r["cloud_peak"] else ""
        if r["peak"] and r["peak"] >= 0.85 * NATIVE_CTX:
            pk = "**" + pk + "**"
        lines.append(f"| {r['stage']} | {r['run']} | **{r['new']:g}**/{r['max']} | {r['cloud']:g} | {r['opus']:g} | {r['reason']} | "
                     f"{r['new_sec']:.0f} ({r['cloud_sec'] or 0:.0f} / {r['opus_sec']}) | {r['calls']} | {pk} | "
                     f"{'CHECK ' + str(len(r['audit'])) if r['audit'] else 'clean'} |")
    # verdict on the first run of each stage, only if all 10 stages are present
    first = {}
    for r in rows:
        first.setdefault(r["stage"], r)
    if len(first) == len(STAGES):
        c, e, gate = weighted(list(first.values()), "new")
        tot = c + e
        lines += ["", f"Weighted total (first run of each stage): **{tot:.1f}** = correctness {c:.1f}/70 + efficiency {e:.1f}/30; "
                      f"every stage >= 80 %: {'yes' if gate else 'NO'} -> **{'PASS' if gate and tot >= 80 else 'FAIL'}**",
                  "Reference: Opus 5.5 99.1 PASS; cloud Qwen 3.8 Flash 62.7 FAIL (S1P 52.6 and D1 60.0 below 80 %)."]
    else:
        lines += ["", f"Verdict needs all {len(STAGES)} stages; have {len(first)}: {', '.join(first)}"]
    md = "\n".join(lines) + "\n"
    (base / "summary.md").write_text(md)
    (base / "summary.json").write_text(json.dumps(rows, indent=1))
    print(md)


if __name__ == "__main__":
    main()

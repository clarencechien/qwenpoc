#!/usr/bin/env python3
"""Run benchmark stages against a model endpoint: init the run directory, let the model work, record the result.

    # self-hosted Qwen3.8-Flash-Next (vLLM / SGLang, OpenAI-compatible)
    python3 scripts/run_all.py --runs runs/onprem --base-url http://localhost:8000/v1 --model Qwen/Qwen3.8-Flash-Next

    # the cloud reference (OpenRouter, needs OPENROUTER_API_KEY), e.g. one cheap stage as a smoke test
    python3 scripts/run_all.py --runs runs/cloud --stages s3-hard --max-cost 0.5

Each stage goes to RUNS/<stage>-r<k>/ (k = 1..--repeat). A stage directory that already has run_summary.json is
skipped, so the command can be re-run after an interruption (delete the half-finished directory first).
Scoring is a separate step (scripts/score_all.py) so that the answer keys need not exist while the model runs.
"""
from __future__ import annotations

import argparse
import pathlib
import shlex
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stages import STAGES  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="output directory, e.g. runs/onprem")
    ap.add_argument("--stages", default=",".join(STAGES), help=f"comma list from: {', '.join(STAGES)}")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--model", default=None, help="model name sent to the endpoint (default: runner default qwen/qwen3.8-flash)")
    ap.add_argument("--base-url", help="OpenAI-compatible endpoint, e.g. http://localhost:8000/v1 (omit for OpenRouter)")
    ap.add_argument("--api-key-env", help="environment variable holding the endpoint's key")
    ap.add_argument("--reasoning-effort", default="high", choices=["low", "medium", "high", "none"])
    ap.add_argument("--extra-body", help="JSON merged into every request")
    ap.add_argument("--max-tokens", type=int, default=64000, help="max output tokens per reply")
    ap.add_argument("--max-cost", type=float, default=1.0, help="USD cap per stage (OpenRouter only)")
    ap.add_argument("--keys-ok", action="store_true", help="do not refuse to start when ~/qwenpoc-keys exists")
    a = ap.parse_args()

    if not shutil.which("bench"):
        sys.exit("`bench` is not on PATH: run `sudo bash bench/install.sh` first")
    keys = pathlib.Path.home() / "qwenpoc-keys"
    if keys.exists() and not a.keys_ok:
        sys.exit(f"{keys} exists. Blender exec code is not sandboxed, so build the answer keys AFTER the runs "
                 "(or move them off this machine). Use --keys-ok to start anyway.")
    base = (ROOT / a.runs).resolve() if not pathlib.Path(a.runs).is_absolute() else pathlib.Path(a.runs)
    base.mkdir(parents=True, exist_ok=True)
    todo = [s.strip() for s in a.stages.split(",") if s.strip()]
    for sid in todo:
        if sid not in STAGES:
            sys.exit(f"unknown stage {sid}")
    for k in range(1, a.repeat + 1):
        for sid in todo:
            title, ph, w, mx, init, runner, cmd, out = STAGES[sid]
            run = base / f"{sid}-r{k}"
            if (run / "run_summary.json").exists():
                print(f"skip {run.name} (done)")
                continue
            if run.exists():
                sys.exit(f"{run} exists but has no run_summary.json (interrupted?). Delete it and start again.")
            print(f"=== {run.name}: {title}", flush=True)
            subprocess.run([sys.executable, "bench/bench_admin.py", "init", "--run", str(run), "--budget", "60", *shlex.split(init)],
                           cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
            cmdline = [sys.executable, "harness/qwen_runner.py", "--run", str(run), *shlex.split(runner),
                       "--max-tokens", str(a.max_tokens), "--max-cost", str(a.max_cost)]
            if a.reasoning_effort != "none":
                cmdline += ["--reasoning-effort", a.reasoning_effort]
            for flag, val in (("--model", a.model), ("--base-url", a.base_url), ("--api-key-env", a.api_key_env),
                              ("--extra-body", a.extra_body)):
                if val:
                    cmdline += [flag, val]
            t0 = time.time()
            with open(run / "runner.out", "w") as f:
                rc = subprocess.run(cmdline, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
            tail = (run / "runner.out").read_text().strip().splitlines()[-3:]
            print(f"    exit {rc} after {time.time() - t0:.0f} s; " + " | ".join(tail), flush=True)
            subprocess.run([sys.executable, "bench/bench_admin.py", "stop"], cwd=ROOT, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()

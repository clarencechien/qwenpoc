# AGENTS.md — instructions for the agent operating this benchmark

You (Codex, Claude Code or another coding agent) are the **operator** of this benchmark, not the participant. Your job is
to run the 10 Blender stages against a self-hosted **Qwen3.8-Flash-Next** endpoint, score the runs, and report the
numbers next to the reference results. The participant model only ever sees one run directory through
`harness/qwen_runner.py`.

Human-oriented version of the same procedure (Traditional Chinese): `docs/REPRODUCE.md`. Project background, full results, cost data and open tasks for an agent taking over the whole project: `docs/AGENT_HANDOFF.md`. Results and verdict being
checked: `report/full_report.html`.

## Hard rules

1. **Never let the participant see an answer.** Answer keys are rebuilt from seeds by `scripts/make_keys.sh` into a
   directory **outside the repo** (default `~/qwenpoc-keys`). Build them only **after** all runs have finished:
   Python run through `bench exec` is not sandboxed and could read any file on the machine. `run_all.py` refuses to
   start while `~/qwenpoc-keys` exists.
2. **Do not change what is being measured**: no edits to `harness/prompts/`, `harness/qwen_runner.py` tool rules,
   `bench/` limits (60 counted calls, 45 or 60 minutes), `score/`, `gen/`, `oracle/`, `inputs/`. If something is
   broken, stop and report it instead of patching around it. Server-side settings (`--extra-body`, `--max-tokens`,
   endpoint URL) are fine to adapt; record what you used.
3. **Never commit** `runs/`, the key directory, API keys or endpoint credentials. `runs/` is gitignored.
4. Keep `reference/` read-only. It holds the recorded runs the report is based on.
5. Do not push to a remote or open pull requests unless the human asks.

## Procedure

Run every command from the repository root.

### 1. Install (once, needs root)

```bash
sudo bash bench/install.sh          # Blender 4.2 LTS -> /opt/blender, Mesa EGL libs, `bench` on PATH
pip install requests pillow numpy scipy shapely
bench --help                        # must print the bench usage
```

No GPU is needed on this machine: Blender only renders Workbench previews (CPU, ~1 s each).

### 2. Check the endpoint

The endpoint must be OpenAI-compatible `/v1/chat/completions` with **tool calling and image input**. Typical vLLM start
(confirm flags against the vLLM version in use):

```bash
vllm serve Qwen/Qwen3.8-Flash-Next --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3
```

Ask the human which context length the server runs with (native 262,144 or YaRN-extended), the precision
(BF16 / FP8 / other quantisation), the GPUs and the framework version. Record all four; they go in the report.

### 3. Smoke test (≈ 10 min)

```bash
python3 scripts/run_all.py --runs runs/onprem --stages s3-hard --base-url http://HOST:8000/v1 --model Qwen/Qwen3.8-Flash-Next
```

Expect `runs/onprem/s3-hard-r1/run_summary.json` with `"reason": "submitted"`. If `reason` starts with `api_stop`,
read `runner.out` and the last lines of `transcript.jsonl`; typical causes: tool calling not enabled on the server, the
reasoning field not accepted (`--reasoning-effort none` plus `--extra-body '{...}'`), or no image support.

### 4. All 10 stages (≈ 5–8 h at cloud speed; on-prem speed decides)

```bash
python3 scripts/run_all.py --runs runs/onprem --base-url http://HOST:8000/v1 --model Qwen/Qwen3.8-Flash-Next
```

- Stages: `s1-easy s1-hard s2 s3-easy s3-hard s1p d1 d2 d3 d5` (definitions in `scripts/stages.py`).
- Re-running the same command skips finished stages. If a stage was interrupted, delete its directory first.
- `--repeat 2` gives a second run of every stage (`*-r2`); recommended if time allows, the reference is one run each.
- If the human wants both context settings, use two output directories, e.g. `runs/onprem-262k` and `runs/onprem-1m`.
- Do not "help" a run that ends early (context overflow, timeout): that outcome is the measurement.

### 5. Answer keys (after the runs)

```bash
bash scripts/make_keys.sh ~/qwenpoc-keys
```

Takes under a minute; the last lines must all read `ok`. A `MISMATCH` means the generators changed — stop.

Optional sanity check that scoring on this machine matches the recorded results (≈ 2 min, must print 20 × `ok`):

```bash
python3 scripts/score_all.py --verify-reference --keys ~/qwenpoc-keys
```

### 6. Score and summarise

```bash
python3 scripts/score_all.py --runs runs/onprem --keys ~/qwenpoc-keys
```

Writes `runs/onprem/summary.md` and `summary.json`: per stage the on-prem score next to the cloud Qwen and Opus
reference, end reason, seconds, bench calls, peak prompt tokens (bold when ≥ 85 % of 262,144) and an audit column.
With all 10 stages present it also prints the weighted verdict used in the report (every stage ≥ 80 % **and**
weighted total ≥ 80; reference: Opus 99.1 pass, cloud Qwen 62.7 fail).

`audit: CHECK n` means some `bench exec` code mentions a path outside its run directory or a key-file name. Open
`bench_log.jsonl` at the listed lines and decide whether it was harmless (e.g. writing a temp file) or an attempt to
read answers; say which in the report.

### 7. Report back to the human

Give: the summary table; the four endpoint facts from step 2; per stage the `reason` and, for any stage that did not
end `submitted`, what happened (last error from `runner.out`); the peak prompt tokens of S1P, D1 and D5 against the
context limit; the total API time. State plainly whether the result supports or contradicts the report's claim that the
on-prem model does no better than the cloud one.

## Repository map

| Path | What |
|---|---|
| `bench/` | `bench` CLI (the participant's only access to Blender) + persistent headless Blender server, `bench_admin.py` to init/stop a run |
| `harness/qwen_runner.py` | agent loop for any OpenAI-compatible endpoint; tools: one `bench` command, write file, read file/image (images downscaled to 1568 px) — all confined to the run directory |
| `harness/prompts/` | `system.md` + one prompt per stage, identical for both models |
| `inputs/`, `ref/` | stage inputs copied into each run directory (`ref/` = public rack photos for S2, licences in `ref/LICENSES.md`) |
| `gen/`, `oracle/` | scenario generators and reference solvers (operator side; produce the answer keys) |
| `score/` | programmatic scorers, one per stage; review-image scripts (`*_overlay.py`, `d3_view.py`, `d5_compare.py`) |
| `scripts/` | `run_all.py`, `make_keys.sh`, `score_all.py`, `stages.py` (single source of stage definitions), `opus_prompt.py` |
| `reference/` | recorded runs behind the report: `opus-5.5/…`, `qwen3.8-flash/…` (scores, transcripts, bench logs, participant code; `.blend` only where a scorer needs it) |
| `report/` | `full_report.html` (phase 1 + 2, verdict), `phase1.html` |

## Re-running the Opus side (only if asked)

The reference Opus runs were fresh Claude Code sessions given the prompt printed by
`python3 scripts/opus_prompt.py --run RUN --stage STAGE`, with the run directory initialised by `bench_admin.py init`
using the same arguments as in `scripts/stages.py`. While such a run is in progress, `reference/` and the key
directory must not be on the machine (the participant is told not to look, but nothing enforces it). The participant
must be a session that has never seen this repository's answers — not the operator session.

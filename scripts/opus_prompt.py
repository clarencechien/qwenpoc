#!/usr/bin/env python3
"""Print the exact prompt the Opus side was given (for re-running a Claude model as the participant).

    python3 scripts/opus_prompt.py --run runs/opus/d5-r1 --stage d5 > /tmp/prompt.txt

How the reference Opus runs were made: a FRESH Claude Code session (subagent, model opus, effort high) received this
prompt, with the run directory initialised by bench_admin.py exactly as for Qwen. During the run the answer keys and
the other model's outputs were NOT on disk (move reference/ and the key directory off the machine). Afterwards the
session transcript was checked for any Read/Write/Bash outside the run directory.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stages import STAGES  # noqa: E402

PRE = """Your working directory (the run directory) is `{run}`.

Rules for this exercise (they mirror the tools the other participant gets, so please follow them exactly):
- Use only three tools: **Bash**, **Write** and **Read** (not Edit — to change a file, Write it again).
- With Bash, run only `cd {run} && bench ...` — a single bench command, no pipes, redirects, chaining beyond that cd, or any other program. Quote arguments that contain `>`.
- With Write and Read, touch only files inside the run directory. Do not read or list anything outside it: not the repository, not other runs, not git, not /tmp.
- No web access, no subagents.
- When you are done, reply with a two-line summary: whether you submitted, and how many bench calls you used.

---

"""

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True)
ap.add_argument("--stage", required=True, choices=list(STAGES))
a = ap.parse_args()
run = pathlib.Path(a.run).resolve()
runner_args = STAGES[a.stage][5].split()
prompt = runner_args[runner_args.index("--prompt") + 1] if "--prompt" in runner_args else runner_args[runner_args.index("--stage") + 1]
P = ROOT / "harness" / "prompts"
print(PRE.format(run=run) + (P / "system.md").read_text().strip() + "\n\n---\n\n" + (P / f"{prompt}.md").read_text().strip())

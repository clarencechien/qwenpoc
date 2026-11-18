"""The 10 benchmark stages: how to set each one up, run it and score it. Shared by run_all.py and score_all.py.

KEY = answer-key directory built by scripts/make_keys.sh (outside the repo). RUN = run directory.
"""
from __future__ import annotations

BLENDER = "/opt/blender/blender"

# id: (title, phase, report weight, max score, bench_admin init args, qwen_runner args, score command, score file)
STAGES = {
    "s1-easy": ("S1 plan -> 3D room (easy, 16 racks)", 1, 3, 100,
                "--stage s1 --scenario easy --minutes 45",
                "--stage s1",
                "python3 score/s1_layout.py --run {RUN} --gt {KEY}/easy --out {RUN}/score_s1.json", "score_s1.json"),
    "s1-hard": ("S1 plan -> 3D room (hard, 58 racks)", 1, 5, 100,
                "--stage s1 --scenario hard --minutes 45",
                "--stage s1 --prompt s1-hard",
                "python3 score/s1_layout.py --run {RUN} --gt {KEY}/hard --out {RUN}/score_s1.json", "score_s1.json"),
    "s2": ("S2 photos -> rack model (geometry only, max 40)", 1, 5, 40,
           "--stage s2 --scenario easy --minutes 45",
           "--stage s2",
           "python3 score/s2_rack.py --run {RUN} --out {RUN}/score_s2_auto.json", "score_s2_auto.json"),
    "s3-easy": ("S3 place racks (easy)", 1, 2, 100,
                "--stage s3 --scenario easy-s3 --start inputs/easy-s3/s3_start.blend --minutes 45",
                "--stage s3",
                "python3 score/s3_place.py --run {RUN} --layout inputs/easy-s3/layout.json --out {RUN}/score_s3.json", "score_s3.json"),
    "s3-hard": ("S3 place racks (hard)", 1, 5, 100,
                "--stage s3 --scenario hard-s3 --start inputs/hard-s3/s3_start.blend --minutes 45",
                "--stage s3 --prompt s3-hard",
                "python3 score/s3_place.py --run {RUN} --layout inputs/hard-s3/layout.json --out {RUN}/score_s3.json", "score_s3.json"),
    "s1p": ("S1P site photos -> layout", 1, 15, 100,
            "--stage s1p --scenario photo-hard --start inputs/photo-hard/start.blend --minutes 60",
            "--stage s1p --prompt s1p --max-turns 200",
            "python3 score/s1p_photo.py --run {RUN} --gt {KEY}/photo/layout.json --out {RUN}/score_s1p.json", "score_s1p.json"),
    "d1": ("D1 as-built check (design vs site photos)", 2, 15, 100,
           "--stage d1 --scenario d1 --start inputs/d1/start.blend --minutes 60",
           "--stage d1 --max-turns 200",
           "python3 score/d1_asbuilt.py --run {RUN} --design inputs/d1/design.json --gt {KEY}/d1/asbuilt.json --out {RUN}/score_d1.json",
           "score_d1.json"),
    "d2": ("D2 layout design under a rule book", 2, 10, 100,
           "--stage d2 --scenario d2 --start inputs/d2/start.blend --minutes 45",
           "--stage d2 --max-turns 200",
           "python3 score/d2_design.py --run {RUN} --room inputs/d2/room.json --ref 250 --out {RUN}/score_d2.json", "score_d2.json"),
    "d3": ("D3 overhead coolant pipe routing", 2, 5, 100,
           "--stage d3 --scenario d3 --start inputs/d3/start.blend --minutes 45",
           "--stage d3 --max-turns 200",
           "python3 score/d3_routes.py --run {RUN} --scene {KEY}/d3/scene.json --ref {KEY}/d3/ref/ref.json --out {RUN}/score_d3.json",
           "score_d3.json"),
    "d5": ("D5 rebuild a CDU from orthographic views", 2, 5, 100,
           "--stage d5 --scenario d5 --minutes 45",
           "--stage d5 --max-turns 200",
           BLENDER + " -b {RUN}/d5.blend --python score/d5_voxel.py -- --gt {KEY}/d5/target.json --out {RUN}/score_d5.json",
           "score_d5.json"),
}

# reference runs (results in reference/, recorded 2026-11; Qwen = OpenRouter qwen/qwen3.8-flash, reasoning effort high)
REFERENCE = {
    "s1-easy": ("opus-5.5/easy/s1-r1", "qwen3.8-flash/easy/s1-r2-high"),
    "s1-hard": ("opus-5.5/hard/s1-r1", "qwen3.8-flash/hard/s1-r1-high"),
    "s2": ("opus-5.5/easy/s2-r1", "qwen3.8-flash/easy/s2-r2-high"),
    "s3-easy": ("opus-5.5/easy/s3-r1", "qwen3.8-flash/easy/s3-r2-high"),
    "s3-hard": ("opus-5.5/hard/s3-r1", "qwen3.8-flash/hard/s3-r1-high"),
    "s1p": ("opus-5.5/photo-hard/s1p-r1", "qwen3.8-flash/photo-hard/s1p-r1-high"),
    "d1": ("opus-5.5/phase2/d1-r1", "qwen3.8-flash/phase2/d1-r1-high"),
    "d2": ("opus-5.5/phase2/d2-r1", "qwen3.8-flash/phase2/d2-r1-high"),
    "d3": ("opus-5.5/phase2/d3-r1", "qwen3.8-flash/phase2/d3-r2-high"),
    "d5": ("opus-5.5/phase2/d5-r1", "qwen3.8-flash/phase2/d5-r1-high"),
}
# Opus ran as Claude Code sessions (no run_summary.json); wall-clock seconds from the session logs
OPUS_SECONDS = {"s1-easy": 66, "s1-hard": 95, "s2": 543, "s3-easy": 102, "s3-hard": 135, "s1p": 954,
                "d1": 567, "d2": 699, "d3": 468, "d5": 154}
PASS = 0.8
NATIVE_CTX = 262_144

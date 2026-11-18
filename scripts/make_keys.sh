#!/usr/bin/env bash
# Rebuild every answer key from its fixed seed, OUTSIDE the repo (the model under test must never see them).
#   bash scripts/make_keys.sh [KEYDIR]        default KEYDIR: ~/qwenpoc-keys
# Takes ~3 min (the D3 reference router is the slow part). Needs /opt/blender (bench/install.sh) for D5.
set -euo pipefail
cd "$(dirname "$0")/.."
K="${1:-$HOME/qwenpoc-keys}"
case "$(realpath -m "$K")" in "$(pwd)"*) echo "KEYDIR must be outside the repo" >&2; exit 1;; esac
BLENDER="${BENCH_BLENDER:-/opt/blender/blender}"
mkdir -p "$K"
python3 gen/layout_gen.py --scenario easy --seed 338793 --out "$K/easy"      # S1 easy
python3 gen/layout_gen.py --scenario hard --seed 806569 --out "$K/hard"      # S1 hard
python3 gen/layout_gen.py --scenario hard --seed 69495  --out "$K/photo"     # S1P
python3 gen/d1_asbuilt.py --seed 4 --out "$K/d1"                              # D1 (asbuilt.json, changes.json)
python3 gen/d3_scene.py --seed 1 --out "$K/d3"                                # D3 scene.json
python3 oracle/d3_router.py --scene "$K/d3/scene.json" --out "$K/d3/ref"      # D3 ref.json (shortest routes)
"$BLENDER" -b --factory-startup --python gen/d5_target.py -- --seed 5417 --out "$K/d5" >/dev/null   # D5 target.json
# D2 needs no key: the rule checker scores against N_REF = 250 (best design found by oracle/d2_solver.py, see docs).
python3 scripts/check_keys.py "$K"

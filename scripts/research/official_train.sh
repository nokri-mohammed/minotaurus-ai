#!/usr/bin/env bash
# Train the official shaped DQN brain: data/examples/dqn-shaped-brain.json with seeds 1 to 8 in
# parallel, CPU only (the DQN trainer uses one torch thread). Run from anywhere:
#   scripts/research/official_train.sh
# Writes runs/official-dqn-shaped/s<seed>/ (git-ignored) and prints the wall time.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
OUT=runs/official-dqn-shaped
mkdir -p "$OUT/configs"
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
start=$(date +%s)
for seed in 1 2 3 4 5 6 7 8; do
  uv run python - "$seed" "$OUT/configs/s$seed.json" <<'EOF'
import json, sys
data = json.load(open("data/examples/dqn-shaped-brain.json"))
data["seed"] = int(sys.argv[1])
data["name"] = f"dqn-shaped-s{sys.argv[1]}"
json.dump(data, open(sys.argv[2], "w"), indent=2)
EOF
  uv run minotaurus train --config "$OUT/configs/s$seed.json" --runs-dir "$OUT/s$seed" \
    --log-every 50 > "$OUT/train-s$seed.log" 2>&1 &
done
wait
echo "wall time: $(( $(date +%s) - start )) s"

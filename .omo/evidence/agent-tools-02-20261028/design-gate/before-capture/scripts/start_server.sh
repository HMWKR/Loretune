#!/bin/bash
# Start the owned capture fixture server under the loopback-only sandbox.
# usage: start_server.sh <ROOT(app source tree)> <OUT(fresh folder)>
# before: ROOT=before-capture/root   after: ROOT=/Users/leesungmin/Desktop/Loretune
# Python must be the project's interpreter (homebrew 3.15): /usr/bin/python3 3.9 rejects
# an empty query in parse_qs(strict_parsing=True) and /api/state returns 400 (attempt 1 evidence).
set -euo pipefail
ROOT="$(cd "$1" && pwd)"; OUT="$2"; HERE="$(cd "$(dirname "$0")" && pwd)"
PY=/opt/homebrew/bin/python3
"$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 15), sys.version'
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
[ -e "$OUT/workspace/data" ] && { echo "OUT already has workspace/data — use a fresh folder"; exit 1; }
cd "$OUT"
env -i HOME="$HOME" PATH="/opt/homebrew/bin:/usr/bin:/bin" PYTHONDONTWRITEBYTECODE=1 \
  sandbox-exec -f "$HERE/network-loopback-only.sb" "$PY" -u "$HERE/serve_capture_fixture.py" "$ROOT" "$OUT" \
  > "$OUT/fixture-server.log" 2>&1 &
echo $! > "$OUT/launcher.pid"
for i in $(seq 1 60); do [ -f "$OUT/ready.json" ] && break; sleep 1; done
[ -f "$OUT/ready.json" ] || { echo "server not ready"; tail -20 "$OUT/fixture-server.log"; exit 1; }
"$PY" --version > "$OUT/python-version.txt"
cat "$OUT/ready.json"

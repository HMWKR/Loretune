#!/bin/bash
# Repeat the exact capture conditions for the "after" state.
# usage: run_after.sh [ROOT=/Users/leesungmin/Desktop/Loretune] [OUT=../../after-capture]
# Same seed script, same sandbox, same capture template/widths/states; only ROOT and TAG differ.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${1:-/Users/leesungmin/Desktop/Loretune}"; OUT="${2:-$HERE/../../after-capture}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
for p in 8765 57888; do echo "PORT $p"; lsof -nP -iTCP:$p -sTCP:LISTEN || echo "no listener"; done > "$OUT/ports-baseline.txt" 2>&1
"$HERE/start_server.sh" "$ROOT" "$OUT/server" || exit 1
PORT=$(/opt/homebrew/bin/python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['port'])" "$OUT/server/ready.json")
"$HERE/capture.sh" "http://127.0.0.1:$PORT" "$OUT" after "$OUT/server/fixture-start.json"
"$HERE/stop_server.sh" "$OUT/server"
for p in 8765 57888; do echo "PORT $p"; lsof -nP -iTCP:$p -sTCP:LISTEN || echo "no listener"; done > "$OUT/ports-after.txt" 2>&1
diff "$OUT/ports-baseline.txt" "$OUT/ports-after.txt" && echo "reserved ports unchanged"

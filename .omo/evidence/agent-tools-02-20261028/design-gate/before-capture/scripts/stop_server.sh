#!/bin/bash
# usage: stop_server.sh <OUT> — SIGTERM the fixture pid recorded in OUT/fixture-start.json and wait.
set -uo pipefail
OUT="$1"; P=$(/opt/homebrew/bin/python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['pid'])" "$OUT/fixture-start.json")
ps -o pid=,command= -p "$P" | grep -q serve_capture_fixture.py || { echo "pid $P is not the fixture server"; exit 1; }
kill -TERM "$P"; for i in $(seq 1 15); do kill -0 "$P" 2>/dev/null || break; sleep 1; done
kill -0 "$P" 2>/dev/null && { echo "still running: $P"; exit 1; }
echo "stopped $P"; cat "$OUT/fixture-stop.json"

#!/bin/bash
# Capture every (width x state) with aside repl and record captures.json.
# usage: capture.sh <ORIGIN e.g. http://127.0.0.1:62828> <OUTDIR> [TAG=before] [SEED_JSON=fixture-start.json path]
# Optional env filters for trials: ONLY_W=<width> ONLY_S=<state>.
# Each call renders capture-state.js into <OUTDIR>/repl/<state>_<w>.js (exact code sent) and runs it once.
set -uo pipefail
ORIGIN="$1"; OUT="$2"; TAG="${3:-before}"; SEED="${4:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[[ "$ORIGIN" =~ ^http://127\.0\.0\.1:[0-9]+$ ]] || { echo "loopback origin only"; exit 1; }
pgrep -f Aside.app >/dev/null || { echo "Aside not running"; exit 1; }
mkdir -p "$OUT/repl" "$OUT/raw" "$OUT/png"
WIDTHS=("1920 1080 0.75" "1280 900 1" "375 812 1")   # width height css-scale (1920 does not fit the 1440x900 Aside tab)
STATES=(a_first_load a2_step1_music b_ai_panel_open c_ai_panel_closed d_shotboard_media_card e_timeline_edit e2_timeline_edit_panel_closed f_dialog_new_project)
for wh in "${WIDTHS[@]}"; do
  set -- $wh; W=$1; H=$2; SC=$3
  [ -n "${ONLY_W:-}" ] && [ "$W" != "$ONLY_W" ] && continue
  for S in "${STATES[@]}"; do
    [ -n "${ONLY_S:-}" ] && [ "$S" != "$ONLY_S" ] && continue
    JS="$OUT/repl/${S}_${W}.js"; RAW="$OUT/raw/${S}_${W}.txt"; PNG="$OUT/png/${TAG}_${S}_${W}x${H}.png"
    /opt/homebrew/bin/python3 - "$HERE/capture-state.js" "$JS" "$ORIGIN" "$W" "$H" "$S" "$SC" <<'PY'
import json, sys
src, dst, origin, w, h, s, sc = sys.argv[1:]
t = open(src, encoding='utf-8').read()
t = t.replace('__ORIGIN__', json.dumps(origin)).replace('__W__', str(int(w))).replace('__H__', str(int(h))).replace('__SCALE__', repr(float(sc)) if float(sc) != 1 else '1').replace('__STATE__', json.dumps(s))
open(dst, 'w', encoding='utf-8').write(t)
PY
    START=$(date -u +%FT%TZ)
    aside repl "$(cat "$JS")" > "$RAW" 2>&1
    rm -f "$PNG"
    sed -n "/^PNG_${S}_${W}_START\$/,/^PNG_${S}_${W}_END\$/p" "$RAW" | sed '1d;$d' | tr -d '\n' | base64 -d > "$PNG" 2>/dev/null
    FT=$(file -b "$PNG")
    echo "$S $W: $FT"
    /opt/homebrew/bin/python3 - "$RAW" "$PNG" "$JS" "$OUT/captures.jsonl" "$START" "$ORIGIN" "$TAG" "$SEED" "$FT" <<'PY'
import hashlib, json, os, re, sys
raw, png, js, out, start, origin, tag, seed, ft = sys.argv[1:]
text = open(raw, encoding='utf-8', errors='replace').read()
m = re.findall(r'^META (.*)$', text, re.M)
meta = json.loads(m[-1]) if m else {'error': 'NO_META', 'raw_tail': text[-400:]}
rec = dict(tag=tag, started_utc=start, origin=origin, capture_url=origin + '/ (iframe in host tab ' + origin + '/studio.css)',
           png=os.path.relpath(png, os.path.dirname(out)), file=ft,
           png_sha256=hashlib.sha256(open(png, 'rb').read()).hexdigest() if os.path.getsize(png) else None,
           png_bytes=os.path.getsize(png), repl_script=os.path.relpath(js, os.path.dirname(out)),
           repl_script_sha256=hashlib.sha256(open(js, 'rb').read()).hexdigest(), fixture_seed=seed or None, **{('app_url' if k=='url' else k):v for k,v in meta.items()})
open(out, 'a', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False) + '\n')
PY
    # keep raw log small: drop base64 body once PNG is decoded
    if [[ "$FT" == PNG* ]]; then awk '/^PNG_.*_START$/{s=1;print "<base64 removed; see png>";next} /^PNG_.*_END$/{s=0;next} !s' "$RAW" > "$RAW.tmp" && mv "$RAW.tmp" "$RAW"; fi
  done
done

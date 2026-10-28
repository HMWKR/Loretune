"""Read current CSS tokens and calculate specified opaque sRGB role pairs.
This is source arithmetic, not browser/computed-style or WCAG conformance QA.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
css = (ROOT / 'studio.css').read_text()
tokens = dict(re.findall(r'(--ui-[\w-]+):\s*(#[0-9a-fA-F]{6})\s*;', css))
pairs = [
    ('strong/panel', 'strong', 'panel'),
    ('body/panel', 'body', 'panel'),
    ('muted/panel', 'muted', 'panel'),
    ('muted/hover', 'muted', 'hover'),
    ('primary foreground/background', 'canvas', 'strong'),
    ('error/error surface', 'error', 'error-bg'),
    ('warning/panel', 'warning', 'panel'),
    ('control edge/panel', 'control', 'panel'),
    ('control edge/hover', 'control', 'hover'),
    ('focus/panel', 'focus', 'panel'),
    ('selection edge/selected', 'selection-edge', 'selected'),
    ('quiet divider/panel (decorative)', 'line', 'panel'),
]

def lum(value):
    rgb = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))

rows = []
for label, fg, bg in pairs:
    foreground, background = tokens['--ui-' + fg], tokens['--ui-' + bg]
    high, low = sorted((lum(foreground), lum(background)), reverse=True)
    rows.append(dict(pair=label, foreground=foreground, background=background,
                     contrast=round((high + .05) / (low + .05), 4)))
result = dict(method='opaque sRGB token arithmetic; no rendered cascade/opacity/forced-colors validation', pairs=rows)
out = Path(__file__).with_name('token-pairs.json')
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))

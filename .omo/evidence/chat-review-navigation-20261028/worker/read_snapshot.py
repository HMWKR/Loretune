"""Read-only SQLite fingerprints for the owned rehearsal fixture."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

path = Path(__file__).parent/'workspace/data/studio.sqlite3'
with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as connection:
    tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    result = {}
    for table in tables:
        rows = connection.execute('SELECT * FROM "'+table.replace('"','""')+'" ORDER BY rowid').fetchall()
        raw = json.dumps(rows, ensure_ascii=False, sort_keys=True, default=lambda value:value.hex()).encode()
        result[table] = dict(count=len(rows), sha256=hashlib.sha256(raw).hexdigest())
print(json.dumps(result, sort_keys=True))

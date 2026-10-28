"""D1-r5 SQLite residue probe (stdlib only, writes only under ./run-<label>/ of the cwd).

Usage: PYTHONDONTWRITEBYTECODE=1 <python> -B -I probe.py <label>
Each row body carries ONE random (non-periodic) base64 marker twice, the way a
general_chat_previews row carries frame base64 in message_body and count_body.
Counts are copies of a 64-char window from the middle of the marker, so a count
of N means N copies of the marker bytes are still in the file.
Connections use the same call shape as app.py Store.connect: sqlite3.connect(db, timeout=30),
a new connection per operation, no PRAGMA unless the scenario says so.
"""
import base64, json, os, shutil, sqlite3, sys
from pathlib import Path

label = sys.argv[1]
root = Path.cwd() / ('run-' + label)
root.mkdir(exist_ok=True)
MARK = base64.b64encode(os.urandom(30000)).decode()   # ~40 KB, larger than a page: overflow pages
WIN = MARK[20000:20064].encode()


def connect(db):
    return sqlite3.connect(db, timeout=30)


def hits(path):
    return Path(path).read_bytes().count(WIN)


def fresh(name):
    db = root / name
    for p in root.glob(name + '*'):
        p.unlink()
    c = connect(db)
    with c:
        c.execute('CREATE TABLE general_chat_previews(id TEXT PRIMARY KEY, project TEXT, conversation TEXT, body TEXT)')
        c.execute('CREATE TABLE other(id INTEGER PRIMARY KEY, v TEXT)')
        c.executemany('INSERT INTO other(v) VALUES (?)', [('x' * 200,)] * 50)
        body = json.dumps(dict(message_body=dict(image=MARK), count_body=dict(image=MARK)))
        c.execute('INSERT INTO general_chat_previews VALUES (?,?,?,?)', ('p1', 'a', 'b', body))
    c.close()
    return db


def op(db, sql, pragma=None):
    c = connect(db)
    if pragma:
        c.execute(pragma)
    sd = c.execute('PRAGMA secure_delete').fetchone()[0]
    with c:
        c.execute(sql)
    c.close()
    return sd


c = sqlite3.connect(':memory:')
opts = [r[0] for r in c.execute('PRAGMA compile_options')]
d = connect(root / 'defaults.sqlite3')
print(f'[{label}] python {sys.version.split()[0]} exe {sys.executable} sqlite {sqlite3.sqlite_version}')
print(f'[{label}] default secure_delete={d.execute("PRAGMA secure_delete").fetchone()[0]} '
      f'journal_mode={d.execute("PRAGMA journal_mode").fetchone()[0]} auto_vacuum={d.execute("PRAGMA auto_vacuum").fetchone()[0]} '
      f'compile SECURE_DELETE={[o for o in opts if "SECURE_DELETE" in o]}')
d.close()

# A: default connection DELETE, then a raw-file backup copy (backup.py copies the file), then VACUUM.
db = fresh('a.sqlite3')
before = hits(db)
sd = op(db, "DELETE FROM general_chat_previews WHERE id='p1'")
after = hits(db)
backup = root / 'a-backup-after-delete.sqlite3'
shutil.copyfile(db, backup)
in_backup = hits(backup)
op(db, 'VACUUM')
print(f'[{label}] A default DELETE: secure_delete={sd} before={before} after_delete={after} backup_copied_after_delete={in_backup} after_vacuum={hits(db)}')

# B: PRAGMA secure_delete=ON on the deleting connection.
db = fresh('b.sqlite3')
sd = op(db, "DELETE FROM general_chat_previews WHERE id='p1'", 'PRAGMA secure_delete=ON')
print(f'[{label}] B ON on deleting connection: secure_delete={sd} after_delete={hits(db)}')

# C: ON set on an EARLIER connection only; a new connection deletes (per-connection setting).
db = fresh('c.sqlite3')
op(db, 'SELECT 1', 'PRAGMA secure_delete=ON')
sd = op(db, "DELETE FROM general_chat_previews WHERE id='p1'")
print(f'[{label}] C ON on earlier connection only: deleting connection secure_delete={sd} after_delete={hits(db)}')

# D: rewrite (UPDATE body to a frame-free value) instead of DELETE, default vs ON.
db = fresh('d.sqlite3')
sd = op(db, "UPDATE general_chat_previews SET body='{}' WHERE id='p1'")
d_default = hits(db)
db = fresh('e.sqlite3')
sd_on = op(db, "UPDATE general_chat_previews SET body='{}' WHERE id='p1'", 'PRAGMA secure_delete=ON')
print(f'[{label}] D rewrite UPDATE: default(secure_delete={sd}) after={d_default} | ON(secure_delete={sd_on}) after={hits(db)}')
print(f'[{label}] files: {sorted(p.name for p in root.iterdir())}')

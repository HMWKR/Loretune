"""Measure SQLite deleted-row residue: default pragmas, DELETE, secure_delete, VACUUM."""
import sqlite3, sys, base64, os
from pathlib import Path
MARK = base64.b64encode(b'FRAMEPROBE' * 400).decode()  # stands in for frame base64 inside a JSON body
def run(name, secure=None, vacuum=False):
    db = Path(name); [p.unlink() for p in db.parent.glob(db.name + '*') if p.exists()]
    c = sqlite3.connect(db, timeout=30)  # same call shape as app.py connect(): no PRAGMA
    if secure is not None: c.execute('PRAGMA secure_delete=' + secure)
    jm = c.execute('PRAGMA journal_mode').fetchone()[0]; sd = c.execute('PRAGMA secure_delete').fetchone()[0]
    av = c.execute('PRAGMA auto_vacuum').fetchone()[0]
    c.execute('CREATE TABLE general_chat_previews(id TEXT PRIMARY KEY, project TEXT, conversation TEXT, body TEXT)')
    c.execute('CREATE TABLE other(id INTEGER PRIMARY KEY, v TEXT)')
    with c: c.executemany('INSERT INTO other(v) VALUES (?)', [('x' * 200,)] * 50)
    with c: c.execute('INSERT INTO general_chat_previews VALUES (?,?,?,?)', ('p1', 'a', 'b', '{"message_body":"' + MARK + '"}'))
    before = db.read_bytes().count(MARK[:64].encode())
    with c: c.execute('DELETE FROM general_chat_previews WHERE id=?', ('p1',))
    rows = c.execute('SELECT count(*) FROM general_chat_previews').fetchone()[0]
    after_delete = db.read_bytes().count(MARK[:64].encode())
    if vacuum: c.execute('VACUUM')
    after_vacuum = db.read_bytes().count(MARK[:64].encode())
    c.close()
    print(f'{name}: sqlite {sqlite3.sqlite_version} journal_mode={jm} secure_delete={sd} auto_vacuum={av} | marker hits before_delete={before} rows_after_delete={rows} file_hits_after_delete={after_delete} after_vacuum({vacuum})={after_vacuum}')
run('default.sqlite3')
run('vacuum.sqlite3', vacuum=True)
run('secure.sqlite3', secure='ON')

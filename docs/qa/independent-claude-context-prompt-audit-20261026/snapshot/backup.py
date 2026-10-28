"""Offline verified backups. Stop the server before backing up; restore to a new folder."""
import argparse
from contextlib import closing
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root / 'backup-manifest.json').read_text())
    if manifest.get('format') != 'loretune-backup-v1':
        raise ValueError('지원하지 않는 백업 형식입니다.')
    for name, expected in manifest['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or str(Path(name)) != name:
            raise ValueError('백업은 정규 상대 경로만 허용합니다.')
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError('잘못된 백업 파일 경로입니다.')
        if digest(path) != expected:
            raise ValueError(f'백업 파일 해시 불일치: {name}')
    if 'studio.sqlite3' not in manifest['files']:
        raise ValueError('데이터베이스가 없는 백업입니다.')
    with closing(sqlite3.connect((root / 'studio.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('데이터베이스 무결성 오류입니다.')
    return manifest


def create(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError('원본 밖의 새 백업 폴더를 지정하세요.')
    with closing(sqlite3.connect((source / 'studio.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        if any(json.loads(row[0])['status'] in {'queued', 'running'} for row in db.execute('SELECT body FROM jobs')):
            raise ValueError('대기·진행 작업이 있습니다. 완료 후 서버를 종료하고 백업하세요.')
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='generation_jobs'").fetchone():
            active={'submitting','accepted','running','downloading','cancel_pending','cancel_sent'}
            if any(json.loads(row[0])['state'] in active for row in db.execute('SELECT body FROM generation_jobs')):
                raise ValueError('진행 중 생성·수신 작업이 있습니다. 상태 확인 후 서버를 종료하고 백업하세요.')
    files = [p for p in source.rglob('*') if p.is_file()]
    if any(p.is_symlink() or not p.resolve().is_relative_to(source) for p in source.rglob('*')):
        raise ValueError('심볼릭 링크가 포함된 저장소는 백업하지 않습니다.')
    destination.mkdir(parents=True)
    try:
        hashes = {}
        for path in files:
            relative = path.relative_to(source)
            if str(relative) == 'backup-manifest.json':
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            hashes[str(relative)] = digest(target)
            if digest(path) != hashes[str(relative)]:
                raise ValueError('백업 중 원본이 변경되었습니다. 서버 종료 후 다시 실행하세요.')
        (destination / 'backup-manifest.json').write_text(json.dumps(dict(format='loretune-backup-v1', source=str(source), files=hashes), ensure_ascii=False, indent=2))
        verify(destination)
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination


def restore(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    manifest = verify(source)
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError('복원은 백업 밖의 새 폴더에만 가능합니다.')
    destination.mkdir(parents=True)
    try:
        for name in manifest['files']:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        # Persisted local asset paths must point at the restored storage root.
        old = str(Path(manifest['source']).resolve()) + '/'
        def relocate(value, key=None):
            if isinstance(value, dict):
                return {k: relocate(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [relocate(v) for v in value]
            if key == 'asset' and isinstance(value, str) and value.startswith(old):
                return str(destination) + '/' + value[len(old):]
            return value
        with closing(sqlite3.connect(destination / 'studio.sqlite3')) as db, db:
            for table in ('state', 'jobs', 'generation_jobs'):
                if not db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():continue
                for identifier, body in db.execute(f'SELECT id,body FROM {table}').fetchall():
                    db.execute(f'UPDATE {table} SET body=? WHERE id=?', (json.dumps(relocate(json.loads(body))), identifier))
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'verify', 'restore'])
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path, nargs='?')
    args = parser.parse_args()
    if args.action != 'verify' and args.destination is None:
        parser.error('새 대상 폴더가 필요합니다.')
    result = verify(args.source) if args.action == 'verify' else globals()[args.action](args.source, args.destination)
    print('검증 완료' if args.action == 'verify' else result)

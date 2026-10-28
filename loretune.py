"""Offline workflow prototype. No model calls, credentials, or video encoding."""
from copy import deepcopy
from hashlib import sha256
import json

class Conflict(ValueError):
    pass

class Studio:
    def __init__(self):
        self.canon = []
        self.projects = {}

    def approve_setting(self, text, *, scope='ip', era='default', valid_from=0, valid_to=None):
        if not text or scope != 'ip' or valid_from < 0 or (valid_to is not None and valid_to < valid_from):
            raise ValueError('Invalid approved setting scope or story range')
        setting = dict(text=text, scope=scope, era=era, valid_from=valid_from,
                       valid_to=valid_to, revision=len(self.canon)+1, approved=True)
        self.canon.append(setting)
        return deepcopy(setting)

    def new_song(self, name, *, era='default', story=0, ip='default'):
        if not name or name in self.projects:
            raise ValueError('Song name must be unique and nonempty')
        snapshot = [deepcopy(s) for s in self.canon if s.get('ip','default') == ip and s.get('approved', False) and not s.get('superseded_by') and s['era'] == era and s['valid_from'] <= story
                    and (s['valid_to'] is None or story <= s['valid_to'])]
        self.projects[name] = dict(name=name, ip=ip, snapshot=snapshot, shots={}, revision=0)

    def plan_shot(self, song, shot, description):
        p = self.projects[song]
        if not shot or shot in p['shots'] or not description:
            raise ValueError('Invalid shot')
        p['shots'][shot] = dict(description=description, takes=[], selected=None, revision=0)
        p['revision'] += 1

    def attach_take(self, song, shot, asset, *, reason='existing asset', expected_revision):
        from pathlib import Path
        s = self.projects[song]['shots'][shot]
        if expected_revision != s['revision']:
            raise Conflict('Shot changed; reload before revising')
        path = Path(asset).resolve()
        if not path.is_file() or not reason:
            raise ValueError('Existing asset and revision reason required')
        take = dict(id=len(s['takes'])+1, asset=str(path), sha256=sha256(path.read_bytes()).hexdigest(), reason=reason)
        s['takes'].append(take)
        s['revision'] += 1
        self.projects[song]['revision'] += 1
        return take['id']

    def select_take(self, song, shot, take, *, expected_revision):
        s = self.projects[song]['shots'][shot]
        if expected_revision != s['revision']:
            raise Conflict('Selection changed; reload before selecting')
        if take not in [t['id'] for t in s['takes']]:
            raise ValueError('Take does not belong to this shot')
        s['selected'] = take
        s['revision'] += 1
        self.projects[song]['revision'] += 1

    def estimate(self, song):
        p = self.projects[song]
        if not p['shots'] or any(s['selected'] is None for s in p['shots'].values()):
            raise ValueError('Review and select every shot')
        return dict(kind='render-only', project=song, revision=p['revision'], generation_calls=0,
                    amount=0, currency='USD', basis='mock manifest export; not a production render price')

    def export(self, song, estimate, budget=0):
        from pathlib import Path
        if estimate != self.estimate(song) or budget < estimate['amount']:
            raise Conflict('Estimate stale or budget insufficient')
        p = deepcopy(self.projects[song])
        for s in p['shots'].values():
            t = next(t for t in s['takes'] if t['id'] == s['selected'])
            if sha256(Path(t['asset']).read_bytes()).hexdigest() != t['sha256']:
                raise Conflict('Asset changed since review')
        return json.dumps(dict(format='loretune-manifest-v1', renderer='mock', project=p, estimate=estimate), ensure_ascii=False, indent=2)

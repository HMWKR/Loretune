"""Explicit administrator startup configuration; no credential or network IO on load."""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

import chat_models


MAX_CONFIG_BYTES = 8192
FIELDS = frozenset({'version', 'enabled', 'workspace_id', 'connection_id',
                    'connection_revision', 'model', 'price_revision'})
ERROR = '일반 Claude 관리자 설정과 대상 작업공간을 확인하세요.'


class GeneralChatConfigError(ValueError):
    """Never includes configuration values or credentials."""


@dataclass(frozen=True)
class Configuration:
    version: int
    enabled: bool
    workspace_id: str
    connection_id: str
    connection_revision: int
    model: str
    price_revision: str

    def __post_init__(self):
        self.validate()

    def validate(self):
        try:
            spec = chat_models.contract('anthropic-haiku-5-5')
            if type(self.version) is not int or self.version != 1 or type(self.enabled) is not bool:
                raise ValueError()
            if type(self.workspace_id) is not str or str(uuid.UUID(self.workspace_id)) != self.workspace_id:
                raise ValueError()
            if type(self.connection_id) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', self.connection_id):
                raise ValueError()
            if type(self.connection_revision) is not int or not 1 <= self.connection_revision <= 2**53-1:
                raise ValueError()
            if (type(self.model) is not str or type(self.price_revision) is not str or
                    self.model != spec['model'] or self.price_revision != spec['price_revision']):
                raise ValueError()
        except (TypeError, ValueError, AttributeError):
            raise GeneralChatConfigError(ERROR) from None
        return self

    def digest(self):
        self.validate()
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def parse(value):
    if type(value) is Configuration:
        return value.validate()
    if type(value) is not dict or set(value) != FIELDS:
        raise GeneralChatConfigError(ERROR)
    try:
        return Configuration(**value)
    except (TypeError, ValueError):
        raise GeneralChatConfigError(ERROR) from None


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError()
        value[key] = item
    return value


def _constant(_):
    raise ValueError()


def load(path):
    """Read a bounded, owner-controlled JSON config; never read a key or env."""
    try:
        path = Path(path)
        if path.is_symlink():
            raise ValueError()
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid not in (0, os.geteuid()) or
                    info.st_mode & 0o022 or info.st_size > MAX_CONFIG_BYTES):
                raise ValueError()
            raw = stream.read(MAX_CONFIG_BYTES + 1)
        if len(raw) > MAX_CONFIG_BYTES:
            raise ValueError()
        return parse(json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant))
    except (OSError, TypeError, ValueError, UnicodeError):
        raise GeneralChatConfigError(ERROR) from None


def environment_credential(name):
    """Called only by the approved adapter operation, never by configuration."""
    if name != 'Anthropic_KEY':
        raise GeneralChatConfigError(ERROR)
    return os.environ.get(name)


def build(configuration, credential_supplier=None):
    settings = parse(configuration)
    if credential_supplier is not None and not callable(credential_supplier):
        raise GeneralChatConfigError(ERROR)
    if not settings.enabled:
        return None
    import chat_general
    import chat_runtime
    adapter = chat_runtime.AnthropicChatAdapter(
        credential_supplier if credential_supplier is not None else environment_credential,
        enabled=True,
    )
    return chat_general.LiveTransport(adapter, settings.connection_id,
                                      settings.connection_revision, activation=settings)

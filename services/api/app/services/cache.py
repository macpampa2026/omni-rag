"""Cache opcional en Redis.

Si no hay `REDIS_URL` (o Redis no responde), es un **no-op transparente**: la app
funciona igual, solo que sin cache. Así el mismo código corre con o sin Redis.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, url: str | None) -> None:
        self._client = None
        if not url:
            return
        try:
            import redis  # import perezoso: solo si se configura Redis

            self._client = redis.Redis.from_url(url, decode_responses=True)
            self._client.ping()
            logger.info("cache Redis conectado")
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache Redis deshabilitado: %s", exc)
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def get_json(self, key: str):
        if self._client is None:
            return None
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception:  # noqa: BLE001
            return None

    def set_json(self, key: str, value, ttl: int = 86400) -> None:
        if self._client is None:
            return
        try:
            self._client.set(key, json.dumps(value), ex=ttl)
        except Exception:  # noqa: BLE001
            pass

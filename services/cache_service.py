import time
from typing import Any, Optional
import pickle
import hashlib

class CacheService:
    def __init__(self):
        self.cache = {}
        self.ttl_map = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Check if expired
            if key in self.ttl_map:
                if time.time() > self.ttl_map[key]:
                    # Expired, remove from cache
                    del self.cache[key]
                    del self.ttl_map[key]
                    return None

            return self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        self.cache[key] = value
        if ttl > 0:
            self.ttl_map[key] = time.time() + ttl

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl_map:
            del self.ttl_map[key]

    def clear(self):
        self.cache.clear()
        self.ttl_map.clear()

    def exists(self, key: str) -> bool:
        if key in self.cache:
            # Check if expired
            if key in self.ttl_map:
                if time.time() > self.ttl_map[key]:
                    # Expired
                    del self.cache[key]
                    del self.ttl_map[key]
                    return False
            return True
        return False

    def get_or_set(self, key: str, callback, ttl: int = 300) -> Any:
        value = self.get(key)
        if value is None:
            value = callback()
            self.set(key, value, ttl)
        return value

    def cleanup_expired(self):
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.ttl_map.items()
            if current_time > expiry
        ]

        for key in expired_keys:
            self.delete(key)

    def get_stats(self) -> dict:
        return {
            'total_keys': len(self.cache),
            'expired_keys': len([k for k, v in self.ttl_map.items() if time.time() > v]),
            'cache_size_bytes': sum(len(pickle.dumps(v)) for v in self.cache.values())
        }

    @staticmethod
    def generate_key(*args) -> str:
        key_str = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
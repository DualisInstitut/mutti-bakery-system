# src/cache.py
from datetime import datetime, timedelta

class ScalingCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, recipe_id: str, target_servings: int):
        key = f"{recipe_id}:{target_servings}"
        entry = self.cache.get(key)
        if entry and datetime.now() < entry["expires"]:
            return entry["result"]
        return None

    def set(self, recipe_id: str, target_servings: int, result):
        key = f"{recipe_id}:{target_servings}"
        self.cache[key] = {
            "result": result,
            "expires": datetime.now() + timedelta(seconds=self.ttl)
        }

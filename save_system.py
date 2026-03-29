"""
save_system.py — JSON-based save/load with auto-save support.
"""

import json
import os
import time

SAVE_FILE = "worky_save.json"
AUTO_SAVE_INTERVAL = 10.0  # seconds


class SaveSystem:
    def __init__(self):
        self.last_save_time = time.time()

    def should_auto_save(self) -> bool:
        return (time.time() - self.last_save_time) >= AUTO_SAVE_INTERVAL

    def save(self, player, economy, restaurant=None):
        data = {
            "player": player.to_dict(),
            "economy": economy.to_dict(),
            "timestamp": time.time(),
        }
        if restaurant is not None:
            data["restaurant"] = restaurant.to_dict()
        tmp = SAVE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # Atomic rename to prevent corruption on crash
        if os.path.exists(SAVE_FILE):
            os.replace(tmp, SAVE_FILE)
        else:
            os.rename(tmp, SAVE_FILE)
        self.last_save_time = time.time()

    def load(self, player, economy, worker_factory, restaurant=None):
        if not os.path.exists(SAVE_FILE):
            return False
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        player.from_dict(data.get("player", {}), worker_factory)
        economy.from_dict(data.get("economy", {}))
        if restaurant is not None and "restaurant" in data:
            restaurant.from_dict(data["restaurant"])
        self.last_save_time = time.time()
        return True

    @staticmethod
    def has_save() -> bool:
        return os.path.exists(SAVE_FILE)

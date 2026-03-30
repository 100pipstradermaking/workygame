"""
save_system.py — JSON-based save/load with auto-save support.
Supports both file system (desktop) and browser localStorage (web/pygbag).
"""

import json
import os
import time
from online import is_web, web_save, web_load

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

        if is_web():
            web_save("save", data)
        else:
            tmp = SAVE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if os.path.exists(SAVE_FILE):
                os.replace(tmp, SAVE_FILE)
            else:
                os.rename(tmp, SAVE_FILE)
        self.last_save_time = time.time()

    def load(self, player, economy, worker_factory, restaurant=None):
        data = None
        if is_web():
            data = web_load("save")
        else:
            if not os.path.exists(SAVE_FILE):
                return False
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

        if not data:
            return False
        player.from_dict(data.get("player", {}), worker_factory)
        economy.from_dict(data.get("economy", {}))
        if restaurant is not None and "restaurant" in data:
            restaurant.from_dict(data["restaurant"])
        self.last_save_time = time.time()
        return True

    @staticmethod
    def has_save() -> bool:
        if is_web():
            return web_load("save") is not None
        return os.path.exists(SAVE_FILE)

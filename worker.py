"""
worker.py — Worker entity and hiring logic.
Each worker produces income based on speed, efficiency, level, and rarity.
"""

import random
from sprites import pick_archetype, pick_skin_tone


# Rarity tiers: name -> (probability weight, base_speed, base_efficiency, color)
RARITIES = {
    "common":    {"weight": 70, "speed": 2.0, "efficiency": 1.0, "color": (180, 180, 180)},
    "uncommon":  {"weight": 20, "speed": 2.6, "efficiency": 1.2, "color": (100, 200, 100)},
    "rare":      {"weight": 7,  "speed": 3.2, "efficiency": 1.5, "color": (80, 140, 240)},
    "epic":      {"weight": 2.5, "speed": 4.0, "efficiency": 2.0, "color": (180, 80, 240)},
    "legendary": {"weight": 0.5, "speed": 6.0, "efficiency": 3.0, "color": (255, 200, 50)},
}

BASE_HIRE_COST = 8.0
HIRE_COST_EXPONENT = 1.12


class Worker:
    def __init__(self, rarity: str = "common", level: int = 1,
                 archetype: str = None, skin_tone: tuple = None):
        info = RARITIES[rarity]
        self.rarity = rarity
        self.level = level
        self.base_speed = info["speed"]
        self.base_efficiency = info["efficiency"]
        self.color = info["color"]
        # WORKY character identity
        self.archetype = archetype or pick_archetype(rarity)
        self.skin_tone = skin_tone or pick_skin_tone()

    # ── Stats ─────────────────────────────────────────────────
    @property
    def speed(self) -> float:
        """Power scaling: base × (1 + level × 0.1)"""
        return self.base_speed * (1 + self.level * 0.1)

    @property
    def efficiency(self) -> float:
        return self.base_efficiency * (1 + self.level * 0.1)

    def get_income(self) -> float:
        """income = speed × efficiency"""
        return self.speed * self.efficiency

    # ── Upgrade ───────────────────────────────────────────────
    def upgrade_cost(self) -> float:
        """cost = base × (1.15 ^ level)"""
        return BASE_HIRE_COST * (HIRE_COST_EXPONENT ** self.level)

    def upgrade(self):
        self.level += 1

    # ── Serialization ─────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "rarity": self.rarity,
            "level": self.level,
            "archetype": self.archetype,
            "skin_tone": list(self.skin_tone),
        }

    @staticmethod
    def from_dict(data: dict) -> "Worker":
        skin = tuple(data["skin_tone"]) if "skin_tone" in data else None
        return Worker(
            rarity=data["rarity"],
            level=data.get("level", 1),
            archetype=data.get("archetype"),
            skin_tone=skin,
        )


def roll_rarity() -> str:
    """Weighted random rarity selection."""
    names = list(RARITIES.keys())
    weights = [RARITIES[n]["weight"] for n in names]
    return random.choices(names, weights=weights, k=1)[0]


def hire_cost(current_worker_count: int) -> float:
    """Each new hire costs more: base × 1.15^count."""
    return BASE_HIRE_COST * (HIRE_COST_EXPONENT ** current_worker_count)

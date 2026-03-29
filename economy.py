"""
economy.py — Production engine, super-burger events, and economy tick.
Handles per-frame income calculation, random bonus events,
and dine-in vs takeout sales split.
"""

import random
from player import Player

# Super-burger event tiers
SUPER_BURGER_EVENTS = [
    {"name": "Rare Burger",      "chance": 0.08,  "multiplier": 5,   "duration": 12.0,
     "color": (80, 140, 240)},
    {"name": "Epic Burger",      "chance": 0.04,  "multiplier": 20,  "duration": 10.0,
     "color": (180, 80, 240)},
    {"name": "Legendary Burger", "chance": 0.01,  "multiplier": 100, "duration": 7.0,
     "color": (255, 200, 50)},
]

# Dine-in vs Takeout base split (before upgrades)
BASE_DINEIN_RATIO = 0.3        # 30% dine-in by default
DINEIN_MULTIPLIER = 1.5        # dine-in pays 1.5x
TAKEOUT_MULTIPLIER = 0.8       # takeout pays 0.8x


class Economy:
    """Drives the production loop every tick."""

    def __init__(self):
        self.event_check_interval = 5.0   # seconds between event rolls
        self.event_timer = 0.0
        self.last_event_name: str | None = None
        self.last_event_color: tuple = (255, 255, 255)
        self.event_display_timer: float = 0.0

        # Dine-in / Takeout tracking
        self.dinein_income: float = 0.0     # total earned from dine-in
        self.takeout_income: float = 0.0    # total earned from takeout
        self.dinein_orders: int = 0
        self.takeout_orders: int = 0
        self.order_timer: float = 0.0       # ticks order counter

    # ── Main tick ─────────────────────────────────────────────
    def update(self, player: Player, dt: float, seats: int = 3):
        """Called every frame. dt = seconds since last frame.
        seats = number of dine-in seats (from upgrades).
        """
        # 1. Calculate dine-in ratio (more seats = higher dine-in %)
        dinein_ratio = min(0.80, BASE_DINEIN_RATIO + seats * 0.04)

        # 2. Earn income with dine-in / takeout split
        base_income = player.get_income_per_second() * dt
        if base_income > 0:
            dinein_part = base_income * dinein_ratio * DINEIN_MULTIPLIER
            takeout_part = base_income * (1 - dinein_ratio) * TAKEOUT_MULTIPLIER
            total = dinein_part + takeout_part
            player.earn(total)
            self.dinein_income += dinein_part
            self.takeout_income += takeout_part

            # Count orders (roughly 1 order per coin earned)
            self.order_timer += total
            while self.order_timer >= 1.0:
                self.order_timer -= 1.0
                if random.random() < dinein_ratio:
                    self.dinein_orders += 1
                else:
                    self.takeout_orders += 1

        # 3. Tick active bonus countdown
        player.update_bonus(dt)

        # 4. Roll for super-burger events periodically
        self.event_timer += dt
        if self.event_timer >= self.event_check_interval:
            self.event_timer = 0.0
            self._roll_event(player)

        # 5. Event display countdown
        if self.event_display_timer > 0:
            self.event_display_timer -= dt

    # ── Event roll ────────────────────────────────────────────
    def _roll_event(self, player: Player):
        if not player.workers:
            return
        roll = random.random()
        cumulative = 0.0
        for evt in SUPER_BURGER_EVENTS:
            cumulative += evt["chance"]
            if roll < cumulative:
                player.apply_bonus(evt["multiplier"], evt["duration"])
                self.last_event_name = evt["name"]
                self.last_event_color = evt["color"]
                self.event_display_timer = evt["duration"]
                return

    # ── Serialization ─────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "event_timer": self.event_timer,
            "dinein_income": self.dinein_income,
            "takeout_income": self.takeout_income,
            "dinein_orders": self.dinein_orders,
            "takeout_orders": self.takeout_orders,
        }

    def from_dict(self, data: dict):
        self.event_timer = data.get("event_timer", 0.0)
        self.dinein_income = data.get("dinein_income", 0.0)
        self.takeout_income = data.get("takeout_income", 0.0)
        self.dinein_orders = data.get("dinein_orders", 0)
        self.takeout_orders = data.get("takeout_orders", 0)

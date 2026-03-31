"""
economy.py — Production engine, super-burger events, and economy tick.
Handles per-frame income calculation, random bonus events,
and dine-in vs takeout sales split.
"""

import random
import time
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

# Sabotage attack definitions
SABOTAGE_DEFS = {
    "grill_jam":      {"name": "Grill Jam",      "cooldown": 300,  "cost": 100,
                       "damage": 50,  "effect_duration": 30,  "income_penalty": 0.50},
    "power_outage":   {"name": "Power Outage",   "cooldown": 600,  "cost": 200,
                       "damage": 100, "effect_duration": 60,  "income_penalty": 0.40},
    "food_poisoning": {"name": "Food Poisoning", "cooldown": 900,  "cost": 300,
                       "damage": 150, "effect_duration": 90,  "income_penalty": 0.30},
    "network_hack":   {"name": "Network Hack",   "cooldown": 1200, "cost": 500,
                       "damage": 200, "effect_duration": 120, "income_penalty": 0.20},
}

# Guild definitions
GUILDS = [
    {"id": "grill_masters",  "name": "GRILL MASTERS",   "motto": "Fire & Flavor",
     "color": (239, 68, 68),  "bonus_income": 0.05, "bonus_xp": 0.10},
    {"id": "fry_nation",     "name": "FRY NATION",      "motto": "Golden & Crispy",
     "color": (245, 158, 11), "bonus_income": 0.04, "bonus_xp": 0.12},
    {"id": "burger_lords",   "name": "BURGER LORDS",    "motto": "Stack It High",
     "color": (139, 92, 246), "bonus_income": 0.06, "bonus_xp": 0.08},
    {"id": "chef_collective","name": "CHEF COLLECTIVE",  "motto": "Craft & Create",
     "color": (34, 197, 94),  "bonus_income": 0.03, "bonus_xp": 0.15},
    {"id": "flip_squad",     "name": "FLIP SQUAD",      "motto": "Speed & Style",
     "color": (59, 130, 246), "bonus_income": 0.07, "bonus_xp": 0.06},
]
GUILDS_BY_ID = {g["id"]: g for g in GUILDS}

# Season config
SEASON_NUMBER = 1
SEASON_NAME = "Grand Opening"
SEASON_DURATION_DAYS = 30
SEASON_START = time.time()  # reset each server restart (single-player)

SEASON_REWARDS = [
    {"tier": "Bronze",  "pts": 100,   "reward_coins": 50,    "reward_worker": None,
     "color": (205, 127, 50),  "icon": "medal_bronze"},
    {"tier": "Silver",  "pts": 500,   "reward_coins": 200,   "reward_worker": "uncommon",
     "color": (192, 192, 192), "icon": "medal_silver"},
    {"tier": "Gold",    "pts": 2000,  "reward_coins": 500,   "reward_worker": "rare",
     "color": (255, 215, 0),   "icon": "medal_gold"},
    {"tier": "Master",  "pts": 10000, "reward_coins": 2000,  "reward_worker": "epic",
     "color": (180, 80, 240),  "icon": "star"},
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
        self._season_acc: float = 0.0       # accumulator for season points

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

        # 6. Tick sabotage cooldowns
        expired = []
        for atk_id, remaining in player.sabotage_cooldowns.items():
            player.sabotage_cooldowns[atk_id] = remaining - dt
            if player.sabotage_cooldowns[atk_id] <= 0:
                expired.append(atk_id)
        for atk_id in expired:
            del player.sabotage_cooldowns[atk_id]

        # 7. Tick incoming sabotage debuff
        if player.incoming_sabotage:
            player.incoming_sabotage["timer"] -= dt
            if player.incoming_sabotage["timer"] <= 0:
                player.incoming_sabotage = None

        # 8. Earn season points (accumulate, 1 pt per 10 coins)
        self._season_acc += base_income
        if self._season_acc >= 10:
            pts = int(self._season_acc / 10)
            player.season_points += pts
            self._season_acc -= pts * 10

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


# ═══════════════════════════════════════════════════════════════
#  Sabotage helpers (single-player simulation)
# ═══════════════════════════════════════════════════════════════
def execute_sabotage(player: Player, attack_id: str) -> dict:
    """Player launches a sabotage attack against a simulated rival.
    Returns {"ok": bool, "msg": str, "damage": int}.
    """
    defn = SABOTAGE_DEFS.get(attack_id)
    if not defn:
        return {"ok": False, "msg": "Unknown attack", "damage": 0}
    if attack_id in player.sabotage_cooldowns:
        return {"ok": False, "msg": "On cooldown!", "damage": 0}
    if player.coins < defn["cost"]:
        return {"ok": False, "msg": "Not enough coins!", "damage": 0}

    player.coins -= defn["cost"]
    player.sabotage_cooldowns[attack_id] = defn["cooldown"]
    player.sabotage_attacks_sent += 1

    # Simulated rival defense (random 0-40% block chance)
    rival_block = random.random() < 0.2
    if rival_block:
        return {"ok": True, "msg": "Attack blocked by rival!", "damage": 0}

    damage = defn["damage"]
    # Season points bonus for sabotage
    player.season_points += damage // 10
    return {"ok": True, "msg": f"{defn['name']} dealt {damage} DMG!", "damage": damage}


def get_sabotage_income_mult(player: Player) -> float:
    """Returns income multiplier considering active incoming sabotage debuff."""
    if player.incoming_sabotage and player.incoming_sabotage["timer"] > 0:
        from upgrades import get_sabotage_income_protection
        protection = get_sabotage_income_protection(player)
        penalty = player.incoming_sabotage["effect"]
        return max(0.1, 1.0 - (1.0 - penalty) * protection)
    return 1.0


# ═══════════════════════════════════════════════════════════════
#  Guild helpers
# ═══════════════════════════════════════════════════════════════
def join_guild(player: Player, guild_id: str) -> bool:
    """Join a guild. Returns True if joined successfully."""
    if guild_id not in GUILDS_BY_ID:
        return False
    if player.guild_id:
        return False  # already in a guild
    player.guild_id = guild_id
    player.guild_role = "member"
    player.guild_contribution = 0.0
    return True


def leave_guild(player: Player) -> bool:
    if not player.guild_id:
        return False
    player.guild_id = ""
    player.guild_role = "member"
    player.guild_contribution = 0.0
    return True


def contribute_to_guild(player: Player, amount: float) -> bool:
    """Donate coins to guild. Earns season points."""
    if not player.guild_id or amount <= 0:
        return False
    if player.coins < amount:
        return False
    player.coins -= amount
    player.guild_contribution += amount
    player.season_points += max(1, int(amount / 5))
    return True


def get_guild_income_bonus(player: Player) -> float:
    """Returns guild income multiplier (1.0 = no bonus)."""
    if not player.guild_id:
        return 1.0
    guild = GUILDS_BY_ID.get(player.guild_id)
    if not guild:
        return 1.0
    return 1.0 + guild["bonus_income"]


def get_guild_xp_bonus(player: Player) -> float:
    """Returns guild season point multiplier."""
    if not player.guild_id:
        return 1.0
    guild = GUILDS_BY_ID.get(player.guild_id)
    if not guild:
        return 1.0
    return 1.0 + guild["bonus_xp"]


# ═══════════════════════════════════════════════════════════════
#  Season helpers
# ═══════════════════════════════════════════════════════════════
def get_season_progress(player: Player) -> float:
    """Season progress 0.0 - 1.0 based on master tier."""
    if not SEASON_REWARDS:
        return 0.0
    max_pts = SEASON_REWARDS[-1]["pts"]
    return min(1.0, player.season_points / max_pts)


def get_season_time_remaining() -> tuple[int, int]:
    """Returns (days, hours) remaining in current season."""
    elapsed = time.time() - SEASON_START
    remaining = max(0, SEASON_DURATION_DAYS * 86400 - elapsed)
    days = int(remaining // 86400)
    hours = int((remaining % 86400) // 3600)
    return days, hours


def claim_season_reward(player: Player, tier: str) -> dict | None:
    """Claim a season reward tier. Returns reward dict or None."""
    if tier in player.season_rewards_claimed:
        return None
    for r in SEASON_REWARDS:
        if r["tier"] == tier and player.season_points >= r["pts"]:
            player.season_rewards_claimed.append(tier)
            player.coins += r["reward_coins"]
            result = {"tier": tier, "coins": r["reward_coins"], "worker": None}
            if r["reward_worker"]:
                from worker import Worker
                w = Worker(rarity=r["reward_worker"])
                player.workers.append(w)
                result["worker"] = r["reward_worker"]
            return result
    return None

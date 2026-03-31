"""
player.py — Player state management.
Tracks coins, total income, prestige, and owned workers/upgrades.
Designed for future integration with token economy and leaderboards.
"""

import math


class Player:
    def __init__(self):
        self.player_name: str = ""
        self.restaurant_name: str = ""
        self.coins: float = 0.0
        self.total_income: float = 0.0          # lifetime income (never resets except via prestige tracking)
        self.prestige_level: int = 0
        self.prestige_multiplier: float = 1.0
        self.workers: list = []                  # list of Worker instances
        self.upgrades_purchased: dict = {}       # {upgrade_id: level}

        # Super-burger active bonus
        self.active_bonus_multiplier: float = 1.0
        self.active_bonus_timer: float = 0.0     # seconds remaining

        # ── Sabotage state ────────────────────────────────────
        self.sabotage_cooldowns: dict = {}        # {attack_id: seconds_remaining}
        self.sabotage_attacks_sent: int = 0
        self.sabotage_defense_level: int = 0
        self.incoming_sabotage: dict | None = None # active debuff {"id", "timer", "effect"}

        # ── Guild state ───────────────────────────────────────
        self.guild_id: str = ""                    # guild name (empty = no guild)
        self.guild_role: str = "member"            # member / officer / leader
        self.guild_contribution: float = 0.0       # coins contributed to guild

        # ── Season state ──────────────────────────────────────
        self.season_points: int = 0
        self.season_rewards_claimed: list = []     # list of tier strings already claimed

    # ── Income ────────────────────────────────────────────────
    def get_income_per_second(self) -> float:
        """Sum income from all workers, apply prestige + active bonuses."""
        base = sum(w.get_income() for w in self.workers)
        return base * self.prestige_multiplier * self.active_bonus_multiplier

    def earn(self, amount: float):
        self.coins += amount
        self.total_income += amount

    def spend(self, amount: float) -> bool:
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False

    # ── Prestige ──────────────────────────────────────────────
    def get_prestige_bonus(self) -> float:
        """bonus = sqrt(total_income / 1,000,000)"""
        return math.sqrt(self.total_income / 1_000_000)

    def prestige(self):
        """Reset progress but keep prestige multiplier and one starter worker."""
        bonus = self.get_prestige_bonus()
        if bonus < 0.01:
            return False  # not enough income to prestige

        self.prestige_level += 1
        self.prestige_multiplier += bonus
        self.coins = 0.0
        self.total_income = 0.0
        self.workers.clear()
        self.upgrades_purchased.clear()
        self.active_bonus_multiplier = 1.0
        self.active_bonus_timer = 0.0
        # Keep one starter worker so income doesn't stop
        from worker import Worker
        self.workers.append(Worker(rarity="common"))
        return True

    # ── Super-burger bonus ────────────────────────────────────
    def apply_bonus(self, multiplier: float, duration: float):
        self.active_bonus_multiplier = multiplier
        self.active_bonus_timer = duration

    def update_bonus(self, dt: float):
        if self.active_bonus_timer > 0:
            self.active_bonus_timer -= dt
            if self.active_bonus_timer <= 0:
                self.active_bonus_timer = 0
                self.active_bonus_multiplier = 1.0

    # ── Serialization ─────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "player_name": self.player_name,
            "restaurant_name": self.restaurant_name,
            "coins": self.coins,
            "total_income": self.total_income,
            "prestige_level": self.prestige_level,
            "prestige_multiplier": self.prestige_multiplier,
            "workers": [w.to_dict() for w in self.workers],
            "upgrades_purchased": self.upgrades_purchased,
            "active_bonus_multiplier": self.active_bonus_multiplier,
            "active_bonus_timer": self.active_bonus_timer,
            "sabotage_cooldowns": self.sabotage_cooldowns,
            "sabotage_attacks_sent": self.sabotage_attacks_sent,
            "sabotage_defense_level": self.sabotage_defense_level,
            "guild_id": self.guild_id,
            "guild_role": self.guild_role,
            "guild_contribution": self.guild_contribution,
            "season_points": self.season_points,
            "season_rewards_claimed": self.season_rewards_claimed,
        }

    def from_dict(self, data: dict, worker_factory):
        """Restore player from saved dict.  worker_factory(d)->Worker."""
        self.player_name = data.get("player_name", "")
        self.restaurant_name = data.get("restaurant_name", "")
        self.coins = data.get("coins", 0.0)
        self.total_income = data.get("total_income", 0.0)
        self.prestige_level = data.get("prestige_level", 0)
        self.prestige_multiplier = data.get("prestige_multiplier", 1.0)
        self.upgrades_purchased = data.get("upgrades_purchased", {})
        self.active_bonus_multiplier = data.get("active_bonus_multiplier", 1.0)
        self.active_bonus_timer = data.get("active_bonus_timer", 0.0)
        self.sabotage_cooldowns = data.get("sabotage_cooldowns", {})
        self.sabotage_attacks_sent = data.get("sabotage_attacks_sent", 0)
        self.sabotage_defense_level = data.get("sabotage_defense_level", 0)
        self.guild_id = data.get("guild_id", "")
        self.guild_role = data.get("guild_role", "member")
        self.guild_contribution = data.get("guild_contribution", 0.0)
        self.season_points = data.get("season_points", 0)
        self.season_rewards_claimed = data.get("season_rewards_claimed", [])
        self.workers = [worker_factory(w) for w in data.get("workers", [])]

"""
upgrades.py — Upgrade definitions and purchasing logic.
Three categories: Production, Sales, Automation.
cost = base × (1.2 ^ level)
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

COST_EXPONENT = 1.2

# Each upgrade: id, name, category, base_cost, description, effect per level
UPGRADE_DEFS: list[dict] = [
    # ── Production ────────────────────────────────────────────
    {
        "id": "prod_speed",
        "name": "Faster Grills",
        "category": "Production",
        "base_cost": 30,
        "desc": "+15% worker speed per level",
        "max_level": 50,
    },
    {
        "id": "prod_efficiency",
        "name": "Better Ingredients",
        "category": "Production",
        "base_cost": 45,
        "desc": "+15% worker efficiency per level",
        "max_level": 50,
    },
    # ── Sales ─────────────────────────────────────────────────
    {
        "id": "sales_multiplier",
        "name": "Marketing Campaign",
        "category": "Sales",
        "base_cost": 120,
        "desc": "+20% income multiplier per level",
        "max_level": 30,
    },
    {
        "id": "sales_event_chance",
        "name": "Lucky Seasoning",
        "category": "Sales",
        "base_cost": 300,
        "desc": "Events checked more often (-0.3s interval/lvl)",
        "max_level": 10,
    },
    # ── Automation ────────────────────────────────────────────
    {
        "id": "auto_hire",
        "name": "Recruitment Agency",
        "category": "Automation",
        "base_cost": 600,
        "desc": "-5% hire cost per level",
        "max_level": 20,
    },
    {
        "id": "auto_upgrade",
        "name": "Training Program",
        "category": "Automation",
        "base_cost": 500,
        "desc": "-5% worker upgrade cost per level",
        "max_level": 20,
    },
    # ── Defense ───────────────────────────────────────────────
    {
        "id": "def_firewall",
        "name": "Firewall",
        "category": "Defense",
        "base_cost": 200,
        "desc": "-10% sabotage damage per level",
        "max_level": 10,
    },
    {
        "id": "def_security",
        "name": "Security System",
        "category": "Defense",
        "base_cost": 350,
        "desc": "+10% chance to block attacks/lvl",
        "max_level": 10,
    },
    {
        "id": "def_insurance",
        "name": "Insurance",
        "category": "Defense",
        "base_cost": 500,
        "desc": "-15% income loss from sabotage/lvl",
        "max_level": 8,
    },
]

# Build a quick lookup
UPGRADES_BY_ID = {u["id"]: u for u in UPGRADE_DEFS}


def get_upgrade_level(player: "Player", upgrade_id: str) -> int:
    return player.upgrades_purchased.get(upgrade_id, 0)


def upgrade_cost(upgrade_id: str, current_level: int) -> float:
    base = UPGRADES_BY_ID[upgrade_id]["base_cost"]
    return base * (COST_EXPONENT ** current_level)


def can_buy(player: "Player", upgrade_id: str) -> bool:
    defn = UPGRADES_BY_ID[upgrade_id]
    lvl = get_upgrade_level(player, upgrade_id)
    if lvl >= defn["max_level"]:
        return False
    return player.coins >= upgrade_cost(upgrade_id, lvl)


def buy_upgrade(player: "Player", upgrade_id: str) -> bool:
    """Purchase one level of an upgrade. Returns True on success."""
    defn = UPGRADES_BY_ID[upgrade_id]
    lvl = get_upgrade_level(player, upgrade_id)
    if lvl >= defn["max_level"]:
        return False
    cost = upgrade_cost(upgrade_id, lvl)
    if not player.spend(cost):
        return False
    player.upgrades_purchased[upgrade_id] = lvl + 1
    return True


# ── Apply upgrade effects to gameplay values ─────────────────
def get_speed_multiplier(player: "Player") -> float:
    lvl = get_upgrade_level(player, "prod_speed")
    return 1.0 + lvl * 0.15

def get_efficiency_multiplier(player: "Player") -> float:
    lvl = get_upgrade_level(player, "prod_efficiency")
    return 1.0 + lvl * 0.15

def get_income_multiplier(player: "Player") -> float:
    lvl = get_upgrade_level(player, "sales_multiplier")
    return 1.0 + lvl * 0.20

def get_event_interval_reduction(player: "Player") -> float:
    lvl = get_upgrade_level(player, "sales_event_chance")
    return lvl * 0.3

def get_hire_cost_discount(player: "Player") -> float:
    lvl = get_upgrade_level(player, "auto_hire")
    return 1.0 - lvl * 0.05

def get_worker_upgrade_discount(player: "Player") -> float:
    lvl = get_upgrade_level(player, "auto_upgrade")
    return 1.0 - lvl * 0.05

# ── Defense upgrade effects ──────────────────────────────────
def get_sabotage_damage_reduction(player: "Player") -> float:
    """Returns multiplier on incoming sabotage damage (lower = better)."""
    lvl = get_upgrade_level(player, "def_firewall")
    return max(0.1, 1.0 - lvl * 0.10)

def get_sabotage_block_chance(player: "Player") -> float:
    """Probability of completely blocking incoming sabotage."""
    lvl = get_upgrade_level(player, "def_security")
    return min(0.90, lvl * 0.10)

def get_sabotage_income_protection(player: "Player") -> float:
    """Returns multiplier on income loss from active sabotage (lower = better)."""
    lvl = get_upgrade_level(player, "def_insurance")
    return max(0.1, 1.0 - lvl * 0.15)

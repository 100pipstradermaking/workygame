"""
shop.py — In-game shop / upgrade store.
Four shop categories with scrollable panels and vibrant pixel UI:
  1. STAFF   — Hire workers, worker upgrades
  2. KITCHEN — Production & equipment upgrades
  3. DESIGN  — Seating, decor, restaurant look (dine-in boost)
  4. BUSINESS — Sales, automation, expansion

Dine-in seats affect the economy: more seats → more dine-in orders → more money.
"""

import pygame
import math
from player import Player
from worker import Worker, hire_cost, roll_rarity, RARITIES
from upgrades import (
    UPGRADE_DEFS, UPGRADES_BY_ID, get_upgrade_level,
    upgrade_cost, can_buy, buy_upgrade,
    get_hire_cost_discount, get_worker_upgrade_discount,
)
from theme import (BG, BG_PANEL as PANEL_BG, BG_CARD as CARD_BG,
                   BG_CARD_H as CARD_HOVER,
                   TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, TEXT_GREEN, TEXT_RED,
                   TEXT_CYAN, TEXT_PINK,
                   BTN_BUY, BTN_BUY_H, BTN_DISABLED, BTN_DIS_TXT,
                   BORDER, ACCENT, ACCENT_GLOW)
import icons

CARD_GLOW    = (70, 60, 90)

# Tab colors per category
TAB_COLORS = {
    "Staff":    ((200, 120, 40), (240, 150, 60)),
    "Kitchen":  ((180, 60, 60),  (220, 80, 80)),
    "Design":   ((60, 140, 200), (80, 170, 240)),
    "Business": ((120, 60, 180), (160, 90, 220)),
}
TAB_INACTIVE = (40, 38, 52)

# ── Shop item definitions ────────────────────────────────────
KITCHEN_ITEMS = [
    {
        "id": "kitchen_oven", "name": "Brick Oven",
        "base_cost": 300, "max_level": 10,
        "desc": "Cooking speed +10%/level",
        "category": "kitchen", "effect": "cook_speed",
        "icon_color": (255, 140, 50),
    },
    {
        "id": "kitchen_fridge", "name": "Walk-in Fridge",
        "base_cost": 250, "max_level": 15,
        "desc": "Efficiency +8%/level",
        "category": "kitchen", "effect": "efficiency",
        "icon_color": (100, 200, 255),
    },
    {
        "id": "kitchen_fryer", "name": "Deep Fryer",
        "base_cost": 400, "max_level": 10,
        "desc": "Income +12%/level (fries side)",
        "category": "kitchen", "effect": "income",
        "icon_color": (255, 200, 80),
    },
    {
        "id": "kitchen_prep", "name": "Prep Station",
        "base_cost": 180, "max_level": 20,
        "desc": "Assembly speed +10%/level",
        "category": "kitchen", "effect": "speed",
        "icon_color": (180, 220, 180),
    },
]

DESIGN_ITEMS = [
    {
        "id": "design_seats", "name": "Extra Seating",
        "base_cost": 200, "max_level": 12,
        "desc": "+2 seats/lvl → more dine-in (×1.5 income!)",
        "category": "design", "effect": "seats",
        "icon_color": (180, 130, 80),
    },
    {
        "id": "design_neon", "name": "Neon Signs",
        "base_cost": 350, "max_level": 8,
        "desc": "Attract +15% customers/level",
        "category": "design", "effect": "attract",
        "icon_color": (255, 80, 200),
    },
    {
        "id": "design_floor", "name": "Premium Flooring",
        "base_cost": 500, "max_level": 5,
        "desc": "Fancy floor, worker speed +5%/level",
        "category": "design", "effect": "floor_speed",
        "icon_color": (200, 180, 140),
    },
    {
        "id": "design_paint", "name": "Wall Art & Paint",
        "base_cost": 280, "max_level": 10,
        "desc": "+10% dine-in tip bonus/level",
        "category": "design", "effect": "tip_bonus",
        "icon_color": (130, 200, 255),
    },
    {
        "id": "design_music", "name": "Background Music",
        "base_cost": 400, "max_level": 6,
        "desc": "Happier workers, +8% efficiency/level",
        "category": "design", "effect": "music_eff",
        "icon_color": (200, 130, 255),
    },
    {
        "id": "design_ac", "name": "Air Conditioning",
        "base_cost": 600, "max_level": 5,
        "desc": "+12% worker speed in summer heat",
        "category": "design", "effect": "ac_speed",
        "icon_color": (120, 220, 255),
    },
]

BUSINESS_ITEMS = [
    {
        "id": "biz_ads", "name": "Billboard Ad",
        "base_cost": 500, "max_level": 15,
        "desc": "+20% customer flow/level",
        "category": "business", "effect": "income_mult",
        "icon_color": (255, 100, 100),
    },
    {
        "id": "biz_delivery", "name": "Delivery Service",
        "base_cost": 800, "max_level": 10,
        "desc": "+15% takeout income/level",
        "category": "business", "effect": "income_events",
        "icon_color": (100, 200, 100),
    },
    {
        "id": "biz_franchise", "name": "Franchise License",
        "base_cost": 5000, "max_level": 5,
        "desc": "×2 base income multiplier",
        "category": "business", "effect": "base_mult",
        "icon_color": (200, 180, 100),
    },
    {
        "id": "biz_vip", "name": "VIP Lounge",
        "base_cost": 2000, "max_level": 8,
        "desc": "+25% super-burger bonus/level",
        "category": "business", "effect": "event_boost",
        "icon_color": (255, 215, 0),
    },
]

ALL_SHOP_ITEMS = {item["id"]: item for item in KITCHEN_ITEMS + DESIGN_ITEMS + BUSINESS_ITEMS}

COST_EXPONENT = 1.2


def shop_item_cost(item_id: str, level: int) -> float:
    item = ALL_SHOP_ITEMS[item_id]
    return item["base_cost"] * (COST_EXPONENT ** level)


def shop_item_level(player: Player, item_id: str) -> int:
    return player.upgrades_purchased.get(item_id, 0)


def can_buy_shop_item(player: Player, item_id: str) -> bool:
    item = ALL_SHOP_ITEMS[item_id]
    lvl = shop_item_level(player, item_id)
    if lvl >= item["max_level"]:
        return False
    return player.coins >= shop_item_cost(item_id, lvl)


def buy_shop_item(player: Player, item_id: str) -> bool:
    item = ALL_SHOP_ITEMS[item_id]
    lvl = shop_item_level(player, item_id)
    if lvl >= item["max_level"]:
        return False
    cost = shop_item_cost(item_id, lvl)
    if not player.spend(cost):
        return False
    player.upgrades_purchased[item_id] = lvl + 1
    return True


# ── Shop effect getters (used by economy/main) ───────────────
def get_cook_speed_bonus(player: Player) -> float:
    return 1.0 + shop_item_level(player, "kitchen_oven") * 0.10

def get_fridge_efficiency(player: Player) -> float:
    return 1.0 + shop_item_level(player, "kitchen_fridge") * 0.08

def get_fryer_income(player: Player) -> float:
    return 1.0 + shop_item_level(player, "kitchen_fryer") * 0.12

def get_prep_speed(player: Player) -> float:
    return 1.0 + shop_item_level(player, "kitchen_prep") * 0.10

def get_ads_bonus(player: Player) -> float:
    return 1.0 + shop_item_level(player, "biz_ads") * 0.20

def get_delivery_bonus(player: Player) -> float:
    return 1.0 + shop_item_level(player, "biz_delivery") * 0.15

def get_franchise_mult(player: Player) -> float:
    return 1.0 + shop_item_level(player, "biz_franchise") * 1.0

def get_vip_event_boost(player: Player) -> float:
    return 1.0 + shop_item_level(player, "biz_vip") * 0.25

# Design getters
def get_seat_count(player: Player) -> int:
    """Base 3 seats + 2 per level of Extra Seating."""
    return 3 + shop_item_level(player, "design_seats") * 2

def get_neon_attract(player: Player) -> float:
    return 1.0 + shop_item_level(player, "design_neon") * 0.15

def get_floor_speed(player: Player) -> float:
    return 1.0 + shop_item_level(player, "design_floor") * 0.05

def get_paint_tip(player: Player) -> float:
    return 1.0 + shop_item_level(player, "design_paint") * 0.10

def get_music_efficiency(player: Player) -> float:
    return 1.0 + shop_item_level(player, "design_music") * 0.08

def get_ac_speed(player: Player) -> float:
    return 1.0 + shop_item_level(player, "design_ac") * 0.12

def get_total_shop_multiplier(player: Player) -> float:
    """Combined multiplier from all shop items."""
    return (get_cook_speed_bonus(player)
            * get_fridge_efficiency(player)
            * get_fryer_income(player)
            * get_prep_speed(player)
            * get_ads_bonus(player)
            * get_delivery_bonus(player)
            * get_franchise_mult(player)
            * get_neon_attract(player)
            * get_floor_speed(player)
            * get_paint_tip(player)
            * get_music_efficiency(player)
            * get_ac_speed(player))


def get_attractiveness(player: Player) -> int:
    """Attractiveness score 0-100 based on design upgrades.
    Each design item contributes proportionally to its max level."""
    score = 0.0
    weights = {
        "design_seats": 20,
        "design_neon":  18,
        "design_floor": 15,
        "design_paint": 18,
        "design_music": 14,
        "design_ac":    15,
    }
    for item_id, max_pts in weights.items():
        item = ALL_SHOP_ITEMS[item_id]
        lvl = shop_item_level(player, item_id)
        score += max_pts * (lvl / item["max_level"])
    return min(100, int(score))


# ── Shop UI ──────────────────────────────────────────────────

class ShopUI:
    """In-game shop panel — vibrant pixel UI with 4 tabs."""

    TABS = ["Staff", "Kitchen", "Design", "Business"]

    def __init__(self, panel_x: int, panel_w: int, panel_h: int):
        self.panel_x = panel_x
        self.panel_w = panel_w
        self.panel_h = panel_h
        self.active_tab = 0
        self.scroll_y = 0
        self.max_scroll = 0
        self.glow_t = 0.0  # animation timer

        # Fonts
        self.font_sm = pygame.font.SysFont("Consolas", 12)
        self.font_md = pygame.font.SysFont("Consolas", 14)
        self.font_lg = pygame.font.SysFont("Consolas", 18)
        self.font_title = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_coins = pygame.font.SysFont("Consolas", 20, bold=True)

        # Dynamic buttons rebuilt each frame
        self._buttons: list[tuple[pygame.Rect, str, str]] = []

        # Purchase animation state
        self._purchase_flash: float = 0.0       # screen flash timer
        self._purchase_particles: list[dict] = []  # coin burst particles
        self._tooltip_text: str = ""
        self._tooltip_pos: tuple = (0, 0)

    def update(self, dt: float):
        self.glow_t += dt
        # Update purchase flash
        if self._purchase_flash > 0:
            self._purchase_flash -= dt * 3
        # Update coin particles
        alive = []
        for p in self._purchase_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 80 * dt
            p["life"] -= dt
            if p["life"] > 0:
                alive.append(p)
        self._purchase_particles = alive

    def _spawn_purchase_effect(self, mx: int, my: int):
        """Spawn coin burst particles and flash on purchase."""
        self._purchase_flash = 1.0
        for _ in range(8):
            import random
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 100)
            self._purchase_particles.append({
                "x": mx, "y": my,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 40,
                "life": random.uniform(0.4, 0.8),
                "max_life": 0.8,
                "color": random.choice([
                    (255, 215, 70), (255, 200, 50), (255, 180, 40),
                    (80, 230, 120), (255, 255, 200),
                ]),
            })

    def handle_event(self, event: pygame.event.Event, player: Player) -> str | None:
        """Handle shop interactions. Returns action string or None."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Tab clicks
            tab_y = 42
            tab_w = self.panel_w // 4
            for i, tab_name in enumerate(self.TABS):
                tab_rect = pygame.Rect(self.panel_x + i * tab_w, tab_y, tab_w, 26)
                if tab_rect.collidepoint(mx, my):
                    self.active_tab = i
                    self.scroll_y = 0
                    return None

            # Button clicks
            for rect, action_type, action_id in self._buttons:
                if rect.collidepoint(mx, my):
                    if action_type == "hire":
                        cost = hire_cost(len(player.workers)) * get_hire_cost_discount(player)
                        if player.spend(cost):
                            rarity = roll_rarity()
                            player.workers.append(Worker(rarity=rarity))
                            self._spawn_purchase_effect(mx, my)
                            return "hired"
                    elif action_type == "worker_up":
                        idx = int(action_id)
                        if idx < len(player.workers):
                            w = player.workers[idx]
                            cost = w.upgrade_cost() * get_worker_upgrade_discount(player)
                            if player.spend(cost):
                                w.upgrade()
                                self._spawn_purchase_effect(mx, my)
                                return "worker_upgraded"
                    elif action_type == "upgrade":
                        if action_id in UPGRADES_BY_ID:
                            if buy_upgrade(player, action_id):
                                self._spawn_purchase_effect(mx, my)
                            return "upgraded"
                        elif action_id in ALL_SHOP_ITEMS:
                            if buy_shop_item(player, action_id):
                                self._spawn_purchase_effect(mx, my)
                            return "shop_bought"

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if mx >= self.panel_x:
                self.scroll_y = max(0, min(self.max_scroll,
                                           self.scroll_y - event.y * 30))

        return None

    def draw(self, surf: pygame.Surface, player: Player):
        self._buttons.clear()

        # Panel background with gradient effect
        panel_rect = pygame.Rect(self.panel_x, 0, self.panel_w, self.panel_h)
        pygame.draw.rect(surf, BG, panel_rect)

        # Subtle gradient overlay
        for i in range(0, self.panel_h, 4):
            alpha = int(5 + 3 * math.sin(i * 0.02 + self.glow_t))
            gs = pygame.Surface((self.panel_w, 4), pygame.SRCALPHA)
            gs.fill((100, 80, 160, max(0, min(255, alpha))))
            surf.blit(gs, (self.panel_x, i))

        # Left border with accent glow
        glow_alpha = int(40 + 20 * math.sin(self.glow_t * 2))
        for i in range(3):
            c = (*ACCENT[:3], max(0, glow_alpha - i * 15))
            gs = pygame.Surface((1, self.panel_h), pygame.SRCALPHA)
            gs.fill(c)
            surf.blit(gs, (self.panel_x + i, 0))

        # Header area
        header_bg = pygame.Surface((self.panel_w, 38), pygame.SRCALPHA)
        header_bg.fill((0, 0, 0, 60))
        surf.blit(header_bg, (self.panel_x, 0))

        # Title
        title = self.font_title.render("SHOP", True, TEXT_GOLD)
        surf.blit(title, (self.panel_x + 12, 8))

        # Coins with icon
        coins_str = f"{player.coins:,.0f}"
        coins_txt = self.font_coins.render(coins_str, True, TEXT_GOLD)
        coin_x = self.panel_x + self.panel_w - coins_txt.get_width() - 28
        surf.blit(icons.get("coin"), (coin_x - 8, 12))
        surf.blit(coins_txt, (coin_x + 10, 8))

        # Tabs
        self._draw_tabs(surf)

        # Content area (clipped)
        content_y = 72
        content_h = self.panel_h - content_y - 58
        content_rect = pygame.Rect(self.panel_x, content_y, self.panel_w, content_h)
        prev_clip = surf.get_clip()
        surf.set_clip(content_rect)

        if self.active_tab == 0:
            self._draw_staff_tab(surf, player, content_y)
        elif self.active_tab == 1:
            self._draw_items_tab(surf, player, content_y, "Production", KITCHEN_ITEMS)
        elif self.active_tab == 2:
            self._draw_design_tab(surf, player, content_y)
        elif self.active_tab == 3:
            self._draw_items_tab(surf, player, content_y, "Sales|Automation", BUSINESS_ITEMS)

        surf.set_clip(prev_clip)

        # Scroll indicator
        if self.max_scroll > 0:
            bar_x = self.panel_x + self.panel_w - 6
            bar_h = max(20, int(content_h * content_h / (content_h + self.max_scroll)))
            bar_y = content_y + int((content_h - bar_h) * self.scroll_y / self.max_scroll)
            sb = pygame.Surface((4, bar_h), pygame.SRCALPHA)
            sb.fill((120, 110, 160, 80))
            surf.blit(sb, (bar_x, bar_y))

        # Prestige button at bottom
        self._draw_prestige(surf, player)

        # Purchase flash overlay
        if self._purchase_flash > 0:
            flash_a = int(40 * self._purchase_flash)
            fs = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
            fs.fill((255, 255, 200, max(0, flash_a)))
            surf.blit(fs, (self.panel_x, 0))

        # Purchase coin particles
        for p in self._purchase_particles:
            alpha = max(0, min(255, int(255 * (p["life"] / p["max_life"]))))
            sz = 4
            ps = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"], alpha), (sz // 2, sz // 2), sz // 2)
            surf.blit(ps, (int(p["x"]) - sz // 2, int(p["y"]) - sz // 2))

    def _draw_tabs(self, surf):
        tab_y = 42
        tab_w = self.panel_w // 4
        for i, name in enumerate(self.TABS):
            rect = pygame.Rect(self.panel_x + i * tab_w, tab_y, tab_w, 26)
            if i == self.active_tab:
                color = TAB_COLORS[name][0]
                pygame.draw.rect(surf, TAB_COLORS[name][1],
                                 (rect.x, rect.bottom - 3, rect.width, 3))
            else:
                color = TAB_INACTIVE
                mx, my = pygame.mouse.get_pos()
                if rect.collidepoint(mx, my):
                    color = (55, 52, 68)
            pygame.draw.rect(surf, color, rect)
            # Tab icon + label
            ico = icons.get_scaled(icons.TAB_ICONS[name], 12)
            txt = self.font_sm.render(name, True, TEXT_WHITE if i == self.active_tab else TEXT_GRAY)
            total_w = 12 + 3 + txt.get_width()
            ix = rect.centerx - total_w // 2
            surf.blit(ico, (ix, rect.centery - 6))
            surf.blit(txt, (ix + 15, rect.centery - txt.get_height() // 2))

    # ── Staff tab ─────────────────────────────────────────────
    def _draw_staff_tab(self, surf, player, start_y):
        x = self.panel_x + 6
        y = start_y + 6 - self.scroll_y
        w = self.panel_w - 12

        # Hire card (special golden border)
        hire_c = hire_cost(len(player.workers)) * get_hire_cost_discount(player)
        affordable = player.coins >= hire_c
        y = self._draw_card(surf, x, y, w,
                            "Hire New Worker",
                            f"Cost: {hire_c:,.0f}c  |  Workers: {len(player.workers)}",
                            "Random rarity roll!",
                            f"HIRE ({hire_c:,.0f}c)",
                            affordable, "hire", "new",
                            icon_color=(255, 200, 80), special=True)
        y += 8

        # Separator with gradient
        sep_w = w - 20
        for sx in range(sep_w):
            alpha = int(60 * (1 - abs(sx / sep_w - 0.5) * 2))
            pygame.draw.rect(surf, (*TEXT_GRAY[:3], max(0, alpha)),
                             (x + 10 + sx, y, 1, 1))
        sep = self.font_sm.render(f"Workers: {len(player.workers)}", True, TEXT_CYAN)
        surf.blit(sep, sep.get_rect(center=(self.panel_x + self.panel_w // 2, y + 10)))
        y += 24

        # Worker list
        for i, wk in enumerate(player.workers):
            rarity_col = RARITIES[wk.rarity]["color"]
            up_cost = wk.upgrade_cost() * get_worker_upgrade_discount(player)
            can_up = player.coins >= up_cost

            name = f"Lv{wk.level} {wk.rarity.capitalize()} {wk.archetype.replace('_',' ').title()}"
            detail = f"{wk.get_income():.1f}/s  Spd:{wk.speed:.1f}  Eff:{wk.efficiency:.1f}"

            rect = pygame.Rect(x, y, w, 52)
            mx, my_m = pygame.mouse.get_pos()
            bg = CARD_HOVER if rect.collidepoint(mx, my_m) else CARD_BG
            pygame.draw.rect(surf, bg, rect, border_radius=4)
            # Rarity gradient left border
            pygame.draw.rect(surf, rarity_col, (x, y, 3, 52), border_radius=2)
            # Subtle rarity glow
            rg = pygame.Surface((20, 52), pygame.SRCALPHA)
            rg.fill((*rarity_col, 20))
            surf.blit(rg, (x, y))

            ntxt = self.font_md.render(name, True, rarity_col)
            surf.blit(ntxt, (x + 8, y + 4))
            dtxt = self.font_sm.render(detail, True, TEXT_GRAY)
            surf.blit(dtxt, (x + 8, y + 22))

            # Upgrade button
            btn_rect = pygame.Rect(x + w - 95, y + 26, 85, 20)
            self._draw_btn(surf, btn_rect, f"Up {up_cost:,.0f}c", can_up)
            if can_up:
                self._buttons.append((btn_rect, "worker_up", str(i)))

            y += 56

        self.max_scroll = max(0, y - (start_y + self.panel_h - 140))

    # ── Generic items tab (Kitchen / Business) ────────────────
    def _draw_items_tab(self, surf, player, start_y, upgrade_categories: str, items: list):
        x = self.panel_x + 6
        y = start_y + 6 - self.scroll_y
        w = self.panel_w - 12

        # Original upgrades from upgrades.py
        cats = upgrade_categories.split("|")
        for u in UPGRADE_DEFS:
            if u["category"] not in cats:
                continue
            lvl = get_upgrade_level(player, u["id"])
            maxed = lvl >= u["max_level"]
            cost = upgrade_cost(u["id"], lvl) if not maxed else 0
            affordable = can_buy(player, u["id"])

            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            y = self._draw_card(surf, x, y, w,
                                f'{u["name"]} (Lv {lvl}/{u["max_level"]})',
                                u["desc"],
                                f'{u["category"]}',
                                btn_label,
                                affordable and not maxed, "upgrade", u["id"])
            y += 3

        # Shop items
        for item in items:
            lvl = shop_item_level(player, item["id"])
            maxed = lvl >= item["max_level"]
            cost = shop_item_cost(item["id"], lvl) if not maxed else 0
            affordable = can_buy_shop_item(player, item["id"])

            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            y = self._draw_card(surf, x, y, w,
                                f'{item["name"]} (Lv {lvl}/{item["max_level"]})',
                                item["desc"],
                                f'Effect: {item["effect"]}',
                                btn_label,
                                affordable and not maxed, "upgrade", item["id"],
                                icon_color=item.get("icon_color"))
            y += 3

        self.max_scroll = max(0, y - (start_y + self.panel_h - 140))

    # ── Design tab ────────────────────────────────────────────
    def _draw_design_tab(self, surf, player, start_y):
        x = self.panel_x + 6
        y = start_y + 6 - self.scroll_y
        w = self.panel_w - 12

        # ── Attractiveness header ────────────────────────────
        attract = get_attractiveness(player)
        header_h = 60
        header_rect = pygame.Rect(x, y, w, header_h)

        # Gradient background based on score
        if attract >= 80:
            hdr_bg = (40, 42, 25)
            hdr_border = TEXT_GOLD
        elif attract >= 50:
            hdr_bg = (25, 42, 35)
            hdr_border = TEXT_GREEN
        else:
            hdr_bg = (30, 30, 45)
            hdr_border = TEXT_CYAN
        pygame.draw.rect(surf, hdr_bg, header_rect, border_radius=6)
        pygame.draw.rect(surf, hdr_border, header_rect, 2, border_radius=6)

        # Animated glow
        glow_a = int(15 + 10 * math.sin(self.glow_t * 2))
        gs = pygame.Surface((w, header_h), pygame.SRCALPHA)
        gs.fill((*hdr_border[:3], max(0, glow_a)))
        surf.blit(gs, (x, y))

        # Star rating (pixel icons)
        stars_full = attract // 20
        star_x = x + 8
        for si in range(5):
            s_ico = icons.get_scaled("star", 14)
            if si >= stars_full:
                s_ico = s_ico.copy()
                s_ico.set_alpha(60)
            surf.blit(s_ico, (star_x + si * 16, y + 6))

        # Percentage
        pct_txt = self.font_title.render(f"{attract}%", True, hdr_border)
        surf.blit(pct_txt, (x + w - pct_txt.get_width() - 10, y + 2))

        # Progress bar
        bar_x = x + 8
        bar_y_pos = y + 30
        bar_w = w - 16
        bar_h = 12
        pygame.draw.rect(surf, (20, 20, 30), (bar_x, bar_y_pos, bar_w, bar_h),
                         border_radius=6)
        fill_w = int(bar_w * attract / 100)
        if fill_w > 0:
            # Color gradient from red → yellow → green
            if attract < 33:
                fill_c = (200, 80, 60)
            elif attract < 66:
                fill_c = (220, 180, 50)
            else:
                fill_c = (80, 220, 100)
            pygame.draw.rect(surf, fill_c, (bar_x, bar_y_pos, fill_w, bar_h),
                             border_radius=6)
        # Bar shimmer
        shimmer_x = int((self.glow_t * 40) % (bar_w + 20)) - 10
        if 0 < shimmer_x < fill_w:
            sh = pygame.Surface((8, bar_h), pygame.SRCALPHA)
            sh.fill((255, 255, 255, 30))
            surf.blit(sh, (bar_x + shimmer_x, bar_y_pos))

        lbl = self.font_sm.render("ATTRACTIVENESS", True, TEXT_GRAY)
        surf.blit(lbl, lbl.get_rect(center=(x + w // 2, bar_y_pos + bar_h + 10)))

        y += header_h + 8

        # ── Seats summary ────────────────────────────────────
        seats = get_seat_count(player)
        seats_rect = pygame.Rect(x, y, w, 24)
        pygame.draw.rect(surf, (35, 50, 70), seats_rect, border_radius=4)
        s1_ico = icons.get_scaled("chair", 12)
        s1_txt = self.font_sm.render(f"Seats: {seats}", True, TEXT_CYAN)
        surf.blit(s1_ico, (x + 8, y + 6))
        surf.blit(s1_txt, (x + 24, y + 5))
        s2 = self.font_sm.render("More seats = dine-in x1.5", True, TEXT_GREEN)
        surf.blit(s2, (x + w - s2.get_width() - 8, y + 5))
        y += 30

        # ── Design upgrade cards with level bars ─────────────
        # Get current effect values for display
        effect_labels = {
            "design_seats": lambda: f"+{shop_item_level(player, 'design_seats') * 2} seats",
            "design_neon":  lambda: f"+{shop_item_level(player, 'design_neon') * 15}% attract",
            "design_floor": lambda: f"+{shop_item_level(player, 'design_floor') * 5}% speed",
            "design_paint": lambda: f"+{shop_item_level(player, 'design_paint') * 10}% tips",
            "design_music": lambda: f"+{shop_item_level(player, 'design_music') * 8}% efficiency",
            "design_ac":    lambda: f"+{shop_item_level(player, 'design_ac') * 12}% speed",
        }

        for item in DESIGN_ITEMS:
            iid = item["id"]
            lvl = shop_item_level(player, iid)
            maxed = lvl >= item["max_level"]
            cost = shop_item_cost(iid, lvl) if not maxed else 0
            affordable = can_buy_shop_item(player, iid)

            card_h = 82
            card_rect = pygame.Rect(x, y, w, card_h)
            mx, my = pygame.mouse.get_pos()
            hovered = card_rect.collidepoint(mx, my)
            bg = CARD_HOVER if hovered else CARD_BG
            pygame.draw.rect(surf, bg, card_rect, border_radius=5)

            ic = item.get("icon_color", BORDER)
            # Left accent bar (thicker for design)
            pygame.draw.rect(surf, ic, (x, y + 3, 4, card_h - 6), border_radius=2)

            # Subtle icon glow
            ig = pygame.Surface((24, card_h), pygame.SRCALPHA)
            ig.fill((*ic, 15))
            surf.blit(ig, (x, y))

            # Pixel icon
            icon_name = icons.ITEM_ICONS.get(iid)
            if icon_name:
                surf.blit(icons.get(icon_name), (x + 8, y + 4))

            # Name
            name_x = (x + 28) if icon_name else (x + 10)
            name_txt = self.font_md.render(item["name"], True, TEXT_WHITE)
            surf.blit(name_txt, (name_x, y + 4))

            # Level badge
            if maxed:
                lvl_col = TEXT_GOLD
                lvl_str = "MAX"
            else:
                lvl_col = TEXT_CYAN
                lvl_str = f"Lv {lvl}/{item['max_level']}"
            lvl_txt = self.font_sm.render(lvl_str, True, lvl_col)
            surf.blit(lvl_txt, (x + w - lvl_txt.get_width() - 8, y + 5))

            # Description
            desc_txt = self.font_sm.render(item["desc"], True, TEXT_GRAY)
            surf.blit(desc_txt, (x + 10, y + 22))

            # Current effect value
            eff_str = effect_labels[iid]()
            eff_txt = self.font_sm.render(f"Current: {eff_str}", True, TEXT_GREEN)
            surf.blit(eff_txt, (x + 10, y + 38))

            # Level progress bar
            pb_x = x + 10
            pb_y = y + 54
            pb_w = w - 130
            pb_h = 8
            pygame.draw.rect(surf, (25, 25, 35), (pb_x, pb_y, pb_w, pb_h),
                             border_radius=4)
            if lvl > 0:
                fill = int(pb_w * lvl / item["max_level"])
                pygame.draw.rect(surf, ic, (pb_x, pb_y, fill, pb_h),
                                 border_radius=4)
            # Pips for each level
            for pip_i in range(item["max_level"]):
                pip_x = pb_x + int(pb_w * (pip_i + 1) / item["max_level"])
                pip_c = (60, 60, 70) if pip_i >= lvl else (*ic[:3],)
                pygame.draw.rect(surf, pip_c, (pip_x - 1, pb_y, 1, pb_h))

            # Buy button
            btn_rect = pygame.Rect(x + w - 110, y + 48, 100, 24)
            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            self._draw_btn(surf, btn_rect, btn_label, affordable and not maxed)
            if affordable and not maxed:
                self._buttons.append((btn_rect, "upgrade", iid))

            # Hover border
            if hovered:
                pygame.draw.rect(surf, ic, card_rect, 1, border_radius=5)
            else:
                pygame.draw.rect(surf, BORDER, card_rect, 1, border_radius=5)

            y += card_h + 4

        self.max_scroll = max(0, y - (start_y + self.panel_h - 140))

    # ── Prestige section ──────────────────────────────────────
    def _draw_prestige(self, surf, player):
        y = self.panel_h - 52
        rect = pygame.Rect(self.panel_x + 6, y, self.panel_w - 12, 44)
        bonus = player.get_prestige_bonus()
        can_prestige = bonus >= 0.01

        if can_prestige:
            pulse = int(15 * math.sin(self.glow_t * 3))
            color = (180 + pulse, 100, 50)
            hover = (220 + pulse, 130, 60)
        else:
            color = BTN_DISABLED
            hover = BTN_DISABLED
        mx, my = pygame.mouse.get_pos()
        c = hover if rect.collidepoint(mx, my) and can_prestige else color
        pygame.draw.rect(surf, c, rect, border_radius=6)
        # Glow border
        bc = ACCENT if can_prestige else BORDER
        pygame.draw.rect(surf, bc, rect, 2, border_radius=6)

        label = f"PRESTIGE  (+{bonus:.2f}x mult)"
        txt = self.font_md.render(label, True, TEXT_WHITE)
        ico = icons.get("prestige")
        total_w = 16 + 4 + txt.get_width()
        ix = rect.centerx - total_w // 2
        surf.blit(ico, (ix, rect.centery - 8))
        surf.blit(txt, (ix + 20, rect.centery - txt.get_height() // 2))

        if can_prestige:
            self._buttons.append((rect, "upgrade", "__prestige__"))

    # ── Vibrant button helper ─────────────────────────────────
    def _draw_btn(self, surf, rect, label, enabled):
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)
        if enabled:
            c = BTN_BUY_H if hovered else BTN_BUY
            txt_c = TEXT_WHITE
            # Subtle glow when hovered
            if hovered:
                gs = pygame.Surface((rect.w + 4, rect.h + 4), pygame.SRCALPHA)
                gs.fill((80, 255, 120, 20))
                surf.blit(gs, (rect.x - 2, rect.y - 2))
        else:
            c = BTN_DISABLED
            txt_c = BTN_DIS_TXT
        pygame.draw.rect(surf, c, rect, border_radius=3)
        btxt = self.font_sm.render(label, True, txt_c)
        surf.blit(btxt, btxt.get_rect(center=rect.center))

    # ── Vibrant card drawer ──────────────────────────────────
    def _draw_card(self, surf, x, y, w, title, desc, detail, btn_label,
                   enabled, action_type, action_id,
                   icon_color=None, special=False) -> int:
        """Draw a shop item card with optional accent. Returns new y position."""
        h = 68
        rect = pygame.Rect(x, y, w, h)
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)
        bg = CARD_HOVER if hovered else CARD_BG

        pygame.draw.rect(surf, bg, rect, border_radius=5)

        # Special golden glow for hire card
        if special:
            glow_a = int(20 + 10 * math.sin(self.glow_t * 2))
            gs = pygame.Surface((w, h), pygame.SRCALPHA)
            gs.fill((255, 200, 50, max(0, glow_a)))
            surf.blit(gs, (x, y))
            pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=5)
        else:
            border_c = icon_color if (icon_color and hovered) else BORDER
            pygame.draw.rect(surf, border_c, rect, 1, border_radius=5)

        # Icon color accent bar + pixel icon
        if icon_color:
            pygame.draw.rect(surf, icon_color, (x, y + 4, 3, h - 8), border_radius=2)
        # Draw pixel icon if this is a shop item
        icon_name = icons.ITEM_ICONS.get(action_id)
        if icon_name:
            surf.blit(icons.get(icon_name), (x + 8, y + 6))
        elif special:
            surf.blit(icons.get("person"), (x + 8, y + 6))
        offset_x = 28 if (icon_name or special) else 8

        # Title
        ttxt = self.font_md.render(title, True, TEXT_WHITE)
        surf.blit(ttxt, (x + offset_x, y + 4))

        # Description
        dtxt = self.font_sm.render(desc, True, TEXT_GRAY)
        surf.blit(dtxt, (x + offset_x, y + 22))

        # Detail
        det = self.font_sm.render(detail, True, (90, 88, 110))
        surf.blit(det, (x + offset_x, y + 38))

        # Buy button
        btn_rect = pygame.Rect(x + w - 110, y + 38, 100, 24)
        self._draw_btn(surf, btn_rect, btn_label, enabled)
        if enabled:
            self._buttons.append((btn_rect, action_type, action_id))

        return y + h

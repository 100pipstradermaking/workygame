"""
game_screen.py — Modern pixel-art game screen manager for WORKY.
Full-screen layout with top bar, bottom navigation, and swappable screens:
  Home, Workers, Upgrades, Sabotage, Guild, Events.
Replaces the old UI + ShopUI split-panel layout.
"""

import pygame
import math
import random
from enum import IntEnum

from player import Player
from economy import (
    Economy, SABOTAGE_DEFS, GUILDS, GUILDS_BY_ID, GUILD_COLORS,
    SEASON_REWARDS, SEASON_NUMBER, SEASON_NAME,
    execute_sabotage, get_sabotage_income_mult,
    create_guild, join_guild, leave_guild, contribute_to_guild,
    get_guild_income_bonus, get_guild_xp_bonus,
    get_season_progress, get_season_time_remaining, claim_season_reward,
    _GUILD_CREATE_COST,
)
from worker import Worker, hire_cost, roll_rarity, RARITIES
from upgrades import (
    UPGRADE_DEFS, UPGRADES_BY_ID, get_upgrade_level,
    upgrade_cost, can_buy, buy_upgrade,
    get_hire_cost_discount, get_worker_upgrade_discount,
    get_sabotage_damage_reduction, get_sabotage_block_chance,
    get_sabotage_income_protection,
    get_speed_multiplier, get_efficiency_multiplier,
    get_income_multiplier,
)
from shop import (
    KITCHEN_ITEMS, DESIGN_ITEMS, BUSINESS_ITEMS, ALL_SHOP_ITEMS,
    shop_item_cost, shop_item_level, can_buy_shop_item, buy_shop_item,
    get_total_shop_multiplier, get_seat_count, get_attractiveness,
)
from theme import (
    BG, BG_DARK, BG_PANEL, BG_CARD, BG_CARD_H,
    TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, TEXT_DIM, TEXT_RED, TEXT_GREEN,
    TEXT_CYAN, TEXT_PINK,
    ACCENT, ACCENT_GLOW, BORDER, BORDER_LIGHT,
    BTN_PRIMARY, BTN_PRIMARY_H, BTN_BUY, BTN_BUY_H,
    BTN_DISABLED, BTN_DIS_TXT,
    NEON_CYAN, NEON_YELLOW, NEON_MAGENTA, NEON_GREEN, NEON_BLUE, NEON_ORANGE,
)
import icons
from ui_components import (
    get_font, draw_card, draw_button, draw_progress_bar,
    draw_badge, draw_separator, draw_section_header, draw_stat_row,
    draw_panel_bg, draw_glow_border, draw_icon_button,
    draw_coins_display, draw_locked_overlay, draw_neon_tab,
    draw_pixel_corners, draw_neon_glow,
)

# ── Layout constants ─────────────────────────────────────────
SCREEN_W, SCREEN_H = 960, 720
TOP_BAR_H = 48
BOT_NAV_H = 58
CONTENT_Y = TOP_BAR_H
CONTENT_H = SCREEN_H - TOP_BAR_H - BOT_NAV_H  # 614
REST_W = 560        # restaurant area width
PANEL_X = REST_W    # right panel x-offset
PANEL_W = SCREEN_W - REST_W  # 400


class Tab(IntEnum):
    WORKERS = 0
    UPGRADES = 1
    SABOTAGE = 2
    GUILD = 3
    SEASON = 4


TAB_INFO = [
    {"name": "Workers",  "icon": "person"},
    {"name": "Upgrades", "icon": "arrow_up"},
    {"name": "Sabotage", "icon": "fire"},
    {"name": "Guild",    "icon": "crown"},
    {"name": "Season",   "icon": "star"},
]

# Upgrade sub-tabs (Figma: Production, Sales, Automation, Defense)
UPGRADE_TABS = ["Production", "Sales", "Automation", "Defense"]
UPGRADE_TAB_COLORS = {
    "Production":  NEON_GREEN,
    "Sales":       NEON_YELLOW,
    "Automation":  NEON_CYAN,
    "Defense":     NEON_MAGENTA,
}

# Sabotage attack definitions (Figma design)
SABOTAGE_ATTACKS = [
    {"id": "grill_jam",       "name": "Grill Jam",        "icon": "fire",
     "desc": "Jam a rival's grill for 30s", "cooldown": 300,
     "cost": 100, "damage": 50, "color": NEON_ORANGE},
    {"id": "power_outage",    "name": "Power Outage",     "icon": "snowflake",
     "desc": "Cut power to a rival kitchen for 60s", "cooldown": 600,
     "cost": 200, "damage": 100, "color": NEON_YELLOW},
    {"id": "food_poisoning",  "name": "Food Poisoning",   "icon": "chef_hat",
     "desc": "Contaminate rival ingredients — customers flee!", "cooldown": 900,
     "cost": 300, "damage": 150, "color": NEON_GREEN},
    {"id": "network_hack",    "name": "Network Hack",     "icon": "speed",
     "desc": "Hack rival's ordering system — orders cancelled!", "cooldown": 1200,
     "cost": 500, "damage": 200, "color": NEON_CYAN},
]

# Guild perks (placeholder)
GUILD_PERKS = [
    {"name": "Shared Tips",    "icon": "coin",   "desc": "+5% income for all members",     "level": 1},
    {"name": "Bulk Ordering",  "icon": "fries",  "desc": "-10% hire cost for guild",       "level": 3},
    {"name": "Franchise Net",  "icon": "building","desc": "+15% prestige bonus",            "level": 5},
    {"name": "Guild Kitchen",  "icon": "pot",    "desc": "Unlock special recipes",          "level": 8},
]


class GameScreen:
    """Full-screen game UI with tabbed navigation."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.active_tab: Tab = Tab.WORKERS
        self.glow_t: float = 0.0

        # Scrolling per tab
        self._scroll = {t: 0 for t in Tab}
        self._max_scroll = {t: 0 for t in Tab}

        # Animated coin display
        self._display_coins: float = 0.0

        # Upgrade sub-tab
        self._upgrade_tab: int = 0

        # Clickable button rects (rebuilt each frame)
        self._buttons: list[tuple[pygame.Rect, str, str]] = []

        # Purchase effects
        self._flash: float = 0.0
        self._particles: list[dict] = []

        # Notification popup
        self._notif_msg: str = ""
        self._notif_timer: float = 0.0

        # Guild creation state
        self._guild_creating: bool = False
        self._guild_name_input: str = ""
        self._guild_color_idx: int = 0

        # Nav button rects
        self._nav_rects: list[pygame.Rect] = []
        tab_w = SCREEN_W // len(TAB_INFO)
        for i in range(len(TAB_INFO)):
            self._nav_rects.append(
                pygame.Rect(i * tab_w, SCREEN_H - BOT_NAV_H, tab_w, BOT_NAV_H))

        # Top bar button rects
        self._btn_exit = pygame.Rect(SCREEN_W - 110, 10, 100, 28)
        self._btn_leaderboard = pygame.Rect(SCREEN_W - 220, 10, 100, 28)

    # ── Update ───────────────────────────────────────────────
    def update(self, dt: float):
        self.glow_t += dt
        if self._flash > 0:
            self._flash -= dt * 3
        if self._notif_timer > 0:
            self._notif_timer -= dt
        alive = []
        for p in self._particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 80 * dt
            p["life"] -= dt
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive

    # ── Purchase effect ──────────────────────────────────────
    def _spawn_purchase_fx(self, mx: int, my: int):
        self._flash = 1.0
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 100)
            self._particles.append({
                "x": mx, "y": my,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 40,
                "life": random.uniform(0.4, 0.8),
                "max_life": 0.8,
                "color": random.choice([
                    NEON_YELLOW, NEON_GREEN, NEON_CYAN,
                    (255, 200, 50), (255, 255, 200),
                ]),
            })

    # ── Event handling ───────────────────────────────────────
    def handle_event(self, event: pygame.event.Event, player: Player) -> str | None:
        """Handle UI events. Returns action string or None.
        Possible actions: 'exit_to_menu', 'toggle_leaderboard', 'hired',
        'worker_upgraded', 'upgraded', 'shop_bought'.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Top bar buttons
            if self._btn_exit.collidepoint(mx, my):
                return "exit_to_menu"
            if self._btn_leaderboard.collidepoint(mx, my):
                return "toggle_leaderboard"

            # Bottom nav
            for i, rect in enumerate(self._nav_rects):
                if rect.collidepoint(mx, my):
                    self.active_tab = Tab(i)
                    self._scroll[self.active_tab] = 0
                    return None

            # Upgrade sub-tabs
            if self.active_tab == Tab.UPGRADES:
                sub_y = CONTENT_Y + 4
                margin_sub = 6
                total_sub_w = PANEL_W - margin_sub * 2
                tab_w = total_sub_w // len(UPGRADE_TABS)
                for i in range(len(UPGRADE_TABS)):
                    sub_rect = pygame.Rect(PANEL_X + margin_sub + i * tab_w, sub_y, tab_w - 4, 28)
                    if sub_rect.collidepoint(mx, my):
                        self._upgrade_tab = i
                        self._scroll[Tab.UPGRADES] = 0
                        return None

            # Content buttons
            for rect, action_type, action_id in self._buttons:
                if rect.collidepoint(mx, my):
                    if action_type == "hire":
                        cost = hire_cost(len(player.workers)) * get_hire_cost_discount(player)
                        if player.spend(cost):
                            rarity = roll_rarity()
                            player.workers.append(Worker(rarity=rarity))
                            self._spawn_purchase_fx(mx, my)
                            return "hired"
                    elif action_type == "worker_up":
                        idx = int(action_id)
                        if idx < len(player.workers):
                            w = player.workers[idx]
                            cost = w.upgrade_cost() * get_worker_upgrade_discount(player)
                            if player.spend(cost):
                                w.upgrade()
                                self._spawn_purchase_fx(mx, my)
                                return "worker_upgraded"
                    elif action_type == "upgrade":
                        if action_id in UPGRADES_BY_ID:
                            if buy_upgrade(player, action_id):
                                self._spawn_purchase_fx(mx, my)
                            return "upgraded"
                        elif action_id in ALL_SHOP_ITEMS:
                            if buy_shop_item(player, action_id):
                                self._spawn_purchase_fx(mx, my)
                            return "shop_bought"
                    elif action_type == "prestige":
                        if player.prestige():
                            self._spawn_purchase_fx(mx, my)
                            return "prestige"
                    elif action_type == "sabotage":
                        result = execute_sabotage(player, action_id)
                        if result["ok"]:
                            self._spawn_purchase_fx(mx, my)
                            self._notif_msg = result["msg"]
                            self._notif_timer = 2.5
                        else:
                            self._notif_msg = result["msg"]
                            self._notif_timer = 2.0
                        return "sabotage"
                    elif action_type == "guild_join":
                        if join_guild(player, action_id):
                            self._spawn_purchase_fx(mx, my)
                            self._notif_msg = f"Joined {GUILDS_BY_ID[action_id]['name']}!"
                            self._notif_timer = 2.5
                        return "guild_join"
                    elif action_type == "guild_leave":
                        if leave_guild(player):
                            self._notif_msg = "Left guild"
                            self._notif_timer = 2.0
                        return "guild_leave"
                    elif action_type == "guild_donate":
                        amt = min(player.coins * 0.1, 100)  # donate 10% or 100 max
                        if contribute_to_guild(player, amt):
                            self._spawn_purchase_fx(mx, my)
                            self._notif_msg = f"Donated {amt:.0f}c to guild!"
                            self._notif_timer = 2.0
                        return "guild_donate"
                    elif action_type == "guild_toggle_create":
                        self._guild_creating = not self._guild_creating
                        self._guild_name_input = ""
                        return None
                    elif action_type == "guild_color_pick":
                        self._guild_color_idx = int(action_id)
                        return None
                    elif action_type == "guild_create_confirm":
                        color = GUILD_COLORS[self._guild_color_idx % len(GUILD_COLORS)]
                        if create_guild(player, self._guild_name_input, color):
                            self._spawn_purchase_fx(mx, my)
                            self._notif_msg = f"Created guild '{self._guild_name_input.upper()}'!"
                            self._notif_timer = 2.5
                            self._guild_creating = False
                            self._guild_name_input = ""
                        else:
                            self._notif_msg = f"Need {_GUILD_CREATE_COST}c to create guild"
                            self._notif_timer = 2.0
                        return "guild_create"
                    elif action_type == "season_claim":
                        r = claim_season_reward(player, action_id)
                        if r:
                            self._spawn_purchase_fx(mx, my)
                            msg = f"Claimed {r['tier']}: +{r['coins']}c"
                            if r.get("worker"):
                                msg += f" + {r['worker']} worker!"
                            self._notif_msg = msg
                            self._notif_timer = 3.0
                            return "season_claimed"
                        return None

        # Scroll
        if event.type == pygame.MOUSEWHEEL:
            tab = self.active_tab
            ms = self._max_scroll.get(tab, 0)
            self._scroll[tab] = max(0, min(ms,
                                           self._scroll[tab] - event.y * 35))

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            # Guild name text input
            if self._guild_creating and self.active_tab == Tab.GUILD:
                if event.key == pygame.K_BACKSPACE:
                    self._guild_name_input = self._guild_name_input[:-1]
                    return None
                elif event.key == pygame.K_ESCAPE:
                    self._guild_creating = False
                    self._guild_name_input = ""
                    return None
                elif event.key == pygame.K_RETURN:
                    return None  # handled by confirm button
                elif event.unicode and len(self._guild_name_input) < 20:
                    ch = event.unicode
                    if ch.isprintable() and ch not in ('\t', '\r', '\n'):
                        self._guild_name_input += ch
                    return None
            if event.key == pygame.K_ESCAPE:
                return "exit_to_menu"
            if event.key == pygame.K_l:
                return "toggle_leaderboard"
            # Number keys switch tabs
            if pygame.K_1 <= event.key <= pygame.K_5:
                self.active_tab = Tab(event.key - pygame.K_1)
                return None

        return None

    # ── Draw ─────────────────────────────────────────────────
    def draw(self, player: Player, economy: Economy,
             ips: float, restaurant=None):
        """Draw the complete game screen."""
        self._buttons.clear()

        # Background (light cream)
        self.screen.fill(BG_DARK)

        # ── Restaurant area (always visible on left) ─────────
        rest_rect = pygame.Rect(0, CONTENT_Y, REST_W, CONTENT_H)
        if restaurant:
            restaurant.draw(self.screen, rest_rect)
            if economy.event_display_timer > 0 and economy.last_event_name:
                self._draw_event_popup(economy, rest_rect)

        # ── Right panel ──────────────────────────────────────
        panel_bg = pygame.Rect(PANEL_X, CONTENT_Y, PANEL_W, CONTENT_H)
        pygame.draw.rect(self.screen, BG_PANEL, panel_bg)
        pygame.draw.line(self.screen, BORDER_LIGHT,
                         (PANEL_X, CONTENT_Y), (PANEL_X, SCREEN_H - BOT_NAV_H))

        if self.active_tab == Tab.WORKERS:
            self._draw_workers(player)
        elif self.active_tab == Tab.UPGRADES:
            self._draw_upgrades(player)
        elif self.active_tab == Tab.SABOTAGE:
            self._draw_sabotage(player)
        elif self.active_tab == Tab.GUILD:
            self._draw_guild(player)
        elif self.active_tab == Tab.SEASON:
            self._draw_events(player, economy)

        # Top bar (always on top)
        self._draw_top_bar(player, ips)

        # Bottom nav (always on top)
        self._draw_bottom_nav()

        # Purchase flash
        if self._flash > 0:
            flash_a = int(40 * self._flash)
            fs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fs.fill((255, 255, 200, max(0, flash_a)))
            self.screen.blit(fs, (0, 0))

        # Particles
        for p in self._particles:
            alpha = max(0, min(255, int(255 * (p["life"] / p["max_life"]))))
            sz = 4
            ps = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"], alpha), (sz // 2, sz // 2), sz // 2)
            self.screen.blit(ps, (int(p["x"]) - sz // 2, int(p["y"]) - sz // 2))

        # Notification popup
        if self._notif_timer > 0 and self._notif_msg:
            alpha = min(255, int(self._notif_timer * 200))
            notif_font = get_font(13, bold=True)
            ntxt = notif_font.render(self._notif_msg, True, TEXT_WHITE)
            nw = ntxt.get_width() + 30
            nh = 36
            nx = (SCREEN_W - nw) // 2
            ny = CONTENT_Y + 10
            # Shadow
            ss = pygame.Surface((nw + 4, nh + 4), pygame.SRCALPHA)
            ss.fill((0, 0, 0, min(80, alpha // 3)))
            self.screen.blit(ss, (nx + 2, ny + 2))
            # Background
            ns = pygame.Surface((nw, nh), pygame.SRCALPHA)
            ns.fill((25, 28, 32, min(230, alpha)))
            self.screen.blit(ns, (nx, ny))
            pygame.draw.rect(self.screen, NEON_GREEN, (nx, ny, nw, nh), 2, border_radius=8)
            draw_pixel_corners(self.screen, pygame.Rect(nx, ny, nw, nh), NEON_GREEN, 3)
            # Green glow
            glow_a = min(40, alpha // 5)
            gs = pygame.Surface((nw, nh), pygame.SRCALPHA)
            gs.fill((*NEON_GREEN[:3], max(0, glow_a)))
            self.screen.blit(gs, (nx, ny))
            self.screen.blit(ntxt, (nx + 15, ny + 8))

    # ═══════════════════════════════════════════════════════════
    #  TOP BAR
    # ═══════════════════════════════════════════════════════════
    def _draw_top_bar(self, player: Player, ips: float):
        bar_rect = pygame.Rect(0, 0, SCREEN_W, TOP_BAR_H)
        pygame.draw.rect(self.screen, BG_PANEL, bar_rect)
        # Subtle gradient overlay
        grad = pygame.Surface((SCREEN_W, TOP_BAR_H), pygame.SRCALPHA)
        for gy in range(TOP_BAR_H):
            a = int(8 * (1 - gy / TOP_BAR_H))
            pygame.draw.line(grad, (0, 0, 0, a), (0, gy), (SCREEN_W, gy))
        self.screen.blit(grad, (0, 0))
        # Bottom border line (neon cyan) with glow
        pulse = int(180 + 75 * math.sin(self.glow_t * 2.5))
        glow_s = pygame.Surface((SCREEN_W, 4), pygame.SRCALPHA)
        glow_s.fill((*NEON_CYAN[:3], max(0, pulse // 8)))
        self.screen.blit(glow_s, (0, TOP_BAR_H - 3))
        pygame.draw.line(self.screen, NEON_CYAN, (0, TOP_BAR_H - 1),
                         (SCREEN_W, TOP_BAR_H - 1), 1)

        # Animated coins
        target = player.coins
        if abs(self._display_coins - target) > 0.5:
            speed = max(1.0, abs(target - self._display_coins) * 8)
            if self._display_coins < target:
                self._display_coins = min(target, self._display_coins + speed * (1/60))
            else:
                self._display_coins = max(target, self._display_coins - speed * (1/60))
        else:
            self._display_coins = target

        x = 12
        # Coin icon + amount (neon-yellow)
        self.screen.blit(icons.get("coin"), (x, 14))
        font_coins = get_font(22, bold=True)
        ct = font_coins.render(f"{self._display_coins:,.0f}", True, NEON_YELLOW)
        self.screen.blit(ct, (x + 20, 12))
        x += 28 + ct.get_width()

        # Divider
        pygame.draw.rect(self.screen, BORDER_LIGHT, (x, 8, 1, 32))
        x += 10

        # Income/s (neon-green)
        font_sm = get_font(13)
        self.screen.blit(icons.get_scaled("speed", 14), (x, 16))
        it = font_sm.render(f"{ips:,.1f}/s", True, NEON_GREEN)
        self.screen.blit(it, (x + 16, 16))
        x += 20 + it.get_width()

        # Workers count (neon-cyan)
        pygame.draw.rect(self.screen, BORDER_LIGHT, (x, 8, 1, 32))
        x += 10
        self.screen.blit(icons.get_scaled("person", 14), (x, 16))
        wt = font_sm.render(f"{len(player.workers)}", True, NEON_CYAN)
        self.screen.blit(wt, (x + 16, 16))
        x += 20 + wt.get_width()

        # Prestige level (neon-magenta)
        pygame.draw.rect(self.screen, BORDER_LIGHT, (x, 8, 1, 32))
        x += 10
        self.screen.blit(icons.get_scaled("prestige", 12), (x, 17))
        pt = font_sm.render(f"P{player.prestige_level} (x{player.prestige_multiplier:.1f})",
                            True, NEON_MAGENTA)
        self.screen.blit(pt, (x + 16, 16))

        # Active bonus
        if player.active_bonus_timer > 0:
            pulse = math.sin(self.glow_t * 5)
            col = (255, int(130 + 60 * pulse), 80)
            bonus_font = get_font(12, bold=True)
            bt = bonus_font.render(
                f"BONUS x{player.active_bonus_multiplier:.0f} ({player.active_bonus_timer:.0f}s)",
                True, col)
            bx = SCREEN_W - 230 - bt.get_width()
            bg_s = pygame.Surface((bt.get_width() + 8, 20), pygame.SRCALPHA)
            bg_s.fill((*NEON_ORANGE[:3], int(30 + 20 * pulse)))
            self.screen.blit(bg_s, (bx - 4, 14))
            self.screen.blit(bt, (bx, 15))

        # Restaurant name
        if player.restaurant_name:
            name_font = get_font(11)
            nt = name_font.render(player.restaurant_name, True, TEXT_GRAY)
            self.screen.blit(nt, (12, 34))

        # Action buttons (right side) — neon style
        mx, my = pygame.mouse.get_pos()
        # Leaderboard
        lb_hover = self._btn_leaderboard.collidepoint(mx, my)
        lb_c = NEON_BLUE if lb_hover else (100, 149, 237)
        pygame.draw.rect(self.screen, lb_c, self._btn_leaderboard, border_radius=6)
        draw_pixel_corners(self.screen, self._btn_leaderboard, lb_c, 2)
        lb_ico = icons.get_scaled("trophy", 14)
        lb_txt = get_font(11, bold=True).render("RANK", True, (255, 255, 255))
        lbx = self._btn_leaderboard.centerx - (14 + 4 + lb_txt.get_width()) // 2
        self.screen.blit(lb_ico, (lbx, self._btn_leaderboard.centery - 7))
        self.screen.blit(lb_txt, (lbx + 18, self._btn_leaderboard.centery - lb_txt.get_height() // 2))

        # Exit
        ex_hover = self._btn_exit.collidepoint(mx, my)
        ex_c = ACCENT if ex_hover else (220, 120, 120)
        pygame.draw.rect(self.screen, ex_c, self._btn_exit, border_radius=6)
        draw_pixel_corners(self.screen, self._btn_exit, ex_c, 2)
        ex_ico = icons.get_scaled("door", 14)
        ex_txt = get_font(11, bold=True).render("MENU", True, (255, 255, 255))
        exx = self._btn_exit.centerx - (14 + 4 + ex_txt.get_width()) // 2
        self.screen.blit(ex_ico, (exx, self._btn_exit.centery - 7))
        self.screen.blit(ex_txt, (exx + 18, self._btn_exit.centery - ex_txt.get_height() // 2))

    # ═══════════════════════════════════════════════════════════
    #  BOTTOM NAVIGATION
    # ═══════════════════════════════════════════════════════════
    def _draw_bottom_nav(self):
        nav_y = SCREEN_H - BOT_NAV_H
        nav_rect = pygame.Rect(0, nav_y, SCREEN_W, BOT_NAV_H)
        pygame.draw.rect(self.screen, BG, nav_rect)
        # Top border line
        pygame.draw.line(self.screen, BORDER_LIGHT, (0, nav_y), (SCREEN_W, nav_y), 1)

        tab_w = SCREEN_W // len(TAB_INFO)
        for i, info in enumerate(TAB_INFO):
            rect = self._nav_rects[i]
            active = i == self.active_tab
            draw_icon_button(self.screen, rect, info["icon"], info["name"],
                             active=active, color=BG,
                             active_color=BG_PANEL, glow_t=self.glow_t)
            # Active tab indicator bar
            if active:
                ind_w = min(tab_w - 12, 40)
                ind_x = rect.centerx - ind_w // 2
                pulse = int(180 + 75 * math.sin(self.glow_t * 3))
                pygame.draw.rect(self.screen, NEON_CYAN,
                                 (ind_x, nav_y, ind_w, 3), border_radius=1)
                glow_s = pygame.Surface((ind_w + 8, 6), pygame.SRCALPHA)
                glow_s.fill((*NEON_CYAN[:3], max(0, pulse // 6)))
                self.screen.blit(glow_s, (ind_x - 4, nav_y - 1))
            # Dividers
            if i > 0:
                pygame.draw.rect(self.screen, BORDER_LIGHT,
                                 (rect.x, nav_y + 8, 1, BOT_NAV_H - 16))

    # ═══════════════════════════════════════════════════════════
    #  HOME SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_home(self, player, economy, ips, restaurant):
        content_rect = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)

        # Restaurant fills content area
        if restaurant:
            restaurant.draw(self.screen, content_rect)

        # Event popup
        if economy.event_display_timer > 0 and economy.last_event_name:
            center_x = SCREEN_W // 2
            star_ico = icons.get_scaled("star", 18)
            ev_font = get_font(22, bold=True)
            name_txt = ev_font.render(f" {economy.last_event_name}! ", True,
                                      economy.last_event_color)
            total_w = 18 + 4 + name_txt.get_width() + 4 + 18
            left_x = center_x - total_w // 2
            text_y = CONTENT_Y + CONTENT_H - 60
            rect = pygame.Rect(left_x - 8, text_y - 4,
                               total_w + 16, name_txt.get_height() + 8)
            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            alpha = int(180 + 40 * math.sin(self.glow_t * 4))
            bg.fill((20, 20, 30, max(0, min(255, alpha))))
            self.screen.blit(bg, rect.topleft)
            pygame.draw.rect(self.screen, economy.last_event_color,
                             rect, 2, border_radius=6)
            self.screen.blit(star_ico, (left_x, text_y + 2))
            self.screen.blit(name_txt, (left_x + 22, text_y))
            self.screen.blit(star_ico, (left_x + 22 + name_txt.get_width() + 4, text_y + 2))

        # Quick-stats overlay (bottom-left of content)
        self._draw_home_stats_overlay(player, economy, ips)

    def _draw_home_stats_overlay(self, player, economy, ips):
        """Translucent stats panel overlaid on restaurant."""
        ow, oh = 280, 130
        ox = 10
        oy = CONTENT_Y + CONTENT_H - oh - 10
        overlay = pygame.Surface((ow, oh), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 200))
        self.screen.blit(overlay, (ox, oy))
        pygame.draw.rect(self.screen, BORDER_LIGHT, (ox, oy, ow, oh), 1, border_radius=6)

        # Economy stats
        font = get_font(12)
        di = economy.dinein_orders
        to = economy.takeout_orders
        total = di + to
        di_pct = (di / total * 100) if total > 0 else 0

        y = oy + 8
        t1 = font.render(f"Dine-In: {di:,} ({di_pct:.0f}%)  ${economy.dinein_income:,.0f}",
                         True, TEXT_CYAN)
        self.screen.blit(t1, (ox + 8, y))
        y += 16
        t2 = font.render(f"Takeout: {to:,} ({100-di_pct:.0f}%)  ${economy.takeout_income:,.0f}",
                         True, TEXT_GREEN)
        self.screen.blit(t2, (ox + 8, y))
        y += 16
        t3 = font.render(f"Total Income: ${player.total_income:,.0f}", True, TEXT_GOLD)
        self.screen.blit(t3, (ox + 8, y))
        y += 20

        # Dine-in ratio bar
        bar_w = ow - 16
        draw_progress_bar(self.screen, ox + 8, y, bar_w, 8,
                          di_pct / 100, color=(80, 200, 255))
        y += 12
        lbl1 = font.render("Dine-In", True, TEXT_GRAY)
        lbl2 = font.render("Takeout", True, TEXT_GRAY)
        self.screen.blit(lbl1, (ox + 8, y))
        self.screen.blit(lbl2, (ox + ow - 8 - lbl2.get_width(), y))

        # Attractiveness stars (top-right of overlay)
        from shop import get_attractiveness
        attract = get_attractiveness(player)
        if attract > 0:
            stars_full = attract // 20
            star_x = ox + ow - 82
            for si in range(5):
                s_ico = icons.get_scaled("star", 10)
                if si >= stars_full:
                    s_ico = s_ico.copy()
                    s_ico.set_alpha(60)
                self.screen.blit(s_ico, (star_x + si * 12, oy + 8))

    # ═══════════════════════════════════════════════════════════
    #  WORKERS SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_workers(self, player):
        area = pygame.Rect(PANEL_X, CONTENT_Y, PANEL_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)

        scroll = self._scroll[Tab.WORKERS]
        margin = 10
        lx = PANEL_X + margin
        card_w = PANEL_W - margin * 2
        y = CONTENT_Y + 8 - scroll

        # Header
        title = get_font(16, bold=True).render("WORKERS", True, NEON_CYAN)
        self.screen.blit(title, (lx, y))
        count_txt = get_font(11).render(f"{len(player.workers)} hired", True, TEXT_GRAY)
        self.screen.blit(count_txt, (lx + title.get_width() + 8, y + 3))
        y += 24

        # Hire card
        hire_c = hire_cost(len(player.workers)) * get_hire_cost_discount(player)
        affordable = player.coins >= hire_c
        draw_card(self.screen, lx, y, card_w, 50, special=True, glow_t=self.glow_t)
        self.screen.blit(icons.get("person"), (lx + 8, y + 8))
        hire_title = get_font(13, bold=True).render("Hire New Worker", True, TEXT_WHITE)
        self.screen.blit(hire_title, (lx + 28, y + 6))
        hire_desc = get_font(10).render(
            f"Random rarity  |  {len(player.workers)} workers", True, TEXT_GRAY)
        self.screen.blit(hire_desc, (lx + 28, y + 22))
        rarity_x = lx + 28
        for rname, rdata in RARITIES.items():
            w_pct = get_font(9).render(f"{rname[0].upper()}{rdata['weight']:.0f}%", True,
                                        rdata["color"])
            self.screen.blit(w_pct, (rarity_x, y + 36))
            rarity_x += w_pct.get_width() + 5
        btn_rect = pygame.Rect(lx + card_w - 120, y + 12, 110, 26)
        draw_button(self.screen, btn_rect, f"HIRE {hire_c:,.0f}c", affordable,
                    color=BTN_PRIMARY, hover_color=BTN_PRIMARY_H, font_size=12)
        if affordable:
            self._buttons.append((btn_rect, "hire", "new"))

        y += 56
        draw_separator(self.screen, lx, y, card_w)
        y += 6

        # Worker cards (single column)
        from sprites import WorkySpriteRenderer
        for i, wk in enumerate(player.workers):
            card_h = 72
            card_rect = pygame.Rect(lx, y, card_w, card_h)
            mx, my_m = pygame.mouse.get_pos()
            hovered = card_rect.collidepoint(mx, my_m)

            rarity_col = RARITIES[wk.rarity]["color"]
            draw_card(self.screen, lx, y, card_w, card_h,
                      hover=hovered, accent_color=rarity_col, glow_t=self.glow_t)

            # Worker sprite (compact)
            spr = WorkySpriteRenderer(wk.archetype, RARITIES[wk.rarity]["color"], wk.skin_tone)
            spr_surf = pygame.Surface((36, 46), pygame.SRCALPHA)
            spr.draw(spr_surf, 18, 24, direction="down", anim_frame=0,
                     state="idle", rarity=wk.rarity)
            self.screen.blit(spr_surf, (lx + 4, y + 12))

            info_x = lx + 44
            # Name + rarity
            name_str = wk.archetype.replace('_', ' ').title()
            name_txt = get_font(12, bold=True).render(name_str, True, TEXT_WHITE)
            self.screen.blit(name_txt, (info_x, y + 4))
            draw_badge(self.screen, info_x + name_txt.get_width() + 4,
                       y + 5, wk.rarity.upper(), rarity_col, 8)

            # Level + stats
            stats_font = get_font(10)
            lvl_txt = stats_font.render(f"Lv{wk.level}", True, TEXT_CYAN)
            self.screen.blit(lvl_txt, (info_x, y + 20))
            st1 = stats_font.render(f"SPD {wk.speed:.1f}", True, TEXT_GREEN)
            st2 = stats_font.render(f"EFF {wk.efficiency:.1f}", True, TEXT_PINK)
            st3 = stats_font.render(f"{wk.get_income():.1f}/s", True, TEXT_GOLD)
            self.screen.blit(st1, (info_x + 30, y + 20))
            self.screen.blit(st2, (info_x + 90, y + 20))
            self.screen.blit(st3, (info_x + 155, y + 20))

            # Progress bar
            max_income = max(w.get_income() for w in player.workers) if player.workers else 1
            bar_pct = wk.get_income() / max_income if max_income > 0 else 0
            draw_progress_bar(self.screen, info_x, y + 34,
                              card_w - 54 - 110, 5, bar_pct, color=rarity_col)

            # Upgrade button
            up_cost = wk.upgrade_cost() * get_worker_upgrade_discount(player)
            can_up = player.coins >= up_cost
            btn_r = pygame.Rect(lx + card_w - 105, y + 46, 95, 22)
            draw_button(self.screen, btn_r, f"UP {up_cost:,.0f}c", can_up, font_size=10)
            if can_up:
                self._buttons.append((btn_r, "worker_up", str(i)))

            y += card_h + 4

        y += 16
        self._max_scroll[Tab.WORKERS] = max(0, y - CONTENT_Y - CONTENT_H + 20)
        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  UPGRADES SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_upgrades(self, player):
        area = pygame.Rect(PANEL_X, CONTENT_Y, PANEL_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        # Sub-tabs
        self._draw_upgrade_tabs()

        # Content below sub-tabs
        content_y = CONTENT_Y + 36
        content_h = CONTENT_H - 36
        content_rect = pygame.Rect(PANEL_X, content_y, PANEL_W, content_h)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(content_rect)

        scroll = self._scroll[Tab.UPGRADES]
        margin = 10
        y = content_y + 8 - scroll

        if self._upgrade_tab == 0:
            y = self._draw_upgrade_items(player, y, margin, "Production", KITCHEN_ITEMS,
                                          "Production")
        elif self._upgrade_tab == 1:
            y = self._draw_upgrade_items(player, y, margin, "Sales", DESIGN_ITEMS,
                                          "Sales")
        elif self._upgrade_tab == 2:
            y = self._draw_upgrade_items(player, y, margin, "Automation", BUSINESS_ITEMS,
                                          "Automation")
        elif self._upgrade_tab == 3:
            y = self._draw_defense_tab(player, y, margin)

        # Prestige section at bottom
        y += 16
        y = self._draw_prestige_section(player, y, margin)

        self._max_scroll[Tab.UPGRADES] = max(0, y - content_y - content_h + 20)
        self.screen.set_clip(prev_clip)

    def _draw_upgrade_tabs(self):
        sub_y = CONTENT_Y + 4
        margin = 6
        total_w = PANEL_W - margin * 2
        tab_w = total_w // len(UPGRADE_TABS)
        for i, name in enumerate(UPGRADE_TABS):
            rect = pygame.Rect(PANEL_X + margin + i * tab_w, sub_y, tab_w - 4, 28)
            active = i == self._upgrade_tab
            color = UPGRADE_TAB_COLORS[name]
            draw_neon_tab(self.screen, rect, name, active=active,
                          color=color, glow_t=self.glow_t)

    def _draw_upgrade_items(self, player, y, margin, section_name, items, upgrade_cats):
        """Draw upgrade category items. Returns new y."""
        w = PANEL_W - margin * 2
        x = PANEL_X + margin

        # Original upgrades from upgrades.py
        cats = upgrade_cats.split("|")
        has_ugrades = False
        for u in UPGRADE_DEFS:
            if u["category"] not in cats:
                continue
            has_ugrades = True
            lvl = get_upgrade_level(player, u["id"])
            maxed = lvl >= u["max_level"]
            cost = upgrade_cost(u["id"], lvl) if not maxed else 0
            affordable = can_buy(player, u["id"])

            card_h = 64
            mx_m, my_m = pygame.mouse.get_pos()
            hovered = pygame.Rect(x, y, w, card_h).collidepoint(mx_m, my_m)
            draw_card(self.screen, x, y, w, card_h, hover=hovered, glow_t=self.glow_t)

            # Name + level
            name_txt = get_font(14, bold=True).render(
                f'{u["name"]}', True, TEXT_WHITE)
            self.screen.blit(name_txt, (x + 10, y + 6))

            lvl_str = f"Lv {lvl}/{u['max_level']}" if not maxed else "MAX"
            lvl_col = TEXT_GOLD if maxed else TEXT_CYAN
            lvl_txt = get_font(11).render(lvl_str, True, lvl_col)
            self.screen.blit(lvl_txt, (x + 10 + name_txt.get_width() + 8, y + 8))

            # Description
            desc_txt = get_font(11).render(u["desc"], True, TEXT_GRAY)
            self.screen.blit(desc_txt, (x + 10, y + 24))

            # Progress bar
            progress = lvl / u["max_level"] if u["max_level"] > 0 else 0
            draw_progress_bar(self.screen, x + 10, y + 42, w - 160, 8, progress,
                              color=TEXT_GREEN, show_shimmer=True, glow_t=self.glow_t)

            # Buy button
            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            btn_r = pygame.Rect(x + w - 140, y + 34, 130, 24)
            draw_button(self.screen, btn_r, btn_label, affordable and not maxed, font_size=12)
            if affordable and not maxed:
                self._buttons.append((btn_r, "upgrade", u["id"]))

            y += card_h + 4

        if has_ugrades:
            draw_separator(self.screen, x, y, w, TEXT_DIM)
            y += 12

        # Shop items
        section_lbl = get_font(14, bold=True).render(f"{section_name} Upgrades", True, TEXT_GOLD)
        self.screen.blit(section_lbl, (x, y))
        y += 20

        for item in items:
            lvl = shop_item_level(player, item["id"])
            maxed = lvl >= item["max_level"]
            cost = shop_item_cost(item["id"], lvl) if not maxed else 0
            affordable = can_buy_shop_item(player, item["id"])
            ic = item.get("icon_color", BORDER)

            card_h = 72
            mx_m, my_m = pygame.mouse.get_pos()
            hovered = pygame.Rect(x, y, w, card_h).collidepoint(mx_m, my_m)
            draw_card(self.screen, x, y, w, card_h, hover=hovered,
                      accent_color=ic, glow_t=self.glow_t)

            # Icon
            icon_name = icons.ITEM_ICONS.get(item["id"])
            off_x = 10
            if icon_name:
                self.screen.blit(icons.get(icon_name), (x + 10, y + 8))
                off_x = 32

            # Name
            name_txt = get_font(14, bold=True).render(item["name"], True, TEXT_WHITE)
            self.screen.blit(name_txt, (x + off_x, y + 6))

            # Level badge
            lvl_str = f"Lv {lvl}/{item['max_level']}" if not maxed else "MAX"
            lvl_col = TEXT_GOLD if maxed else TEXT_CYAN
            lvl_txt = get_font(11).render(lvl_str, True, lvl_col)
            self.screen.blit(lvl_txt, (x + off_x + name_txt.get_width() + 8, y + 8))

            # Description
            desc_txt = get_font(11).render(item["desc"], True, TEXT_GRAY)
            self.screen.blit(desc_txt, (x + off_x, y + 24))

            # Progress bar
            progress = lvl / item["max_level"] if item["max_level"] > 0 else 0
            draw_progress_bar(self.screen, x + off_x, y + 42, w - off_x - 160, 8, progress,
                              color=ic, show_shimmer=True, glow_t=self.glow_t)

            # Buy button
            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            btn_r = pygame.Rect(x + w - 140, y + 40, 130, 24)
            draw_button(self.screen, btn_r, btn_label, affordable and not maxed, font_size=12)
            if affordable and not maxed:
                self._buttons.append((btn_r, "upgrade", item["id"]))

            y += card_h + 4

        return y

    def _draw_design_upgrades(self, player, y, margin):
        """Design tab with attractiveness header + design items."""
        w = PANEL_W - margin * 2
        x = PANEL_X + margin

        # ── Attractiveness header ────────────────────────────
        attract = get_attractiveness(player)
        header_h = 70
        if attract >= 80:
            hdr_bg, hdr_border = BG_CARD, NEON_YELLOW
        elif attract >= 50:
            hdr_bg, hdr_border = BG_CARD, NEON_GREEN
        else:
            hdr_bg, hdr_border = BG_CARD, NEON_CYAN
        header_rect = pygame.Rect(x, y, w, header_h)
        pygame.draw.rect(self.screen, hdr_bg, header_rect, border_radius=6)
        pygame.draw.rect(self.screen, hdr_border, header_rect, 2, border_radius=6)

        # Stars
        stars_full = attract // 20
        for si in range(5):
            s_ico = icons.get_scaled("star", 16)
            if si >= stars_full:
                s_ico = s_ico.copy()
                s_ico.set_alpha(60)
            self.screen.blit(s_ico, (x + 12 + si * 20, y + 8))

        # Score
        pct_txt = get_font(24, bold=True).render(f"{attract}%", True, hdr_border)
        self.screen.blit(pct_txt, (x + w - pct_txt.get_width() - 16, y + 4))

        # Bar
        draw_progress_bar(self.screen, x + 12, y + 36, w - 24, 14,
                          attract / 100,
                          color=(80, 220, 100) if attract >= 66 else
                                (220, 180, 50) if attract >= 33 else (200, 80, 60),
                          show_shimmer=True, glow_t=self.glow_t)

        lbl = get_font(11).render("ATTRACTIVENESS", True, TEXT_GRAY)
        self.screen.blit(lbl, lbl.get_rect(centerx=x + w // 2, top=y + 54))

        y += header_h + 10

        # Seats summary
        seats = get_seat_count(player)
        seats_rect = pygame.Rect(x, y, w, 28)
        pygame.draw.rect(self.screen, BG, seats_rect, border_radius=4)
        self.screen.blit(icons.get_scaled("chair", 12), (x + 10, y + 8))
        self.screen.blit(get_font(12).render(f"Seats: {seats}", True, TEXT_CYAN), (x + 26, y + 6))
        tip = get_font(11).render("More seats = dine-in x1.5", True, TEXT_GREEN)
        self.screen.blit(tip, (x + w - tip.get_width() - 10, y + 7))
        y += 34

        # Design item cards
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
            ic = item.get("icon_color", BORDER)

            card_h = 80
            mx_m, my_m = pygame.mouse.get_pos()
            card_rect = pygame.Rect(x, y, w, card_h)
            hovered = card_rect.collidepoint(mx_m, my_m)
            draw_card(self.screen, x, y, w, card_h, hover=hovered,
                      accent_color=ic, glow_t=self.glow_t)

            # Icon
            icon_name = icons.ITEM_ICONS.get(iid)
            off_x = 10
            if icon_name:
                self.screen.blit(icons.get(icon_name), (x + 10, y + 8))
                off_x = 32

            # Name + level
            name_txt = get_font(14, bold=True).render(item["name"], True, TEXT_WHITE)
            self.screen.blit(name_txt, (x + off_x, y + 6))
            lvl_str = "MAX" if maxed else f"Lv {lvl}/{item['max_level']}"
            lvl_col = TEXT_GOLD if maxed else TEXT_CYAN
            self.screen.blit(get_font(11).render(lvl_str, True, lvl_col),
                             (x + off_x + name_txt.get_width() + 8, y + 8))

            # Description
            self.screen.blit(get_font(11).render(item["desc"], True, TEXT_GRAY),
                             (x + off_x, y + 24))

            # Current effect
            eff_str = effect_labels[iid]()
            self.screen.blit(get_font(11).render(f"Current: {eff_str}", True, TEXT_GREEN),
                             (x + off_x, y + 38))

            # Level progress bar with pips
            pb_x = x + off_x
            pb_w = w - off_x - 160
            draw_progress_bar(self.screen, pb_x, y + 54, pb_w, 8,
                              lvl / item["max_level"] if item["max_level"] > 0 else 0,
                              color=ic, show_shimmer=True, glow_t=self.glow_t)

            # Buy button
            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            btn_r = pygame.Rect(x + w - 140, y + 48, 130, 24)
            draw_button(self.screen, btn_r, btn_label, affordable and not maxed, font_size=12)
            if affordable and not maxed:
                self._buttons.append((btn_r, "upgrade", iid))

            y += card_h + 4

        return y

    def _draw_defense_tab(self, player, y, margin):
        """Defense tab — real purchasable defense upgrades + stats."""
        w = PANEL_W - margin * 2
        x = PANEL_X + margin

        # Header
        y = draw_section_header(self.screen, x, y, w, "Defense Upgrades",
                                color=NEON_MAGENTA, icon_name="snowflake")
        y += 4

        # Defense stats summary card
        dmg_red = (1.0 - get_sabotage_damage_reduction(player)) * 100
        blk_ch = get_sabotage_block_chance(player) * 100
        inc_prot = (1.0 - get_sabotage_income_protection(player)) * 100
        stat_h = 58
        stat_rect = pygame.Rect(x, y, w, stat_h)
        pygame.draw.rect(self.screen, BG_CARD, stat_rect, border_radius=8)
        pulse = int(8 + 5 * math.sin(self.glow_t * 2))
        pygame.draw.rect(self.screen, NEON_MAGENTA, stat_rect, 2, border_radius=8)
        draw_pixel_corners(self.screen, stat_rect, NEON_MAGENTA, 3)
        # Shield icon
        self.screen.blit(icons.get_scaled("snowflake", 16), (x + 8, y + 6))
        self.screen.blit(get_font(12, bold=True).render("DEFENSE STATUS", True, NEON_MAGENTA),
                         (x + 28, y + 4))
        # Stats bars
        bar_w = (w - 20) // 3 - 4
        bar_y = y + 24
        stats = [
            ("DMG Red", dmg_red, NEON_CYAN),
            ("Block %", blk_ch, NEON_GREEN),
            ("Inc Prot", inc_prot, NEON_YELLOW),
        ]
        for i, (lbl, val, col) in enumerate(stats):
            bx = x + 10 + i * (bar_w + 4)
            self.screen.blit(get_font(9).render(lbl, True, TEXT_GRAY), (bx, bar_y))
            draw_progress_bar(self.screen, bx, bar_y + 12, bar_w, 8,
                              val / 100, color=col, show_shimmer=True, glow_t=self.glow_t)
            self.screen.blit(get_font(9, bold=True).render(f"{val:.0f}%", True, col),
                             (bx + bar_w - 24, bar_y))
        y += stat_h + 8

        # Defense upgrade cards (real, purchasable)
        def_icons = {"def_firewall": "snowflake", "def_security": "door", "def_insurance": "coin"}
        def_colors = {"def_firewall": NEON_CYAN, "def_security": NEON_MAGENTA, "def_insurance": NEON_GREEN}
        for u in UPGRADE_DEFS:
            if u["category"] != "Defense":
                continue
            uid = u["id"]
            lvl = get_upgrade_level(player, uid)
            maxed = lvl >= u["max_level"]
            cost = upgrade_cost(uid, lvl) if not maxed else 0
            affordable = can_buy(player, uid)
            acc_col = def_colors.get(uid, NEON_MAGENTA)

            card_h = 74
            mx_m, my_m = pygame.mouse.get_pos()
            card_rect = pygame.Rect(x, y, w, card_h)
            hovered = card_rect.collidepoint(mx_m, my_m)
            draw_card(self.screen, x, y, w, card_h, hover=hovered,
                      accent_color=acc_col, glow_t=self.glow_t)

            ico = icons.get_scaled(def_icons.get(uid, "snowflake"), 16)
            self.screen.blit(ico, (x + 10, y + 8))
            name_txt = get_font(13, bold=True).render(u["name"], True, TEXT_WHITE)
            self.screen.blit(name_txt, (x + 32, y + 6))
            lvl_str = f"Lv {lvl}/{u['max_level']}" if not maxed else "MAX"
            lvl_col = TEXT_GOLD if maxed else TEXT_CYAN
            self.screen.blit(get_font(11).render(lvl_str, True, lvl_col),
                             (x + 32 + name_txt.get_width() + 8, y + 8))

            desc_txt = get_font(10).render(u["desc"], True, TEXT_GRAY)
            self.screen.blit(desc_txt, (x + 32, y + 24))

            # Effect readout
            if uid == "def_firewall":
                eff_str = f"Current: -{(1.0 - get_sabotage_damage_reduction(player))*100:.0f}% dmg"
            elif uid == "def_security":
                eff_str = f"Current: {get_sabotage_block_chance(player)*100:.0f}% block"
            else:
                eff_str = f"Current: -{(1.0 - get_sabotage_income_protection(player))*100:.0f}% loss"
            self.screen.blit(get_font(10).render(eff_str, True, acc_col), (x + 32, y + 38))

            # Progress bar
            progress = lvl / u["max_level"] if u["max_level"] > 0 else 0
            draw_progress_bar(self.screen, x + 32, y + 52, w - 180, 7, progress,
                              color=acc_col, show_shimmer=True, glow_t=self.glow_t)

            # Buy button
            btn_label = "MAXED" if maxed else f"BUY {cost:,.0f}c"
            btn_r = pygame.Rect(x + w - 130, y + 44, 120, 24)
            draw_button(self.screen, btn_r, btn_label, affordable and not maxed, font_size=11)
            if affordable and not maxed:
                self._buttons.append((btn_r, "upgrade", uid))

            y += card_h + 6

        y += 8

        # Prestige section at bottom
        y = self._draw_prestige_section(player, y, margin)
        return y

    def _draw_prestige_section(self, player, y, margin):
        """Draw prestige button section — neon style."""
        w = PANEL_W - margin * 2
        x = PANEL_X + margin
        rect = pygame.Rect(x, y, w, 50)
        bonus = player.get_prestige_bonus()
        can_prestige = bonus >= 0.01

        if can_prestige:
            pulse = int(15 * math.sin(self.glow_t * 3))
            color = (NEON_ORANGE[0], max(0, NEON_ORANGE[1] + pulse), NEON_ORANGE[2])
        else:
            color = BTN_DISABLED

        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my) and can_prestige
        if hovered and can_prestige:
            c = (min(255, color[0] + 20), min(255, color[1] + 20), color[2])
        else:
            c = color
        pygame.draw.rect(self.screen, c, rect, border_radius=8)
        bc = NEON_ORANGE if can_prestige else BORDER_LIGHT
        pygame.draw.rect(self.screen, bc, rect, 2, border_radius=8)
        if can_prestige:
            draw_pixel_corners(self.screen, rect, NEON_ORANGE, 3)

        ico = icons.get("prestige")
        label = f"PRESTIGE  (+{bonus:.2f}x multiplier)"
        txt = get_font(16, bold=True).render(label, True, (255, 255, 255))
        total_w = 16 + 8 + txt.get_width()
        ix = rect.centerx - total_w // 2
        self.screen.blit(ico, (ix, rect.centery - 8))
        self.screen.blit(txt, (ix + 24, rect.centery - txt.get_height() // 2))

        if can_prestige:
            self._buttons.append((rect, "prestige", "__prestige__"))

        return y + 60

    # ═══════════════════════════════════════════════════════════
    #  SABOTAGE SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_sabotage(self, player):
        area = pygame.Rect(PANEL_X, CONTENT_Y, PANEL_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        margin = 10
        lx = PANEL_X + margin
        w = PANEL_W - margin * 2
        y = CONTENT_Y + 8

        # Header
        fire_ico = icons.get_scaled("fire", 16)
        self.screen.blit(fire_ico, (lx, y))
        title = get_font(16, bold=True).render("SABOTAGE", True, NEON_MAGENTA)
        self.screen.blit(title, (lx + 20, y))
        attacks_sent = get_font(10).render(
            f"Attacks sent: {player.sabotage_attacks_sent}", True, TEXT_GRAY)
        self.screen.blit(attacks_sent, (lx + w - attacks_sent.get_width(), y + 4))
        y += 24

        # Attack cards
        for atk in SABOTAGE_ATTACKS:
            atk_id = atk["id"]
            defn = SABOTAGE_DEFS.get(atk_id, {})
            card_h = 70
            mx_m, my_m = pygame.mouse.get_pos()
            card_rect = pygame.Rect(lx, y, w, card_h)
            hovered = card_rect.collidepoint(mx_m, my_m)

            on_cd = atk_id in player.sabotage_cooldowns
            can_afford = player.coins >= atk["cost"]
            atk_color = atk.get("color", NEON_ORANGE)

            draw_card(self.screen, lx, y, w, card_h, hover=hovered,
                      accent_color=atk_color, glow_t=self.glow_t)

            ico = icons.get_scaled(atk["icon"], 14)
            self.screen.blit(ico, (lx + 8, y + 8))
            name_txt = get_font(13, bold=True).render(atk["name"], True, TEXT_WHITE)
            self.screen.blit(name_txt, (lx + 28, y + 6))
            draw_badge(self.screen, lx + 28 + name_txt.get_width() + 6,
                       y + 8, f"{atk['damage']}DMG", atk_color, 9)

            desc = get_font(10).render(atk["desc"], True, TEXT_GRAY)
            self.screen.blit(desc, (lx + 28, y + 24))

            # Cost and cooldown info
            cost_txt = get_font(10).render(f"{atk['cost']:,}c", True, NEON_YELLOW)
            self.screen.blit(cost_txt, (lx + 28, y + 40))

            if on_cd:
                cd_remaining = player.sabotage_cooldowns[atk_id]
                cd_min = int(cd_remaining) // 60
                cd_sec = int(cd_remaining) % 60
                cd_txt = get_font(10, bold=True).render(
                    f"CD {cd_min}:{cd_sec:02d}", True, TEXT_RED)
                self.screen.blit(cd_txt, (lx + 28 + cost_txt.get_width() + 10, y + 40))
                # Cooldown progress bar
                cd_pct = 1.0 - (cd_remaining / atk["cooldown"])
                draw_progress_bar(self.screen, lx + 28, y + 56, w - 44, 6,
                                  cd_pct, color=atk_color, glow_t=self.glow_t)
            else:
                cd_txt = get_font(10).render(f"CD {atk['cooldown']}s", True, TEXT_DIM)
                self.screen.blit(cd_txt, (lx + 28 + cost_txt.get_width() + 10, y + 40))

            # Attack button
            btn_w, btn_h = 60, 22
            btn_rect = pygame.Rect(lx + w - btn_w - 6, y + 40, btn_w, btn_h)
            if on_cd:
                pygame.draw.rect(self.screen, BTN_DISABLED, btn_rect, border_radius=4)
                btn_label = get_font(9).render("WAIT", True, BTN_DIS_TXT)
            elif not can_afford:
                pygame.draw.rect(self.screen, BTN_DISABLED, btn_rect, border_radius=4)
                btn_label = get_font(9).render("NO $", True, BTN_DIS_TXT)
            else:
                btn_hover = btn_rect.collidepoint(mx_m, my_m)
                bc = BTN_BUY_H if btn_hover else BTN_BUY
                pygame.draw.rect(self.screen, bc, btn_rect, border_radius=4)
                pygame.draw.rect(self.screen, atk_color, btn_rect, 1, border_radius=4)
                btn_label = get_font(9, bold=True).render("ATTACK", True, TEXT_WHITE)
                self._buttons.append((btn_rect, "sabotage", atk_id))
            self.screen.blit(btn_label, btn_label.get_rect(center=btn_rect.center))

            y += card_h + 6

        # Defense stats
        y += 4
        info_rect = pygame.Rect(lx, y, w, 56)
        pygame.draw.rect(self.screen, BG_CARD, info_rect, border_radius=8)
        pygame.draw.rect(self.screen, NEON_MAGENTA, info_rect, 1, border_radius=8)
        draw_pixel_corners(self.screen, info_rect, NEON_MAGENTA, 2)
        info_t1 = get_font(11, bold=True).render("Defense Stats", True, NEON_MAGENTA)
        self.screen.blit(info_t1, (lx + 8, y + 4))
        dmg_red = (1.0 - get_sabotage_damage_reduction(player)) * 100
        blk_ch = get_sabotage_block_chance(player) * 100
        inc_prot = (1.0 - get_sabotage_income_protection(player)) * 100
        def_txt = get_font(10).render(
            f"DMG Reduce: {dmg_red:.0f}%  |  Block: {blk_ch:.0f}%  |  Income Prot: {inc_prot:.0f}%",
            True, TEXT_GRAY)
        self.screen.blit(def_txt, (lx + 8, y + 22))
        hint = get_font(9).render("Upgrade Defense in Upgrades tab!", True, TEXT_DIM)
        self.screen.blit(hint, (lx + 8, y + 38))

        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  GUILD SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_guild(self, player):
        area = pygame.Rect(PANEL_X, CONTENT_Y, PANEL_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        scroll = self._scroll[Tab.GUILD]
        margin = 10
        lx = PANEL_X + margin
        w = PANEL_W - margin * 2
        y = CONTENT_Y + 8 - scroll

        # Header
        crown_ico = icons.get_scaled("crown", 16)
        self.screen.blit(crown_ico, (lx, y))
        title = get_font(16, bold=True).render("GUILD NETWORK", True, NEON_YELLOW)
        self.screen.blit(title, (lx + 20, y))
        y += 24

        mx_m, my_m = pygame.mouse.get_pos()

        if player.guild_id:
            # ── CURRENT GUILD INFO ──
            guild = GUILDS_BY_ID.get(player.guild_id)
            if guild:
                gc = guild["color"]
                info_h = 120
                info_rect = pygame.Rect(lx, y, w, info_h)
                pygame.draw.rect(self.screen, BG_CARD, info_rect, border_radius=10)
                pygame.draw.rect(self.screen, gc, info_rect, 2, border_radius=10)
                draw_pixel_corners(self.screen, info_rect, gc, 3)

                glow_a = int(10 + 8 * math.sin(self.glow_t * 1.5))
                gs = pygame.Surface((w, info_h), pygame.SRCALPHA)
                gs.fill((*gc[:3], max(0, glow_a)))
                self.screen.blit(gs, (lx, y))

                # Guild badge circle
                badge_cx = lx + 24
                badge_cy = y + 24
                pygame.draw.circle(self.screen, gc, (badge_cx, badge_cy), 14)
                pygame.draw.circle(self.screen, (255, 255, 255), (badge_cx, badge_cy), 14, 2)
                init = guild["name"][0] if guild["name"] else "G"
                init_sf = get_font(14, bold=True).render(init, True, (255, 255, 255))
                self.screen.blit(init_sf, init_sf.get_rect(center=(badge_cx, badge_cy)))

                gname = get_font(14, bold=True).render(guild["name"], True, TEXT_WHITE)
                self.screen.blit(gname, (lx + 46, y + 8))
                motto = get_font(10).render(f'"{guild["motto"]}"', True, TEXT_GRAY)
                self.screen.blit(motto, (lx + 46, y + 26))

                # Role badge
                role_color = NEON_YELLOW if player.guild_role == "leader" else NEON_CYAN
                role_label = "LEADER" if player.guild_role == "leader" else "MEMBER"
                draw_badge(self.screen, lx + w - 60, y + 8, role_label, role_color, 9)

                # Stats row
                stats_y = y + 46
                members = guild.get("members", 1)
                level = guild.get("level", 1)
                m_font = get_font(10)
                m1 = m_font.render(f"Members: {members}", True, TEXT_GRAY)
                surf = self.screen
                surf.blit(m1, (lx + 10, stats_y))
                m2 = m_font.render(f"Guild Level: {level}", True, TEXT_GRAY)
                surf.blit(m2, (lx + 10, stats_y + 16))
                m3 = m_font.render(f"Contributed: {player.guild_contribution:.0f}c", True, NEON_GREEN)
                surf.blit(m3, (lx + 10, stats_y + 32))

                bonus_txt = get_font(10).render(
                    f"Income +{guild['bonus_income']*100:.0f}%  |  "
                    f"Season XP +{guild['bonus_xp']*100:.0f}%", True, NEON_GREEN)
                self.screen.blit(bonus_txt, (lx + 10, y + 100))

                # Leave button
                leave_btn = pygame.Rect(lx + w - 70, y + 96, 60, 20)
                leave_hover = leave_btn.collidepoint(mx_m, my_m)
                lc = TEXT_RED if leave_hover else (120, 60, 60)
                pygame.draw.rect(self.screen, lc, leave_btn, border_radius=4)
                lt = get_font(9).render("LEAVE", True, TEXT_WHITE)
                self.screen.blit(lt, lt.get_rect(center=leave_btn.center))
                self._buttons.append((leave_btn, "guild_leave", ""))

                y += info_h + 8

                # Donate button
                donate_btn = pygame.Rect(lx, y, w, 32)
                dh = donate_btn.collidepoint(mx_m, my_m)
                dc = BTN_BUY_H if dh else BTN_BUY
                pygame.draw.rect(self.screen, dc, donate_btn, border_radius=6)
                pygame.draw.rect(self.screen, NEON_YELLOW, donate_btn, 1, border_radius=6)
                donate_amt = min(player.coins * 0.1, 100)
                dt_txt = get_font(11, bold=True).render(
                    f"DONATE {donate_amt:.0f}c TO GUILD", True, TEXT_WHITE)
                self.screen.blit(dt_txt, dt_txt.get_rect(center=donate_btn.center))
                self._buttons.append((donate_btn, "guild_donate", ""))
                y += 40

                # Guild Network Activity (simulated)
                draw_separator(self.screen, lx, y, w)
                y += 8
                act_title = get_font(12, bold=True).render("NETWORK ACTIVITY", True, NEON_CYAN)
                self.screen.blit(act_title, (lx, y))
                y += 18

                activities = [
                    ("Chef_Mike joined the guild", "2m ago"),
                    (f"Guild earned +{random.randint(10,50)}c bonus", "5m ago"),
                    ("New perk unlocked!", "12m ago"),
                ]
                for act_text, act_time in activities:
                    act_h = 28
                    act_rect = pygame.Rect(lx, y, w, act_h)
                    pygame.draw.rect(self.screen, BG_CARD, act_rect, border_radius=4)
                    dot_c = NEON_GREEN
                    pygame.draw.circle(self.screen, dot_c, (lx + 10, y + act_h // 2), 3)
                    self.screen.blit(get_font(9).render(act_text, True, TEXT_WHITE),
                                     (lx + 20, y + 4))
                    time_sf = get_font(8).render(act_time, True, TEXT_DIM)
                    self.screen.blit(time_sf, (lx + w - time_sf.get_width() - 6, y + 6))
                    y += act_h + 2
                y += 8

        else:
            # ── NOT IN A GUILD ──

            # Create Guild section
            if self._guild_creating:
                create_h = 170
                cr_rect = pygame.Rect(lx, y, w, create_h)
                pygame.draw.rect(self.screen, BG_CARD, cr_rect, border_radius=10)
                pygame.draw.rect(self.screen, NEON_YELLOW, cr_rect, 2, border_radius=10)
                draw_pixel_corners(self.screen, cr_rect, NEON_YELLOW, 3)

                ct_label = get_font(13, bold=True).render("CREATE YOUR GUILD", True, NEON_YELLOW)
                self.screen.blit(ct_label, (lx + 10, y + 8))

                # Name input field
                name_y = y + 30
                name_rect = pygame.Rect(lx + 10, name_y, w - 20, 26)
                pygame.draw.rect(self.screen, (50, 50, 50), name_rect, border_radius=4)
                blink = int(self.glow_t * 2) % 2 == 0
                border_c = NEON_CYAN if blink else BORDER_LIGHT
                pygame.draw.rect(self.screen, border_c, name_rect, 1, border_radius=4)
                display_name = self._guild_name_input
                if not display_name:
                    display_name = "Type guild name..."
                    name_color = TEXT_DIM
                else:
                    name_color = TEXT_WHITE
                cursor = "|" if blink and self._guild_name_input else ""
                name_sf = get_font(11).render(display_name + cursor, True, name_color)
                self.screen.blit(name_sf, (lx + 16, name_y + 5))

                # Color selection
                color_y = y + 62
                cl = get_font(10).render("Choose color:", True, TEXT_GRAY)
                self.screen.blit(cl, (lx + 10, color_y))
                color_y += 16
                csize = 20
                cpad = 4
                for ci, cc in enumerate(GUILD_COLORS):
                    cx = lx + 10 + ci * (csize + cpad)
                    cy = color_y
                    if cx + csize > lx + w - 10:
                        break
                    cr = pygame.Rect(cx, cy, csize, csize)
                    pygame.draw.rect(self.screen, cc, cr, border_radius=4)
                    if ci == self._guild_color_idx:
                        pygame.draw.rect(self.screen, (255, 255, 255), cr, 2, border_radius=4)
                    self._buttons.append((cr, "guild_color_pick", str(ci)))

                # Cost display
                cost_y = y + 104
                cost_txt = get_font(10).render(
                    f"Cost: {_GUILD_CREATE_COST}c", True,
                    NEON_GREEN if player.coins >= _GUILD_CREATE_COST else TEXT_RED)
                self.screen.blit(cost_txt, (lx + 10, cost_y))

                # Create button
                btn_y = y + 122
                can_create = (len(self._guild_name_input.strip()) >= 2
                              and player.coins >= _GUILD_CREATE_COST)
                cr_btn = pygame.Rect(lx + 10, btn_y, w // 2 - 20, 28)
                cr_hover = cr_btn.collidepoint(mx_m, my_m)
                if can_create:
                    bc = BTN_BUY_H if cr_hover else BTN_BUY
                else:
                    bc = BTN_DISABLED
                pygame.draw.rect(self.screen, bc, cr_btn, border_radius=6)
                pygame.draw.rect(self.screen, NEON_YELLOW, cr_btn, 1, border_radius=6)
                ct = get_font(11, bold=True).render("CREATE", True,
                                                    TEXT_WHITE if can_create else BTN_DIS_TXT)
                self.screen.blit(ct, ct.get_rect(center=cr_btn.center))
                if can_create:
                    self._buttons.append((cr_btn, "guild_create_confirm", ""))

                # Cancel button
                cancel_btn = pygame.Rect(lx + w // 2, btn_y, w // 2 - 10, 28)
                cancel_h = cancel_btn.collidepoint(mx_m, my_m)
                pygame.draw.rect(self.screen, TEXT_RED if cancel_h else (100, 50, 50),
                                 cancel_btn, border_radius=6)
                cl_t = get_font(11, bold=True).render("CANCEL", True, TEXT_WHITE)
                self.screen.blit(cl_t, cl_t.get_rect(center=cancel_btn.center))
                self._buttons.append((cancel_btn, "guild_toggle_create", ""))

                y += create_h + 8

            else:
                # CREATE GUILD button (collapsed)
                create_btn_h = 44
                create_rect = pygame.Rect(lx, y, w, create_btn_h)
                ch = create_rect.collidepoint(mx_m, my_m)
                draw_card(self.screen, lx, y, w, create_btn_h, hover=ch,
                          accent_color=NEON_YELLOW, glow_t=self.glow_t)
                self.screen.blit(icons.get_scaled("crown", 16), (lx + 10, y + 6))
                crt = get_font(13, bold=True).render("+ CREATE GUILD", True, NEON_YELLOW)
                self.screen.blit(crt, (lx + 34, y + 6))
                cost_sub = get_font(10).render(
                    f"Build your own empire  |  {_GUILD_CREATE_COST}c", True, TEXT_GRAY)
                self.screen.blit(cost_sub, (lx + 34, y + 24))
                self._buttons.append((create_rect, "guild_toggle_create", ""))
                y += create_btn_h + 8

            # ── JOIN A GUILD ──
            draw_separator(self.screen, lx, y, w)
            y += 8
            join_title = get_font(13, bold=True).render("JOIN EXISTING GUILD", True, NEON_CYAN)
            self.screen.blit(join_title, (lx, y))
            y += 20

            for guild in GUILDS:
                card_h = 72
                card_rect = pygame.Rect(lx, y, w, card_h)
                hovered = card_rect.collidepoint(mx_m, my_m)
                gc = guild["color"]
                draw_card(self.screen, lx, y, w, card_h, hover=hovered,
                          accent_color=gc, glow_t=self.glow_t)

                # Guild badge circle
                badge_cx = lx + 22
                badge_cy = y + 20
                pygame.draw.circle(self.screen, gc, (badge_cx, badge_cy), 12)
                pygame.draw.circle(self.screen, (255, 255, 255), (badge_cx, badge_cy), 12, 1)
                init = guild["name"][0] if guild["name"] else "G"
                init_sf = get_font(11, bold=True).render(init, True, (255, 255, 255))
                self.screen.blit(init_sf, init_sf.get_rect(center=(badge_cx, badge_cy)))

                gn = get_font(12, bold=True).render(guild["name"], True, TEXT_WHITE)
                self.screen.blit(gn, (lx + 40, y + 4))
                gm = get_font(9).render(f'"{guild["motto"]}"', True, TEXT_GRAY)
                self.screen.blit(gm, (lx + 40, y + 20))

                members = guild.get("members", 0)
                level = guild.get("level", 1)
                stats = f"Lv{level}  |  {members} members"
                if guild.get("created_by") == "player":
                    stats += "  |  Player Guild"
                self.screen.blit(get_font(9).render(stats, True, TEXT_DIM), (lx + 40, y + 34))

                bonus = get_font(9).render(
                    f"Income +{guild['bonus_income']*100:.0f}%  |  "
                    f"XP +{guild['bonus_xp']*100:.0f}%", True, NEON_GREEN)
                self.screen.blit(bonus, (lx + 40, y + 48))

                # Join button
                jbtn = pygame.Rect(lx + w - 56, y + 40, 48, 22)
                jh = jbtn.collidepoint(mx_m, my_m)
                jc = BTN_BUY_H if jh else BTN_BUY
                pygame.draw.rect(self.screen, jc, jbtn, border_radius=5)
                pygame.draw.rect(self.screen, gc, jbtn, 1, border_radius=5)
                jt = get_font(9, bold=True).render("JOIN", True, TEXT_WHITE)
                self.screen.blit(jt, jt.get_rect(center=jbtn.center))
                self._buttons.append((jbtn, "guild_join", guild["id"]))
                y += card_h + 4

        # Guild perks section
        y += 8
        draw_separator(self.screen, lx, y, w)
        y += 8
        perks_title = get_font(13, bold=True).render("GUILD PERKS", True, NEON_CYAN)
        self.screen.blit(perks_title, (lx, y))
        y += 20

        for perk in GUILD_PERKS:
            card_h = 44
            card_rect = pygame.Rect(lx, y, w, card_h)
            has_guild = bool(player.guild_id)
            draw_card(self.screen, lx, y, w, card_h,
                      accent_color=NEON_CYAN, glow_t=self.glow_t)

            self.screen.blit(icons.get_scaled(perk["icon"], 14), (lx + 8, y + 6))
            self.screen.blit(get_font(12, bold=True).render(perk["name"], True, TEXT_WHITE),
                             (lx + 28, y + 4))
            draw_badge(self.screen, lx + w - 46, y + 4,
                       f"Lv{perk['level']}", (60, 100, 140), 9)
            self.screen.blit(get_font(10).render(perk["desc"], True, TEXT_GRAY),
                             (lx + 28, y + 22))
            if not has_guild:
                draw_locked_overlay(self.screen, card_rect, "JOIN GUILD", self.glow_t)
            y += card_h + 4

        y += 20
        self._max_scroll[Tab.GUILD] = max(0, y + scroll - CONTENT_Y - CONTENT_H + 20)
        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  EVENTS / SEASON SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_events(self, player, economy):
        area = pygame.Rect(PANEL_X, CONTENT_Y, PANEL_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        scroll = self._scroll[Tab.SEASON]
        margin = 10
        lx = PANEL_X + margin
        w = PANEL_W - margin * 2
        y = CONTENT_Y + 8 - scroll
        mx_m, my_m = pygame.mouse.get_pos()

        # Header
        star_ico = icons.get_scaled("star", 16)
        self.screen.blit(star_ico, (lx, y))
        title = get_font(16, bold=True).render("SEASON", True, NEON_YELLOW)
        self.screen.blit(title, (lx + 20, y))
        pts_lbl = get_font(11).render(f"{player.season_points:,} pts", True, NEON_GREEN)
        self.screen.blit(pts_lbl, (lx + w - pts_lbl.get_width(), y + 4))
        y += 24

        # Season Banner
        season_h = 70
        season_rect = pygame.Rect(lx, y, w, season_h)
        pygame.draw.rect(self.screen, BG_CARD, season_rect, border_radius=8)
        pygame.draw.rect(self.screen, NEON_YELLOW, season_rect, 2, border_radius=8)
        draw_pixel_corners(self.screen, season_rect, NEON_YELLOW, 3)

        self.screen.blit(icons.get_scaled("trophy", 16), (lx + 10, y + 8))
        s_title = f"Season {SEASON_NUMBER}: {SEASON_NAME}"
        season_title = get_font(13, bold=True).render(s_title, True, TEXT_WHITE)
        self.screen.blit(season_title, (lx + 30, y + 6))
        days, hours = get_season_time_remaining()
        timer_txt = get_font(11).render(f"Ends in: {days}d {hours}h", True, NEON_YELLOW)
        self.screen.blit(timer_txt, (lx + 30, y + 24))
        progress = get_season_progress(player)
        draw_progress_bar(self.screen, lx + 30, y + 42, w - 50, 10,
                          progress, color=NEON_YELLOW, show_shimmer=True, glow_t=self.glow_t)
        pct_lbl = get_font(10).render(f"{int(progress * 100)}%", True, TEXT_GRAY)
        self.screen.blit(pct_lbl, (lx + 30, y + 54))
        y += season_h + 12

        # Active Events
        events_title = get_font(13, bold=True).render("ACTIVE EVENTS", True, NEON_CYAN)
        self.screen.blit(events_title, (lx, y))
        y += 18

        if economy.last_event_name and economy.event_display_timer > 0:
            ev_h = 44
            draw_card(self.screen, lx, y, w, ev_h,
                      accent_color=economy.last_event_color, glow_t=self.glow_t)
            self.screen.blit(icons.get_scaled("star", 14), (lx + 8, y + 6))
            ev_name = get_font(12, bold=True).render(economy.last_event_name, True,
                                                      economy.last_event_color)
            self.screen.blit(ev_name, (lx + 26, y + 6))
            timer_s = f"{economy.event_display_timer:.1f}s remaining"
            ev_desc = get_font(10).render(timer_s, True, TEXT_GRAY)
            self.screen.blit(ev_desc, (lx + 26, y + 24))
            y += ev_h + 6
        else:
            no_ev = get_font(11).render("No active events — keep playing!", True, TEXT_DIM)
            self.screen.blit(no_ev, (lx, y))
            y += 18

        # Incoming sabotage debuff
        if player.incoming_sabotage and player.incoming_sabotage["timer"] > 0:
            sab_h = 36
            draw_card(self.screen, lx, y, w, sab_h,
                      accent_color=TEXT_RED, glow_t=self.glow_t)
            self.screen.blit(icons.get_scaled("fire", 14), (lx + 8, y + 4))
            sab_txt = get_font(11, bold=True).render(
                f"SABOTAGED! {player.incoming_sabotage['timer']:.0f}s",
                True, TEXT_RED)
            self.screen.blit(sab_txt, (lx + 26, y + 6))
            y += sab_h + 6

        # Season Rewards
        y += 6
        rewards_title = get_font(13, bold=True).render("REWARDS", True, NEON_YELLOW)
        self.screen.blit(rewards_title, (lx, y))
        y += 18

        for r in SEASON_REWARDS:
            rh = 48
            r_rect = draw_card(self.screen, lx, y, w, rh,
                               accent_color=r["color"], glow_t=self.glow_t)
            self.screen.blit(icons.get_scaled(r["icon"], 14), (lx + 8, y + 6))
            tier_txt = get_font(12, bold=True).render(r["tier"], True, r["color"])
            self.screen.blit(tier_txt, (lx + 26, y + 4))
            pts_txt = get_font(10).render(f"{r['pts']:,}pts", True, TEXT_GRAY)
            self.screen.blit(pts_txt, (lx + 26 + tier_txt.get_width() + 6, y + 6))

            # Reward description
            reward_desc = f"+{r['reward_coins']}c"
            if r["reward_worker"]:
                reward_desc += f" + {r['reward_worker'].title()} worker"
            reward_txt = get_font(10).render(reward_desc, True, TEXT_WHITE)
            self.screen.blit(reward_txt, (lx + 26, y + 22))

            claimed = r["tier"] in player.season_rewards_claimed
            can_claim = player.season_points >= r["pts"] and not claimed

            if claimed:
                done_txt = get_font(10, bold=True).render("CLAIMED", True, NEON_GREEN)
                self.screen.blit(done_txt, (lx + w - 60, y + 6))
            elif can_claim:
                claim_btn = pygame.Rect(lx + w - 62, y + 22, 54, 20)
                ch = claim_btn.collidepoint(mx_m, my_m)
                cc = BTN_BUY_H if ch else BTN_BUY
                pygame.draw.rect(self.screen, cc, claim_btn, border_radius=4)
                pygame.draw.rect(self.screen, r["color"], claim_btn, 1, border_radius=4)
                ct = get_font(9, bold=True).render("CLAIM", True, TEXT_WHITE)
                self.screen.blit(ct, ct.get_rect(center=claim_btn.center))
                self._buttons.append((claim_btn, "season_claim", r["tier"]))
            else:
                # Show progress toward this tier
                tier_pct = min(1.0, player.season_points / r["pts"])
                draw_progress_bar(self.screen, lx + 26, y + 36, w - 100, 6,
                                  tier_pct, color=r["color"], glow_t=self.glow_t)
                need = get_font(9).render(
                    f"{player.season_points}/{r['pts']}", True, TEXT_DIM)
                self.screen.blit(need, (lx + w - 60, y + 32))

            y += rh + 4

        # Mini leaderboard hint
        y += 8
        lb_rect = pygame.Rect(lx, y, w, 40)
        pygame.draw.rect(self.screen, BG_CARD, lb_rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER_LIGHT, lb_rect, 1, border_radius=6)
        lb_hint = get_font(11).render(
            "Full leaderboard in top bar!", True, TEXT_GRAY)
        self.screen.blit(lb_hint, lb_hint.get_rect(center=lb_rect.center))

        y += 52
        self._max_scroll[Tab.SEASON] = max(0, y + scroll - CONTENT_Y - CONTENT_H + 20)
        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  EVENT POPUP (over restaurant)
    # ═══════════════════════════════════════════════════════════
    def _draw_event_popup(self, economy, rest_rect):
        """Draw event announcement over the restaurant area."""
        center_x = rest_rect.centerx
        ev_font = get_font(18, bold=True)
        name_txt = ev_font.render(economy.last_event_name, True,
                                  economy.last_event_color)
        tw = name_txt.get_width() + 40
        th = name_txt.get_height() + 12
        text_y = rest_rect.bottom - 50
        rx = center_x - tw // 2
        rect = pygame.Rect(rx, text_y, tw, th)
        bg = pygame.Surface((tw, th), pygame.SRCALPHA)
        alpha = int(180 + 40 * math.sin(self.glow_t * 4))
        bg.fill((255, 255, 255, max(0, min(255, alpha))))
        self.screen.blit(bg, rect.topleft)
        pygame.draw.rect(self.screen, economy.last_event_color,
                         rect, 2, border_radius=6)
        star_ico = icons.get_scaled("star", 14)
        self.screen.blit(star_ico, (rx + 6, text_y + 5))
        self.screen.blit(name_txt, (rx + 22, text_y + 6))
        self.screen.blit(star_ico, (rx + 24 + name_txt.get_width(), text_y + 5))

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
from economy import Economy
from worker import Worker, hire_cost, roll_rarity, RARITIES
from upgrades import (
    UPGRADE_DEFS, UPGRADES_BY_ID, get_upgrade_level,
    upgrade_cost, can_buy, buy_upgrade,
    get_hire_cost_discount, get_worker_upgrade_discount,
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
)
import icons
from ui_components import (
    get_font, draw_card, draw_button, draw_progress_bar,
    draw_badge, draw_separator, draw_section_header, draw_stat_row,
    draw_panel_bg, draw_glow_border, draw_icon_button,
    draw_coins_display, draw_locked_overlay,
)

# ── Layout constants ─────────────────────────────────────────
SCREEN_W, SCREEN_H = 960, 720
TOP_BAR_H = 48
BOT_NAV_H = 58
CONTENT_Y = TOP_BAR_H
CONTENT_H = SCREEN_H - TOP_BAR_H - BOT_NAV_H  # 614


class Tab(IntEnum):
    HOME = 0
    WORKERS = 1
    UPGRADES = 2
    SABOTAGE = 3
    GUILD = 4
    EVENTS = 5


TAB_INFO = [
    {"name": "Home",     "icon": "burger"},
    {"name": "Workers",  "icon": "person"},
    {"name": "Upgrades", "icon": "arrow_up"},
    {"name": "Sabotage", "icon": "fire"},
    {"name": "Guild",    "icon": "crown"},
    {"name": "Events",   "icon": "star"},
]

# Upgrade sub-tabs
UPGRADE_TABS = ["Kitchen", "Design", "Business"]
UPGRADE_TAB_COLORS = {
    "Kitchen":  ((180, 60, 60),  (220, 80, 80)),
    "Design":   ((60, 140, 200), (80, 170, 240)),
    "Business": ((120, 60, 180), (160, 90, 220)),
}

# Sabotage attack definitions (placeholder)
SABOTAGE_ATTACKS = [
    {"id": "spy",     "name": "Spy Mission",      "icon": "chef_hat",
     "desc": "Peek at a rival's income for 30s", "cooldown": 120,
     "cost": 500, "unlock_level": 3},
    {"id": "rats",    "name": "Rodent Raid",       "icon": "speed",
     "desc": "Slow a rival's kitchen by 20% for 60s", "cooldown": 300,
     "cost": 1200, "unlock_level": 5},
    {"id": "critic",  "name": "Food Critic Trap",  "icon": "star",
     "desc": "Send a harsh critic — rival loses attractiveness", "cooldown": 600,
     "cost": 2500, "unlock_level": 8},
    {"id": "blackout","name": "Kitchen Blackout",   "icon": "snowflake",
     "desc": "Shut down rival's grill for 30s", "cooldown": 900,
     "cost": 5000, "unlock_level": 12},
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
        self.active_tab: Tab = Tab.HOME
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
                    (255, 215, 70), (255, 200, 50), (255, 180, 40),
                    (80, 230, 120), (255, 255, 200),
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
                sub_w = SCREEN_W // len(UPGRADE_TABS)
                for i in range(len(UPGRADE_TABS)):
                    sub_rect = pygame.Rect(i * sub_w, sub_y, sub_w, 28)
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

        # Scroll
        if event.type == pygame.MOUSEWHEEL:
            tab = self.active_tab
            ms = self._max_scroll.get(tab, 0)
            self._scroll[tab] = max(0, min(ms,
                                           self._scroll[tab] - event.y * 35))

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "exit_to_menu"
            if event.key == pygame.K_l:
                return "toggle_leaderboard"
            # Number keys switch tabs
            if pygame.K_1 <= event.key <= pygame.K_6:
                self.active_tab = Tab(event.key - pygame.K_1)
                return None

        return None

    # ── Draw ─────────────────────────────────────────────────
    def draw(self, player: Player, economy: Economy,
             ips: float, restaurant=None):
        """Draw the complete game screen."""
        self._buttons.clear()

        # Background
        self.screen.fill(BG_DARK)

        # Content area
        content_rect = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)
        if self.active_tab == Tab.HOME:
            self._draw_home(player, economy, ips, restaurant)
        elif self.active_tab == Tab.WORKERS:
            self._draw_workers(player)
        elif self.active_tab == Tab.UPGRADES:
            self._draw_upgrades(player)
        elif self.active_tab == Tab.SABOTAGE:
            self._draw_sabotage(player)
        elif self.active_tab == Tab.GUILD:
            self._draw_guild(player)
        elif self.active_tab == Tab.EVENTS:
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

    # ═══════════════════════════════════════════════════════════
    #  TOP BAR
    # ═══════════════════════════════════════════════════════════
    def _draw_top_bar(self, player: Player, ips: float):
        bar_rect = pygame.Rect(0, 0, SCREEN_W, TOP_BAR_H)
        pygame.draw.rect(self.screen, BG_PANEL, bar_rect)
        # Bottom glow line
        glow_a = int(30 + 15 * math.sin(self.glow_t * 2))
        gs = pygame.Surface((SCREEN_W, 2), pygame.SRCALPHA)
        gs.fill((*ACCENT[:3], max(0, glow_a)))
        self.screen.blit(gs, (0, TOP_BAR_H - 2))

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
        # Coin icon + amount
        self.screen.blit(icons.get("coin"), (x, 14))
        font_coins = get_font(22, bold=True)
        ct = font_coins.render(f"{self._display_coins:,.0f}", True, TEXT_GOLD)
        self.screen.blit(ct, (x + 20, 12))
        x += 28 + ct.get_width()

        # Divider
        pygame.draw.rect(self.screen, BORDER, (x, 8, 1, 32))
        x += 10

        # Income/s
        font_sm = get_font(13)
        self.screen.blit(icons.get_scaled("speed", 14), (x, 16))
        it = font_sm.render(f"{ips:,.1f}/s", True, TEXT_GREEN)
        self.screen.blit(it, (x + 16, 16))
        x += 20 + it.get_width()

        # Workers count
        pygame.draw.rect(self.screen, BORDER, (x, 8, 1, 32))
        x += 10
        self.screen.blit(icons.get_scaled("person", 14), (x, 16))
        wt = font_sm.render(f"{len(player.workers)}", True, TEXT_CYAN)
        self.screen.blit(wt, (x + 16, 16))
        x += 20 + wt.get_width()

        # Prestige level
        pygame.draw.rect(self.screen, BORDER, (x, 8, 1, 32))
        x += 10
        self.screen.blit(icons.get_scaled("prestige", 12), (x, 17))
        pt = font_sm.render(f"P{player.prestige_level} (x{player.prestige_multiplier:.1f})",
                            True, TEXT_PINK)
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
            bg_s.fill((255, 80, 50, int(30 + 20 * pulse)))
            self.screen.blit(bg_s, (bx - 4, 14))
            self.screen.blit(bt, (bx, 15))

        # Restaurant name
        if player.restaurant_name:
            name_font = get_font(11)
            nt = name_font.render(player.restaurant_name, True, TEXT_DIM)
            self.screen.blit(nt, (12, 34))

        # Action buttons (right side)
        mx, my = pygame.mouse.get_pos()
        # Leaderboard
        lb_c = (70, 120, 200) if self._btn_leaderboard.collidepoint(mx, my) else (50, 90, 160)
        pygame.draw.rect(self.screen, lb_c, self._btn_leaderboard, border_radius=4)
        lb_ico = icons.get_scaled("trophy", 14)
        lb_txt = get_font(11).render("RANK", True, TEXT_WHITE)
        lbx = self._btn_leaderboard.centerx - (14 + 4 + lb_txt.get_width()) // 2
        self.screen.blit(lb_ico, (lbx, self._btn_leaderboard.centery - 7))
        self.screen.blit(lb_txt, (lbx + 18, self._btn_leaderboard.centery - lb_txt.get_height() // 2))

        # Exit
        ex_c = (200, 70, 70) if self._btn_exit.collidepoint(mx, my) else (160, 50, 50)
        pygame.draw.rect(self.screen, ex_c, self._btn_exit, border_radius=4)
        ex_ico = icons.get_scaled("door", 14)
        ex_txt = get_font(11).render("MENU", True, TEXT_WHITE)
        exx = self._btn_exit.centerx - (14 + 4 + ex_txt.get_width()) // 2
        self.screen.blit(ex_ico, (exx, self._btn_exit.centery - 7))
        self.screen.blit(ex_txt, (exx + 18, self._btn_exit.centery - ex_txt.get_height() // 2))

    # ═══════════════════════════════════════════════════════════
    #  BOTTOM NAVIGATION
    # ═══════════════════════════════════════════════════════════
    def _draw_bottom_nav(self):
        nav_y = SCREEN_H - BOT_NAV_H
        nav_rect = pygame.Rect(0, nav_y, SCREEN_W, BOT_NAV_H)
        pygame.draw.rect(self.screen, BG_PANEL, nav_rect)
        # Top glow line
        glow_a = int(25 + 12 * math.sin(self.glow_t * 1.8))
        gs = pygame.Surface((SCREEN_W, 2), pygame.SRCALPHA)
        gs.fill((*ACCENT[:3], max(0, glow_a)))
        self.screen.blit(gs, (0, nav_y))

        tab_w = SCREEN_W // len(TAB_INFO)
        for i, info in enumerate(TAB_INFO):
            rect = self._nav_rects[i]
            active = i == self.active_tab
            draw_icon_button(self.screen, rect, info["icon"], info["name"],
                             active=active, color=BG_PANEL,
                             active_color=BG_CARD, glow_t=self.glow_t)
            # Dividers between tabs
            if i > 0:
                pygame.draw.rect(self.screen, BORDER,
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
        overlay.fill((18, 16, 24, 180))
        self.screen.blit(overlay, (ox, oy))
        pygame.draw.rect(self.screen, BORDER, (ox, oy, ow, oh), 1, border_radius=6)

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
        area = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        # Clip content
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)

        scroll = self._scroll[Tab.WORKERS]
        margin = 16
        card_w = (SCREEN_W - margin * 3) // 2  # two columns
        x_left = margin
        x_right = margin * 2 + card_w
        y = CONTENT_Y + 12 - scroll

        # ── Header ───────────────────────────────────────────
        font_title = get_font(20, bold=True)
        title = font_title.render("WORKERS", True, TEXT_GOLD)
        self.screen.blit(title, (margin, y))
        count_txt = get_font(14).render(f"{len(player.workers)} hired", True, TEXT_GRAY)
        self.screen.blit(count_txt, (margin + title.get_width() + 12, y + 4))
        y += 32

        # ── Hire card (full width, special) ──────────────────
        hire_c = hire_cost(len(player.workers)) * get_hire_cost_discount(player)
        affordable = player.coins >= hire_c

        hire_rect = draw_card(self.screen, x_left, y, SCREEN_W - margin * 2, 60,
                              special=True, glow_t=self.glow_t)
        # Content
        self.screen.blit(icons.get("person"), (x_left + 12, y + 12))
        hire_title = get_font(16, bold=True).render("Hire New Worker", True, TEXT_WHITE)
        self.screen.blit(hire_title, (x_left + 34, y + 8))
        hire_desc = get_font(12).render(
            f"Random rarity roll  |  {len(player.workers)} workers hired", True, TEXT_GRAY)
        self.screen.blit(hire_desc, (x_left + 34, y + 28))

        # Rarity chances preview
        rarity_x = x_left + 34
        rarity_y = y + 42
        for rname, rdata in RARITIES.items():
            w_pct = get_font(10).render(f"{rname[0].upper()}{rdata['weight']:.0f}%", True,
                                        rdata["color"])
            self.screen.blit(w_pct, (rarity_x, rarity_y))
            rarity_x += w_pct.get_width() + 8

        # Hire button
        btn_rect = pygame.Rect(SCREEN_W - margin - 150, y + 14, 130, 32)
        draw_button(self.screen, btn_rect, f"HIRE  {hire_c:,.0f}c", affordable,
                    color=BTN_PRIMARY, hover_color=BTN_PRIMARY_H, font_size=14)
        if affordable:
            self._buttons.append((btn_rect, "hire", "new"))

        y += 72
        draw_separator(self.screen, x_left, y, SCREEN_W - margin * 2)
        y += 10

        # ── Worker cards (2 columns) ─────────────────────────
        from sprites import WorkySpriteRenderer
        col = 0
        for i, wk in enumerate(player.workers):
            x = x_left if col == 0 else x_right
            card_h = 90
            card_rect = pygame.Rect(x, y if col == 0 else y, card_w, card_h)
            mx, my_m = pygame.mouse.get_pos()
            hovered = card_rect.collidepoint(mx, my_m)

            rarity_col = RARITIES[wk.rarity]["color"]
            draw_card(self.screen, x, card_rect.y, card_w, card_h,
                      hover=hovered, accent_color=rarity_col, glow_t=self.glow_t)

            # Worker sprite
            spr = WorkySpriteRenderer(wk.archetype, RARITIES[wk.rarity]["color"], wk.skin_tone)
            spr_surf = pygame.Surface((48, 60), pygame.SRCALPHA)
            spr.draw(spr_surf, 24, 30, direction="down", anim_frame=0,
                     state="idle", rarity=wk.rarity)
            self.screen.blit(spr_surf, (x + 6, card_rect.y + 14))

            # Info
            info_x = x + 58
            # Name + rarity badge
            name_str = wk.archetype.replace('_', ' ').title()
            name_txt = get_font(13, bold=True).render(name_str, True, TEXT_WHITE)
            self.screen.blit(name_txt, (info_x, card_rect.y + 6))
            bw = draw_badge(self.screen, info_x + name_txt.get_width() + 6,
                            card_rect.y + 7, wk.rarity.upper(), rarity_col, 9)

            # Level
            lvl_txt = get_font(12).render(f"Level {wk.level}", True, TEXT_CYAN)
            self.screen.blit(lvl_txt, (info_x, card_rect.y + 22))

            # Stats
            stats_font = get_font(11)
            st1 = stats_font.render(f"SPD {wk.speed:.1f}", True, TEXT_GREEN)
            st2 = stats_font.render(f"EFF {wk.efficiency:.1f}", True, TEXT_PINK)
            st3 = stats_font.render(f"{wk.get_income():.1f}/s", True, TEXT_GOLD)
            self.screen.blit(st1, (info_x, card_rect.y + 38))
            self.screen.blit(st2, (info_x + 70, card_rect.y + 38))
            self.screen.blit(st3, (info_x + 140, card_rect.y + 38))

            # Upgrade button
            up_cost = wk.upgrade_cost() * get_worker_upgrade_discount(player)
            can_up = player.coins >= up_cost
            btn_r = pygame.Rect(x + card_w - 120, card_rect.y + 58, 110, 24)
            draw_button(self.screen, btn_r, f"UP {up_cost:,.0f}c", can_up, font_size=11)
            if can_up:
                self._buttons.append((btn_r, "worker_up", str(i)))

            # Income bar visualization
            max_income = max(w.get_income() for w in player.workers) if player.workers else 1
            bar_pct = wk.get_income() / max_income if max_income > 0 else 0
            draw_progress_bar(self.screen, info_x, card_rect.y + 56,
                              card_w - 190, 6, bar_pct, color=rarity_col)

            col += 1
            if col >= 2:
                col = 0
                y += card_h + 8
        if col == 1:
            y += card_h + 8

        y += 20
        self._max_scroll[Tab.WORKERS] = max(0, y - CONTENT_Y - CONTENT_H + 20)
        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  UPGRADES SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_upgrades(self, player):
        area = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        # Sub-tabs
        self._draw_upgrade_tabs()

        # Content below sub-tabs
        content_y = CONTENT_Y + 36
        content_h = CONTENT_H - 36
        content_rect = pygame.Rect(0, content_y, SCREEN_W, content_h)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(content_rect)

        scroll = self._scroll[Tab.UPGRADES]
        margin = 16
        y = content_y + 8 - scroll

        if self._upgrade_tab == 0:
            y = self._draw_upgrade_items(player, y, margin, "Kitchen", KITCHEN_ITEMS,
                                          "Production")
        elif self._upgrade_tab == 1:
            y = self._draw_design_upgrades(player, y, margin)
        elif self._upgrade_tab == 2:
            y = self._draw_upgrade_items(player, y, margin, "Business", BUSINESS_ITEMS,
                                          "Sales|Automation")

        # Prestige section at bottom
        y += 16
        y = self._draw_prestige_section(player, y, margin)

        self._max_scroll[Tab.UPGRADES] = max(0, y - content_y - content_h + 20)
        self.screen.set_clip(prev_clip)

    def _draw_upgrade_tabs(self):
        sub_y = CONTENT_Y + 4
        sub_w = SCREEN_W // len(UPGRADE_TABS)
        for i, name in enumerate(UPGRADE_TABS):
            rect = pygame.Rect(i * sub_w, sub_y, sub_w, 28)
            active = i == self._upgrade_tab
            colors = UPGRADE_TAB_COLORS[name]
            if active:
                pygame.draw.rect(self.screen, colors[0], rect)
                pygame.draw.rect(self.screen, colors[1],
                                 (rect.x, rect.bottom - 3, rect.width, 3))
            else:
                mx, my = pygame.mouse.get_pos()
                c = (45, 42, 60) if rect.collidepoint(mx, my) else (35, 32, 48)
                pygame.draw.rect(self.screen, c, rect)

            ico = icons.get_scaled(icons.TAB_ICONS.get(name, "arrow_up"), 12)
            txt = get_font(12).render(name, True,
                                       TEXT_WHITE if active else TEXT_GRAY)
            total_w = 12 + 4 + txt.get_width()
            ix = rect.centerx - total_w // 2
            self.screen.blit(ico, (ix, rect.centery - 6))
            self.screen.blit(txt, (ix + 16, rect.centery - txt.get_height() // 2))

    def _draw_upgrade_items(self, player, y, margin, section_name, items, upgrade_cats):
        """Draw upgrade category items. Returns new y."""
        w = SCREEN_W - margin * 2
        x = margin

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
        w = SCREEN_W - margin * 2
        x = margin

        # ── Attractiveness header ────────────────────────────
        attract = get_attractiveness(player)
        header_h = 70
        if attract >= 80:
            hdr_bg, hdr_border = (40, 42, 25), TEXT_GOLD
        elif attract >= 50:
            hdr_bg, hdr_border = (25, 42, 35), TEXT_GREEN
        else:
            hdr_bg, hdr_border = (30, 30, 45), TEXT_CYAN
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
        pygame.draw.rect(self.screen, (35, 50, 70), seats_rect, border_radius=4)
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

    def _draw_prestige_section(self, player, y, margin):
        """Draw prestige button section."""
        w = SCREEN_W - margin * 2
        x = margin
        rect = pygame.Rect(x, y, w, 50)
        bonus = player.get_prestige_bonus()
        can_prestige = bonus >= 0.01

        if can_prestige:
            pulse = int(15 * math.sin(self.glow_t * 3))
            color = (180 + pulse, 100, 50)
        else:
            color = BTN_DISABLED

        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my) and can_prestige
        c = (220 + (pulse if can_prestige else 0), 130, 60) if hovered else color
        pygame.draw.rect(self.screen, c, rect, border_radius=6)
        bc = ACCENT if can_prestige else BORDER
        pygame.draw.rect(self.screen, bc, rect, 2, border_radius=6)

        ico = icons.get("prestige")
        label = f"PRESTIGE  (+{bonus:.2f}x multiplier)"
        txt = get_font(16, bold=True).render(label, True, TEXT_WHITE)
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
        area = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        margin = 16
        w = SCREEN_W - margin * 2
        y = CONTENT_Y + 12

        # Header with fire icon
        fire_ico = icons.get_scaled("fire", 20)
        self.screen.blit(fire_ico, (margin, y))
        title = get_font(22, bold=True).render("SABOTAGE", True, TEXT_RED)
        self.screen.blit(title, (margin + 26, y - 2))
        subtitle = get_font(12).render("Disrupt rival restaurants to gain the edge!",
                                       True, TEXT_GRAY)
        self.screen.blit(subtitle, (margin, y + 24))
        y += 48

        # Attack cards
        for atk in SABOTAGE_ATTACKS:
            card_h = 90
            mx_m, my_m = pygame.mouse.get_pos()
            card_rect = pygame.Rect(margin, y, w, card_h)
            hovered = card_rect.collidepoint(mx_m, my_m)

            draw_card(self.screen, margin, y, w, card_h, hover=hovered,
                      accent_color=TEXT_RED, glow_t=self.glow_t)

            # Icon
            ico = icons.get_scaled(atk["icon"], 18)
            self.screen.blit(ico, (margin + 12, y + 12))

            # Name + unlock requirement
            name_txt = get_font(16, bold=True).render(atk["name"], True, TEXT_WHITE)
            self.screen.blit(name_txt, (margin + 38, y + 8))

            # Unlock level badge
            draw_badge(self.screen, margin + 38 + name_txt.get_width() + 8,
                       y + 10, f"LV{atk['unlock_level']}+", (100, 60, 60), 10)

            # Description
            desc = get_font(12).render(atk["desc"], True, TEXT_GRAY)
            self.screen.blit(desc, (margin + 38, y + 28))

            # Cost + cooldown
            cost_txt = get_font(11).render(f"Cost: {atk['cost']:,}c", True, TEXT_GOLD)
            cd_txt = get_font(11).render(f"Cooldown: {atk['cooldown']}s", True, TEXT_DIM)
            self.screen.blit(cost_txt, (margin + 38, y + 46))
            self.screen.blit(cd_txt, (margin + 38 + cost_txt.get_width() + 16, y + 46))

            # "Coming Soon" overlay
            draw_locked_overlay(self.screen, card_rect, "COMING SOON", self.glow_t)

            y += card_h + 8

        # Info box at bottom
        y += 8
        info_rect = pygame.Rect(margin, y, w, 60)
        pygame.draw.rect(self.screen, (30, 25, 40), info_rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, info_rect, 1, border_radius=6)
        info_icon = icons.get_scaled("sparkle", 16)
        self.screen.blit(info_icon, (margin + 12, y + 10))
        info_t1 = get_font(13, bold=True).render("PvP Sabotage System", True, TEXT_PINK)
        self.screen.blit(info_t1, (margin + 34, y + 8))
        info_t2 = get_font(11).render(
            "Attack rival burger joints! Steal customers, sabotage kitchens,",
            True, TEXT_GRAY)
        info_t3 = get_font(11).render(
            "and hire food critics. Defend your own restaurant with upgrades!",
            True, TEXT_GRAY)
        self.screen.blit(info_t2, (margin + 34, y + 26))
        self.screen.blit(info_t3, (margin + 34, y + 40))

        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  GUILD SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_guild(self, player):
        area = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        margin = 16
        w = SCREEN_W - margin * 2
        y = CONTENT_Y + 12

        # Header
        crown_ico = icons.get_scaled("crown", 20)
        self.screen.blit(crown_ico, (margin, y))
        title = get_font(22, bold=True).render("GUILD", True, TEXT_GOLD)
        self.screen.blit(title, (margin + 26, y - 2))
        subtitle = get_font(12).render(
            "Join forces with other burger chefs for shared bonuses!",
            True, TEXT_GRAY)
        self.screen.blit(subtitle, (margin, y + 24))
        y += 48

        # Guild creation / join section
        join_h = 100
        join_rect = pygame.Rect(margin, y, w, join_h)
        pygame.draw.rect(self.screen, BG_CARD, join_rect, border_radius=8)
        pygame.draw.rect(self.screen, TEXT_GOLD, join_rect, 2, border_radius=8)

        # Animated glow
        glow_a = int(15 + 10 * math.sin(self.glow_t * 1.5))
        gs = pygame.Surface((w, join_h), pygame.SRCALPHA)
        gs.fill((*TEXT_GOLD[:3], max(0, glow_a)))
        self.screen.blit(gs, (margin, y))

        self.screen.blit(icons.get_scaled("building", 22), (margin + 16, y + 16))
        create_title = get_font(18, bold=True).render("Create or Join a Guild", True, TEXT_WHITE)
        self.screen.blit(create_title, (margin + 46, y + 14))
        create_desc = get_font(12).render(
            "Team up with other players for bonus income, shared upgrades,",
            True, TEXT_GRAY)
        create_desc2 = get_font(12).render(
            "and exclusive guild-only recipes and decorations!", True, TEXT_GRAY)
        self.screen.blit(create_desc, (margin + 46, y + 38))
        self.screen.blit(create_desc2, (margin + 46, y + 54))

        # Coming soon overlay on the create section
        draw_locked_overlay(self.screen, join_rect, "COMING SOON", self.glow_t)
        y += join_h + 16

        # Guild perks preview
        perks_title = get_font(16, bold=True).render("Guild Perks Preview", True, TEXT_CYAN)
        self.screen.blit(perks_title, (margin, y))
        y += 24

        # Perk cards (2 columns)
        perk_w = (w - margin) // 2
        for i, perk in enumerate(GUILD_PERKS):
            col = i % 2
            px = margin if col == 0 else margin + perk_w + margin
            row = i // 2
            py = y + row * 74

            card_h = 66
            card_rect = pygame.Rect(px, py, perk_w, card_h)
            draw_card(self.screen, px, py, perk_w, card_h,
                      accent_color=TEXT_CYAN, glow_t=self.glow_t)

            # Icon
            self.screen.blit(icons.get_scaled(perk["icon"], 16), (px + 10, py + 10))

            # Name
            self.screen.blit(get_font(13, bold=True).render(perk["name"], True, TEXT_WHITE),
                             (px + 32, py + 8))

            # Level requirement
            draw_badge(self.screen, px + perk_w - 50, py + 8,
                       f"Lv{perk['level']}", (60, 100, 140), 10)

            # Description
            self.screen.blit(get_font(11).render(perk["desc"], True, TEXT_GRAY),
                             (px + 32, py + 26))

            # Locked
            draw_locked_overlay(self.screen, card_rect, "LOCKED", self.glow_t)

        y += (len(GUILD_PERKS) + 1) // 2 * 74

        self.screen.set_clip(prev_clip)

    # ═══════════════════════════════════════════════════════════
    #  EVENTS / SEASON SCREEN
    # ═══════════════════════════════════════════════════════════
    def _draw_events(self, player, economy):
        area = pygame.Rect(0, CONTENT_Y, SCREEN_W, CONTENT_H)
        draw_panel_bg(self.screen, area, self.glow_t)

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        margin = 16
        w = SCREEN_W - margin * 2
        y = CONTENT_Y + 12

        # Header
        star_ico = icons.get_scaled("star", 20)
        self.screen.blit(star_ico, (margin, y))
        title = get_font(22, bold=True).render("EVENTS & SEASONS", True, TEXT_PINK)
        self.screen.blit(title, (margin + 26, y - 2))
        y += 32

        # ── Season Banner ────────────────────────────────────
        season_h = 90
        season_rect = pygame.Rect(margin, y, w, season_h)
        # Gradient background
        for sy in range(season_h):
            alpha = int(40 + 20 * math.sin(sy * 0.05 + self.glow_t))
            grad = pygame.Surface((w, 1), pygame.SRCALPHA)
            grad.fill((80, 50, 120, max(0, min(255, alpha))))
            self.screen.blit(grad, (margin, y + sy))
        pygame.draw.rect(self.screen, TEXT_PINK, season_rect, 2, border_radius=8)

        # Season info
        self.screen.blit(icons.get_scaled("trophy", 22), (margin + 16, y + 12))
        season_title = get_font(20, bold=True).render("Season 1: Grand Opening", True, TEXT_WHITE)
        self.screen.blit(season_title, (margin + 46, y + 10))

        # Timer (mock)
        timer_txt = get_font(14).render("Ends in: 27d 14h 32m", True, TEXT_GOLD)
        self.screen.blit(timer_txt, (margin + 46, y + 36))

        # Season progress bar
        draw_progress_bar(self.screen, margin + 46, y + 58, w - 80, 12,
                          0.35, color=TEXT_PINK, show_shimmer=True, glow_t=self.glow_t)
        pct_lbl = get_font(11).render("35% complete", True, TEXT_GRAY)
        self.screen.blit(pct_lbl, (margin + 46, y + 72))

        draw_locked_overlay(self.screen, season_rect, "COMING SOON", self.glow_t)
        y += season_h + 16

        # ── Active Events ────────────────────────────────────
        events_title = get_font(16, bold=True).render("Active Events", True, TEXT_CYAN)
        self.screen.blit(events_title, (margin, y))
        y += 24

        # Current economy event
        if economy.last_event_name:
            ev_h = 56
            ev_rect = draw_card(self.screen, margin, y, w, ev_h,
                                accent_color=economy.last_event_color, glow_t=self.glow_t)
            self.screen.blit(icons.get_scaled("star", 16), (margin + 12, y + 10))
            ev_name = get_font(14, bold=True).render(economy.last_event_name, True,
                                                      economy.last_event_color)
            self.screen.blit(ev_name, (margin + 34, y + 8))
            ev_desc = get_font(11).render("Active burger economy event!", True, TEXT_GRAY)
            self.screen.blit(ev_desc, (margin + 34, y + 28))
            y += ev_h + 8
        else:
            no_ev = get_font(13).render("No active events right now.", True, TEXT_DIM)
            self.screen.blit(no_ev, (margin, y))
            y += 20

        # ── Season Rewards Preview ───────────────────────────
        y += 8
        rewards_title = get_font(16, bold=True).render("Season Rewards Preview", True, TEXT_GOLD)
        self.screen.blit(rewards_title, (margin, y))
        y += 24

        rewards = [
            {"tier": "Bronze", "pts": 100, "reward": "50 bonus coins",
             "color": (205, 127, 50), "icon": "medal_bronze"},
            {"tier": "Silver", "pts": 500, "reward": "Uncommon worker",
             "color": (192, 192, 192), "icon": "medal_silver"},
            {"tier": "Gold",   "pts": 2000, "reward": "Rare worker + 500c",
             "color": (255, 215, 0),  "icon": "medal_gold"},
            {"tier": "Master", "pts": 10000, "reward": "Epic worker + exclusive decor",
             "color": (180, 80, 240), "icon": "star"},
        ]

        for r in rewards:
            rh = 50
            r_rect = draw_card(self.screen, margin, y, w, rh,
                               accent_color=r["color"], glow_t=self.glow_t)
            self.screen.blit(icons.get_scaled(r["icon"], 16), (margin + 12, y + 8))
            tier_txt = get_font(14, bold=True).render(r["tier"], True, r["color"])
            self.screen.blit(tier_txt, (margin + 34, y + 6))
            pts_txt = get_font(11).render(f"{r['pts']:,} pts", True, TEXT_GRAY)
            self.screen.blit(pts_txt, (margin + 34 + tier_txt.get_width() + 10, y + 8))
            reward_txt = get_font(12).render(r["reward"], True, TEXT_WHITE)
            self.screen.blit(reward_txt, (margin + 34, y + 26))

            draw_locked_overlay(self.screen, r_rect, "LOCKED", self.glow_t)
            y += rh + 6

        # ── Leaderboard mini ─────────────────────────────────
        y += 12
        lb_title = get_font(16, bold=True).render("Top Players This Season", True, TEXT_GOLD)
        self.screen.blit(lb_title, (margin, y))
        y += 24

        lb_rect = pygame.Rect(margin, y, w, 70)
        pygame.draw.rect(self.screen, BG_CARD, lb_rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, lb_rect, 1, border_radius=6)
        lb_hint = get_font(13).render(
            "Check the full leaderboard from the top bar!", True, TEXT_GRAY)
        self.screen.blit(lb_hint, lb_hint.get_rect(center=lb_rect.center))

        self.screen.set_clip(prev_clip)

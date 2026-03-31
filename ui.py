"""
ui.py — Pygame-based pixel UI for WORKY.
Renders bottom info bar (below restaurant), event popups.
The right panel is handled by ShopUI (shop.py) in the main loop.
"""

import pygame
import math
from player import Player
from economy import Economy
from theme import (BG, BG_PANEL as PANEL_BG,
                   TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, TEXT_GREEN,
                   TEXT_CYAN, TEXT_PINK, TEXT_RED,
                   BTN_DISABLED, BORDER, ACCENT)
import icons

# UI-specific button colors
BTN_NORMAL   = (70, 130, 70)
BTN_HOVER    = (90, 170, 90)
BTN_EXIT     = (160, 50, 50)
BTN_EXIT_H   = (200, 70, 70)
BTN_LB       = (50, 90, 160)
BTN_LB_H     = (70, 120, 200)

# Layout constants
SCREEN_W, SCREEN_H = 960, 720
PANEL_W = 320
REST_W = SCREEN_W - PANEL_W   # 640
REST_H = 480                   # restaurant area height
BAR_H = SCREEN_H - REST_H     # 240 bottom info bar height


class UI:
    """Draws the bottom info bar and event popups."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_sm = pygame.font.SysFont("Consolas", 13)
        self.font_md = pygame.font.SysFont("Consolas", 16)
        self.font_lg = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_title = pygame.font.SysFont("Consolas", 26, bold=True)
        self.font_coins = pygame.font.SysFont("Consolas", 28, bold=True)
        self.glow_t = 0.0

        # Animated coin display
        self._display_coins = 0.0  # smoothly approaches real coins
        self._prev_coins = 0.0

        # Bottom bar button rects
        bar_y = REST_H
        self.btn_exit = pygame.Rect(16, bar_y + BAR_H - 46, 130, 34)
        self.btn_leaderboard = pygame.Rect(160, bar_y + BAR_H - 46, 160, 34)
        self.btn_shop_toggle = pygame.Rect(REST_W - 100, bar_y + 8, 88, 28)

    def update(self, dt: float):
        self.glow_t += dt

    # ── Handle bar clicks (returns action string) ────────────
    def handle_bar_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_exit.collidepoint(event.pos):
                return "exit_to_menu"
            if self.btn_leaderboard.collidepoint(event.pos):
                return "toggle_leaderboard"
            if self.btn_shop_toggle.collidepoint(event.pos):
                return "toggle_shop"
        return None

    # ── Draw bottom info bar ─────────────────────────────────
    def draw_bottom_bar(self, player: Player, economy: Economy,
                        ips: float, show_shop: bool):
        bar_y = REST_H
        bar_rect = pygame.Rect(0, bar_y, REST_W, BAR_H)

        # Background gradient
        pygame.draw.rect(self.screen, PANEL_BG, bar_rect)
        # Top border glow
        glow_a = int(30 + 15 * math.sin(self.glow_t * 2))
        gs = pygame.Surface((REST_W, 3), pygame.SRCALPHA)
        gs.fill((*ACCENT[:3], max(0, glow_a)))
        self.screen.blit(gs, (0, bar_y))

        # Subtle grid pattern
        for i in range(0, BAR_H, 6):
            alpha = int(4 + 2 * math.sin(i * 0.1))
            ls = pygame.Surface((REST_W, 1), pygame.SRCALPHA)
            ls.fill((200, 195, 220, max(0, min(255, alpha))))
            self.screen.blit(ls, (0, bar_y + i))

        x_left = 16
        x_right = 340

        # ── Column divider ───────────────────────────────────
        div_x = x_right - 16
        for dy in range(10, BAR_H - 50):
            alpha = int(20 + 10 * math.sin(dy * 0.08))
            ds = pygame.Surface((1, 1), pygame.SRCALPHA)
            ds.fill((200, 195, 220, max(0, alpha)))
            self.screen.blit(ds, (div_x, bar_y + dy))

        # ── Left column: Core stats ─────────────────────────
        # Restaurant name
        if player.restaurant_name:
            name_txt = self.font_title.render(player.restaurant_name, True, TEXT_GOLD)
            self.screen.blit(name_txt, (x_left, bar_y + 10))

        # Coins with animated counter (smoothly ticks to real value)
        target = player.coins
        if abs(self._display_coins - target) > 0.5:
            speed = max(1.0, abs(target - self._display_coins) * 8)
            if self._display_coins < target:
                self._display_coins = min(target, self._display_coins + speed * (1/60))
            else:
                self._display_coins = max(target, self._display_coins - speed * (1/60))
        else:
            self._display_coins = target

        # Coin icon
        gaining = self._display_coins < target - 1
        self.screen.blit(icons.get("coin"), (x_left + 1, bar_y + 42))
        coins_txt = self.font_coins.render(f"{self._display_coins:,.0f}", True, TEXT_GOLD)
        self.screen.blit(coins_txt, (x_left + 22, bar_y + 38))

        # Income per second
        self.screen.blit(icons.get_scaled("speed", 14), (x_left, bar_y + 73))
        ips_txt = self.font_md.render(f"Income: {ips:,.1f}/sec", True, TEXT_GREEN)
        self.screen.blit(ips_txt, (x_left + 18, bar_y + 72))

        # Workers count
        self.screen.blit(icons.get_scaled("person", 14), (x_left, bar_y + 95))
        wk_txt = self.font_md.render(f"Workers: {len(player.workers)}", True, TEXT_WHITE)
        self.screen.blit(wk_txt, (x_left + 18, bar_y + 94))

        # Prestige info
        self.screen.blit(icons.get_scaled("prestige", 12), (x_left, bar_y + 119))
        prestige_txt = self.font_sm.render(
            f"Prestige Lv.{player.prestige_level}  (x{player.prestige_multiplier:.2f})",
            True, TEXT_CYAN)
        self.screen.blit(prestige_txt, (x_left + 16, bar_y + 118))

        # Active bonus indicator with pulsing background
        if player.active_bonus_timer > 0:
            # Pulsing glow background
            pulse = math.sin(self.glow_t * 5)
            bg_a = int(30 + 20 * pulse)
            bg_s = pygame.Surface((280, 22), pygame.SRCALPHA)
            bg_s.fill((255, 80, 50, max(0, bg_a)))
            self.screen.blit(bg_s, (x_left - 4, bar_y + 136))

            pulse_col = (255, int(130 + 60 * pulse), 80)
            bonus_txt = self.font_md.render(
                f"⚡ BONUS x{player.active_bonus_multiplier:.0f}  "
                f"({player.active_bonus_timer:.1f}s)", True, pulse_col)
            self.screen.blit(bonus_txt, (x_left, bar_y + 138))

        # ── Right column: Economy breakdown ──────────────────
        # Section header
        econ_title = self.font_md.render("Economy", True, TEXT_PINK)
        self.screen.blit(econ_title, (x_right, bar_y + 10))

        # Dine-in stats
        di_orders = economy.dinein_orders
        to_orders = economy.takeout_orders
        total_orders = di_orders + to_orders
        di_pct = (di_orders / total_orders * 100) if total_orders > 0 else 0

        self.font_sm_render(f"Dine-In:  {di_orders:,} orders  ({di_pct:.0f}%)  "
                            f"${economy.dinein_income:,.0f}",
                            TEXT_CYAN, x_right, bar_y + 32)
        self.font_sm_render(f"Takeout:  {to_orders:,} orders  ({100-di_pct:.0f}%)  "
                            f"${economy.takeout_income:,.0f}",
                            TEXT_GREEN, x_right, bar_y + 50)

        # Total income
        self.font_sm_render(f"Total Income: ${player.total_income:,.0f}",
                            TEXT_GOLD, x_right, bar_y + 72)

        # Progress bar: dine-in ratio
        bar_x = x_right
        bar_w = 250
        bar_h_px = 10
        bar_bg_y = bar_y + 92
        pygame.draw.rect(self.screen, (230, 228, 235),
                         (bar_x, bar_bg_y, bar_w, bar_h_px), border_radius=4)
        if total_orders > 0:
            fill_w = int(bar_w * di_pct / 100)
            pygame.draw.rect(self.screen, (80, 200, 255),
                             (bar_x, bar_bg_y, fill_w, bar_h_px), border_radius=4)
        di_label = self.font_sm.render("Dine-In", True, TEXT_GRAY)
        to_label = self.font_sm.render("Takeout", True, TEXT_GRAY)
        self.screen.blit(di_label, (bar_x, bar_bg_y + 12))
        self.screen.blit(to_label, (bar_x + bar_w - to_label.get_width(), bar_bg_y + 12))

        # Attractiveness score (from restaurant customization)
        from shop import get_attractiveness
        attract = get_attractiveness(player)
        if attract > 0:
            # Star icons
            stars_full = attract // 20   # 0-5 stars
            if attract >= 80:
                star_col = TEXT_GOLD
            elif attract >= 50:
                star_col = TEXT_GREEN
            else:
                star_col = TEXT_GRAY
            attr_lbl = self.font_md.render("Attract:", True, star_col)
            self.screen.blit(attr_lbl, (x_right, bar_y + 130))
            sx = x_right + attr_lbl.get_width() + 4
            for si in range(5):
                s_ico = icons.get_scaled("star", 12)
                if si >= stars_full:
                    s_ico = s_ico.copy()
                    s_ico.set_alpha(60)
                self.screen.blit(s_ico, (sx + si * 14, bar_y + 132))
            pct_txt = self.font_sm.render(f"{attract}%", True, star_col)
            self.screen.blit(pct_txt, (sx + 5 * 14 + 4, bar_y + 132))

        # Community rating (from leaderboard votes)
        from leaderboard import get_restaurant_rating
        r_avg, r_cnt = get_restaurant_rating(
            player.player_name, player.restaurant_name)
        if r_cnt > 0:
            r_stars = int(round(r_avg))
            if r_avg >= 4.0:
                r_col = TEXT_GOLD
            elif r_avg >= 2.5:
                r_col = TEXT_CYAN
            else:
                r_col = TEXT_GRAY
            rate_lbl = self.font_md.render("Rating:", True, r_col)
            self.screen.blit(rate_lbl, (x_right, bar_y + 150))
            rx = x_right + rate_lbl.get_width() + 4
            for si in range(5):
                s_ico = icons.get_scaled("star", 12)
                if si >= r_stars:
                    s_ico = s_ico.copy()
                    s_ico.set_alpha(60)
                self.screen.blit(s_ico, (rx + si * 14, bar_y + 152))
            info_txt = self.font_sm.render(
                f"{r_avg:.1f} ({r_cnt})", True, r_col)
            self.screen.blit(info_txt, (rx + 5 * 14 + 4, bar_y + 152))

        # ── Buttons (bottom of bar) ──────────────────────────
        # Exit to Menu button
        self._draw_bar_btn(self.btn_exit, "EXIT TO MENU",
                           BTN_EXIT, BTN_EXIT_H, "door")

        # Leaderboard button
        self._draw_bar_btn(self.btn_leaderboard, "LEADERBOARD [L]",
                           BTN_LB, BTN_LB_H, "trophy")

        # Shop/Game toggle at top right of bar
        toggle_label = "GAME" if show_shop else "SHOP [S]"
        toggle_col = (100, 80, 50) if show_shop else (60, 100, 60)
        toggle_hov = (130, 110, 70) if show_shop else (80, 130, 80)
        self._draw_bar_btn(self.btn_shop_toggle, toggle_label,
                           toggle_col, toggle_hov, "shop_bag" if not show_shop else "burger")

        # Key hints
        hint = self.font_sm.render("S: Shop  |  L: Leaderboard  |  ESC: Exit", True,
                                   (70, 68, 85))
        self.screen.blit(hint, (x_right, bar_y + BAR_H - 22))

    def font_sm_render(self, text: str, color: tuple, x: int, y: int):
        """Shorthand to render small text."""
        txt = self.font_sm.render(text, True, color)
        self.screen.blit(txt, (x, y))

    def _draw_bar_btn(self, rect: pygame.Rect, label: str,
                      color: tuple, hover_color: tuple, icon_name: str = ""):
        mx, my = pygame.mouse.get_pos()
        c = hover_color if rect.collidepoint(mx, my) else color
        pygame.draw.rect(self.screen, c, rect, border_radius=5)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=5)
        txt = self.font_sm.render(label, True, TEXT_WHITE)
        if icon_name:
            ico = icons.get_scaled(icon_name, 14)
            total_w = 14 + 4 + txt.get_width()
            ix = rect.centerx - total_w // 2
            self.screen.blit(ico, (ix, rect.centery - 7))
            self.screen.blit(txt, (ix + 18, rect.centery - txt.get_height() // 2))
        else:
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    # ── Event popup (centered in restaurant area) ───────────
    def draw_event(self, economy: Economy):
        if economy.event_display_timer <= 0 or not economy.last_event_name:
            return
        center_x = REST_W // 2
        star_ico = icons.get_scaled("star", 18)
        name_txt = self.font_lg.render(f" {economy.last_event_name}! ", True,
                                  economy.last_event_color)
        total_w = 18 + 4 + name_txt.get_width() + 4 + 18
        left_x = center_x - total_w // 2
        text_y = REST_H - 40 - name_txt.get_height() // 2
        rect = pygame.Rect(left_x - 8, text_y - 4, total_w + 16, name_txt.get_height() + 8)
        # Glowing background
        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        alpha = int(180 + 40 * math.sin(self.glow_t * 4))
        bg.fill((255, 255, 255, max(0, min(255, alpha))))
        self.screen.blit(bg, rect.topleft)
        pygame.draw.rect(self.screen, economy.last_event_color,
                         rect, 2, border_radius=6)
        self.screen.blit(star_ico, (left_x, text_y + 2))
        self.screen.blit(name_txt, (left_x + 22, text_y))
        self.screen.blit(star_ico, (left_x + 22 + name_txt.get_width() + 4, text_y + 2))

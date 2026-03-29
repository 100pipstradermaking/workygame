"""
menu.py — Start menu, registration, and game state management.
Handles: Main menu → Registration → Game → Prestige loop.
"""

import pygame
import math
import os
import random
from sprites import WorkySpriteRenderer, ARCHETYPES
from theme import (BG_DARK, BG_PANEL, TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, TEXT_RED,
                   BTN_PRIMARY, BTN_PRIMARY_H, BTN_SECONDARY, BTN_SECONDARY_H,
                   BTN_DISABLED, BORDER_LIGHT as BORDER, ACCENT)
import icons

MAX_NAME_LENGTH = 16


class MenuState:
    """Tracks which menu screen we're on."""
    MAIN = "main"
    REGISTER = "register"
    PLAYING = "playing"


class StartMenu:
    """Full-screen start menu with animated WORKY logo and registration."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.state = MenuState.MAIN

        # Fonts
        self.font_title = pygame.font.SysFont("Consolas", 48, bold=True)
        self.font_sub = pygame.font.SysFont("Consolas", 18)
        self.font_md = pygame.font.SysFont("Consolas", 20)
        self.font_sm = pygame.font.SysFont("Consolas", 14)
        self.font_input = pygame.font.SysFont("Consolas", 24)

        # Animation
        self.anim_timer = 0.0
        self.anim_frame = 0

        # Mascot sprite
        self.mascot = WorkySpriteRenderer("burger_chef", (255, 210, 80))

        # Registration fields
        self.player_name = ""
        self.restaurant_name = ""
        self.active_field = "player"  # "player" or "restaurant"
        self.error_msg = ""
        self.cursor_blink = 0.0

        # Fade transition
        self._fade_alpha = 255          # start with fade-in from black
        self._fade_dir = -1              # -1 = fading in, +1 = fading out
        self._fade_target_state = None   # state to switch to after fade-out
        self._fade_result = None         # deferred action result

        # Confetti
        self._confetti: list[dict] = []
        self._confetti_timer = 0.0

        # Results
        self.registered = False
        self.reg_data: dict | None = None

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns 'start_game' when registration complete, None otherwise."""

        if self.state == MenuState.MAIN:
            return self._handle_main(event)
        elif self.state == MenuState.REGISTER:
            return self._handle_register(event)
        return None

    # ── Transitions ─────────────────────────────────────────
    def _transition_to(self, target_state, result=None):
        """Start a fade-out → switch state → fade-in transition."""
        self._fade_dir = 1               # fade out
        self._fade_target_state = target_state
        self._fade_result = result

    def _spawn_confetti(self, cx, cy, count=40):
        """Burst confetti particles from a point."""
        colors = [(255,80,80),(80,200,255),(255,220,60),(100,255,120),
                  (200,120,255),(255,160,60)]
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 250)
            self._confetti.append({
                "x": cx, "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 100,
                "life": random.uniform(1.5, 3.0),
                "color": random.choice(colors),
                "size": random.randint(3, 7),
                "rot": 0.0,
                "vr": random.uniform(-5, 5),
            })

    def _draw_confetti(self):
        for p in self._confetti:
            a = max(0, min(255, int(255 * p["life"] / 2.0)))
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], a))
            rotated = pygame.transform.rotate(s, p["rot"] * 57.3)
            self.screen.blit(rotated, (int(p["x"]), int(p["y"])))

    # ── Main menu ─────────────────────────────────────────────
    def _handle_main(self, event):
        if self._fade_dir != 0:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # New Game button
            btn_new = pygame.Rect(self.sw // 2 - 120, 400, 240, 50)
            if btn_new.collidepoint(event.pos):
                self._transition_to(MenuState.REGISTER)
                return None

            # Continue button (only if save exists)
            btn_cont = pygame.Rect(self.sw // 2 - 120, 465, 240, 50)
            if btn_cont.collidepoint(event.pos):
                if os.path.exists("worky_save.json"):
                    return "continue_game"

            # Leaderboard button
            btn_lb = pygame.Rect(self.sw // 2 - 120, 530, 240, 50)
            if btn_lb.collidepoint(event.pos):
                self._show_lb = not getattr(self, '_show_lb', False)
                return None

            # Quit button
            btn_quit = pygame.Rect(self.sw // 2 - 120, 595, 240, 50)
            if btn_quit.collidepoint(event.pos):
                return "quit"
        return None

    # ── Registration ──────────────────────────────────────────
    def _handle_register(self, event):
        if self._fade_dir != 0:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Field selection
            field_player = pygame.Rect(self.sw // 2 - 150, 300, 300, 40)
            field_rest = pygame.Rect(self.sw // 2 - 150, 380, 300, 40)
            if field_player.collidepoint(event.pos):
                self.active_field = "player"
            elif field_rest.collidepoint(event.pos):
                self.active_field = "restaurant"

            # Start button
            btn_start = pygame.Rect(self.sw // 2 - 120, 470, 240, 50)
            if btn_start.collidepoint(event.pos):
                return self._try_register()

            # Back button
            btn_back = pygame.Rect(self.sw // 2 - 120, 535, 240, 40)
            if btn_back.collidepoint(event.pos):
                self._transition_to(MenuState.MAIN)
                return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Switch fields
                self.active_field = "restaurant" if self.active_field == "player" else "player"
            elif event.key == pygame.K_RETURN:
                if self.active_field == "player":
                    self.active_field = "restaurant"
                else:
                    return self._try_register()
            elif event.key == pygame.K_BACKSPACE:
                if self.active_field == "player":
                    self.player_name = self.player_name[:-1]
                else:
                    self.restaurant_name = self.restaurant_name[:-1]
                self.error_msg = ""
            elif event.unicode and event.unicode.isprintable():
                if self.active_field == "player" and len(self.player_name) < MAX_NAME_LENGTH:
                    self.player_name += event.unicode
                elif self.active_field == "restaurant" and len(self.restaurant_name) < MAX_NAME_LENGTH:
                    self.restaurant_name += event.unicode
                self.error_msg = ""

        return None

    def _try_register(self) -> str | None:
        name = self.player_name.strip()
        rest = self.restaurant_name.strip()

        if len(name) < 2:
            self.error_msg = "Name must be at least 2 characters"
            return None
        if len(rest) < 2:
            self.error_msg = "Restaurant name must be at least 2 characters"
            return None

        self.reg_data = {
            "player_name": name,
            "restaurant_name": rest,
        }
        self.registered = True
        # Confetti celebration
        self._spawn_confetti(self.sw // 2, 400, 50)
        return "start_game"

    # ── Drawing ───────────────────────────────────────────────
    def update(self, dt: float):
        self.anim_timer += dt
        self.cursor_blink += dt
        if self.anim_timer > 0.12:
            self.anim_timer = 0.0
            self.anim_frame += 1

        # Fade transition
        if self._fade_dir != 0:
            self._fade_alpha += self._fade_dir * dt * 600
            if self._fade_alpha <= 0:
                self._fade_alpha = 0
                self._fade_dir = 0
            elif self._fade_alpha >= 255:
                self._fade_alpha = 255
                self._fade_dir = -1          # now fade back in
                if self._fade_target_state:
                    self.state = self._fade_target_state
                    self._fade_target_state = None

        # Confetti particles
        alive = []
        for p in self._confetti:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 120 * dt      # gravity
            p["life"] -= dt
            p["rot"] += p["vr"] * dt
            if p["life"] > 0:
                alive.append(p)
        self._confetti = alive

    def draw(self):
        self.screen.fill(BG_DARK)

        if self.state == MenuState.MAIN:
            self._draw_main_menu()
        elif self.state == MenuState.REGISTER:
            self._draw_register()

        # Confetti overlay
        self._draw_confetti()

        # Fade overlay
        if self._fade_alpha > 0:
            fade_surf = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self._fade_alpha)))
            self.screen.blit(fade_surf, (0, 0))

    # ── Main menu drawing ────────────────────────────────────
    def _draw_main_menu(self):
        cx = self.sw // 2

        # Animated background particles
        self._draw_particles()

        # Logo
        bob = math.sin(self.anim_frame * 0.15) * 4
        title = self.font_title.render("WORKY", True, TEXT_GOLD)
        tr = title.get_rect(center=(cx, 120 + bob))
        # Smooth pulsing glow layers
        glow_pulse = 0.5 + 0.5 * math.sin(self.anim_frame * 0.08)
        for offset, alpha_base in [(4, 30), (2, 60)]:
            glow_s = pygame.Surface(
                (tr.w + offset * 4, tr.h + offset * 4), pygame.SRCALPHA)
            glow_t = self.font_title.render("WORKY", True,
                (255, 180, 50, int(alpha_base * glow_pulse)))
            glow_s.blit(glow_t, (offset * 2, offset * 2))
            self.screen.blit(glow_s, (tr.x - offset * 2, tr.y - offset * 2))
        self.screen.blit(title, tr)

        # Subtitle
        sub = self.font_sub.render("Burger Economy Simulator", True, TEXT_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(cx, 170)))

        # Burger icon next to subtitle
        bi = icons.get_scaled("burger", 20)
        sr = sub.get_rect(center=(cx, 170))
        self.screen.blit(bi, (sr.x - 24, 162))
        self.screen.blit(bi, (sr.right + 6, 162))

        # Mascot
        mascot_y = 280 + math.sin(self.anim_frame * 0.2) * 3
        self.mascot.draw(self.screen, cx, int(mascot_y),
                         "down", self.anim_frame, "idle", "legendary")

        # Tagline
        tagline = self.font_sm.render(
            '"Salute the people who keep this world running"', True, TEXT_GRAY)
        self.screen.blit(tagline, tagline.get_rect(center=(cx, 340)))

        # Buttons
        self._draw_menu_btn(pygame.Rect(cx - 120, 400, 240, 50),
                            "NEW GAME", BTN_PRIMARY, BTN_PRIMARY_H, "play")

        has_save = os.path.exists("worky_save.json")
        self._draw_menu_btn(pygame.Rect(cx - 120, 465, 240, 50),
                            "CONTINUE", BTN_SECONDARY if has_save else BTN_DISABLED,
                            BTN_SECONDARY_H if has_save else BTN_DISABLED, "continue")

        self._draw_menu_btn(pygame.Rect(cx - 120, 530, 240, 50),
                            "LEADERBOARD", (50, 90, 160), (70, 120, 200), "leaderboard")

        self._draw_menu_btn(pygame.Rect(cx - 120, 595, 240, 50),
                            "QUIT", (100, 50, 50), (140, 70, 70), "quit")

        # Show leaderboard overlay if toggled
        if getattr(self, '_show_lb', False):
            self._draw_menu_leaderboard()

        # Version
        ver = self.font_sm.render("v0.1.0 MVP", True, (60, 60, 70))
        self.screen.blit(ver, (10, self.sh - 20))

        # Website
        site = self.font_sm.render("workyworker.xyz", True, (80, 80, 100))
        self.screen.blit(site, (self.sw - site.get_width() - 10, self.sh - 20))

    def _draw_particles(self):
        """Floating burger/coin particles in background."""
        for i in range(15):
            phase = i * 1.7 + self.anim_frame * 0.03
            px = int((self.sw * 0.1) + (i * 61) % self.sw)
            py = int((self.sh * 0.5 + math.sin(phase) * 200) % self.sh)
            alpha = int(30 + 20 * math.sin(phase * 2))
            size = 3 + i % 3

            color = (255, 200, 50, alpha) if i % 2 == 0 else (200, 100, 40, alpha)
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color[:3], min(255, alpha)), (size, size), size)
            self.screen.blit(s, (px - size, py - size))

    # ── Registration drawing ─────────────────────────────────
    def _draw_register(self):
        cx = self.sw // 2

        # Panel background
        panel = pygame.Rect(cx - 200, 120, 400, 500)
        pygame.draw.rect(self.screen, BG_PANEL, panel, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT, panel, 2, border_radius=8)

        # Title
        title = self.font_md.render("OPEN YOUR BURGER JOINT", True, TEXT_GOLD)
        self.screen.blit(title, title.get_rect(center=(cx, 160)))

        # Mascot
        self.mascot.draw(self.screen, cx, 230,
                         "down", self.anim_frame, "working", "legendary")

        # Player name field
        self._draw_input_field(
            pygame.Rect(cx - 150, 300, 300, 40),
            "Your Name:", self.player_name,
            self.active_field == "player",
            "Enter your name..."
        )

        # Restaurant name field
        self._draw_input_field(
            pygame.Rect(cx - 150, 380, 300, 40),
            "Restaurant Name:", self.restaurant_name,
            self.active_field == "restaurant",
            "Name your burger joint..."
        )

        # Info text
        info = self.font_sm.render("You'll start with 1 worker + 50 coins", True, TEXT_GRAY)
        self.screen.blit(info, info.get_rect(center=(cx, 445)))

        # Error
        if self.error_msg:
            err = self.font_sm.render(self.error_msg, True, TEXT_RED)
            self.screen.blit(err, err.get_rect(center=(cx, 460)))

        # Start button
        self._draw_menu_btn(pygame.Rect(cx - 120, 470, 240, 50),
                            "START WORKING!", BTN_PRIMARY, BTN_PRIMARY_H, "play")

        # Back
        self._draw_menu_btn(pygame.Rect(cx - 120, 535, 240, 40),
                            "BACK", (70, 70, 80), (90, 90, 100), "door")

    def _draw_input_field(self, rect, label, value, active, placeholder=""):
        # Label
        lbl = self.font_sm.render(label, True, TEXT_WHITE)
        self.screen.blit(lbl, (rect.x, rect.y - 18))

        # Field background
        bg_color = (50, 50, 65) if active else (40, 40, 52)
        border_color = ACCENT if active else BORDER
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=4)

        if value:
            # Text
            txt = self.font_input.render(value, True, TEXT_WHITE)
            self.screen.blit(txt, (rect.x + 10, rect.y + 8))
        else:
            # Placeholder
            txt = self.font_input.render(placeholder, True, (90, 90, 110))
            self.screen.blit(txt, (rect.x + 10, rect.y + 8))

        # Cursor
        if active and int(self.cursor_blink * 2) % 2 == 0:
            cursor_x = rect.x + 10 + 2
            if value:
                val_surf = self.font_input.render(value, True, TEXT_WHITE)
                cursor_x += val_surf.get_width()
            pygame.draw.rect(self.screen, TEXT_GOLD, (cursor_x, rect.y + 8, 2, 24))

    def _draw_menu_btn(self, rect, label, color, hover_color, icon_name=""):
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)
        c = hover_color if hovered else color
        pygame.draw.rect(self.screen, c, rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, rect, 2, border_radius=6)
        txt = self.font_md.render(label, True, TEXT_WHITE)
        if icon_name:
            ico = icons.get(icon_name)
            total_w = 16 + 6 + txt.get_width()
            ix = rect.centerx - total_w // 2
            self.screen.blit(ico, (ix, rect.centery - 8))
            self.screen.blit(txt, (ix + 22, rect.centery - txt.get_height() // 2))
        else:
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def _draw_menu_leaderboard(self):
        """Simple leaderboard view on the main menu."""
        from leaderboard import get_leaderboard
        entries = get_leaderboard()

        cx = self.sw // 2
        pw, ph = 500, 380
        px = cx - pw // 2
        py = (self.sh - ph) // 2

        # Darken background
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Panel
        pygame.draw.rect(self.screen, (28, 26, 38),
                         (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(self.screen, ACCENT,
                         (px, py, pw, ph), 2, border_radius=10)

        # Title with trophy icons
        title = self.font_md.render("LEADERBOARD", True, TEXT_GOLD)
        tr = title.get_rect(center=(cx, py + 24))
        self.screen.blit(title, tr)
        trophy_ico = icons.get_scaled("trophy", 16)
        self.screen.blit(trophy_ico, (tr.x - 22, tr.y))
        self.screen.blit(trophy_ico, (tr.right + 6, tr.y))

        # Entries
        y = py + 50
        for i, entry in enumerate(entries[:10]):
            rank = i + 1

            if rank <= 3:
                medal_name = ["medal_gold", "medal_silver", "medal_bronze"][rank - 1]
                medal_ico = icons.get(medal_name)
                self.screen.blit(medal_ico, (px + 14, y + 1))
                col = [(255, 215, 0), (192, 192, 192), (205, 127, 50)][rank - 1]
            else:
                col = (120, 120, 135)

            rank_txt = self.font_md.render(f"#{rank}", True, col)
            self.screen.blit(rank_txt, (px + 34, y))

            name_txt = self.font_sm.render(
                f"{entry['name'][:12]}  -  {entry['restaurant'][:12]}", True, TEXT_WHITE)
            self.screen.blit(name_txt, (px + 60, y + 2))

            score_str = f"{entry['score']:,.0f}"
            score_txt = self.font_sm.render(score_str, True, TEXT_GOLD)
            self.screen.blit(score_txt, (px + pw - score_txt.get_width() - 16, y + 2))

            y += 30

        if not entries:
            no_data = self.font_sm.render("No entries yet — play a game first!", True, TEXT_GRAY)
            self.screen.blit(no_data, no_data.get_rect(center=(cx, py + ph // 2)))

        # Close hint
        hint = self.font_sm.render("Click LEADERBOARD again to close", True, (80, 80, 100))
        self.screen.blit(hint, hint.get_rect(center=(cx, py + ph - 20)))

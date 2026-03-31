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
            cx = self.sw // 2
            # New Game button
            btn_new = pygame.Rect(cx - 130, 385, 260, 50)
            if btn_new.collidepoint(event.pos):
                self._transition_to(MenuState.REGISTER)
                return None

            # Continue button (only if save exists)
            btn_cont = pygame.Rect(cx - 130, 445, 260, 50)
            if btn_cont.collidepoint(event.pos):
                from online import is_web, web_load
                has_save = os.path.exists("worky_save.json")
                if is_web():
                    has_save = has_save or web_load("save") is not None
                if has_save:
                    return "continue_game"

            # Leaderboard button
            btn_lb = pygame.Rect(cx - 130, 505, 260, 50)
            if btn_lb.collidepoint(event.pos):
                self._show_lb = not getattr(self, '_show_lb', False)
                return None

            # Quit button
            btn_quit = pygame.Rect(cx - 130, 565, 260, 50)
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

        # Animated background — darker kitchen ambience
        self._draw_bg_scene()

        # ── Pixel banner: WORKY BURGERS FARM ──
        bob = math.sin(self.anim_frame * 0.12) * 3
        self._draw_pixel_banner(cx, 40 + int(bob))

        # ── Subtitle ──
        sub = self.font_sub.render("Burger Economy Simulator", True, TEXT_GRAY)
        sub_rect = sub.get_rect(center=(cx, 188))
        self.screen.blit(sub, sub_rect)

        # Burger icons flanking subtitle
        bi = icons.get_scaled("burger", 20)
        self.screen.blit(bi, (sub_rect.x - 26, 180))
        self.screen.blit(bi, (sub_rect.right + 8, 180))

        # ── Animated mascots (two workers on each side of a pixel grill) ──
        self._draw_grill_scene(cx, 270)

        # Tagline
        tagline = self.font_sm.render(
            '"Salute the people who keep this world running"', True, TEXT_GRAY)
        self.screen.blit(tagline, tagline.get_rect(center=(cx, 350)))

        # ── Buttons ──
        self._draw_menu_btn(pygame.Rect(cx - 130, 385, 260, 50),
                            "NEW GAME", BTN_PRIMARY, BTN_PRIMARY_H, "play")

        has_save = os.path.exists("worky_save.json")
        from online import is_web, web_load
        if is_web():
            has_save = has_save or web_load("save") is not None
        self._draw_menu_btn(pygame.Rect(cx - 130, 445, 260, 50),
                            "CONTINUE", BTN_SECONDARY if has_save else BTN_DISABLED,
                            BTN_SECONDARY_H if has_save else BTN_DISABLED, "continue")

        self._draw_menu_btn(pygame.Rect(cx - 130, 505, 260, 50),
                            "LEADERBOARD", (50, 90, 160), (70, 120, 200), "leaderboard")

        self._draw_menu_btn(pygame.Rect(cx - 130, 565, 260, 50),
                            "QUIT", (100, 50, 50), (140, 70, 70), "quit")

        # Show leaderboard overlay if toggled
        if getattr(self, '_show_lb', False):
            self._draw_menu_leaderboard()

        # Version
        ver = self.font_sm.render("v0.2.0", True, (60, 60, 70))
        self.screen.blit(ver, (10, self.sh - 20))

        # Website
        site = self.font_sm.render("workyworker.xyz", True, (80, 80, 100))
        self.screen.blit(site, (self.sw - site.get_width() - 10, self.sh - 20))

    # ── Pixel banner renderer ────────────────────────────────
    _BANNER_FONT = {
        'W': ['#...#','#...#','#.#.#','#.#.#','#.#.#','##.##','#...#'],
        'O': ['.###.','#...#','#...#','#...#','#...#','#...#','.###.'],
        'R': ['####.','#...#','#...#','####.','#.#..','#..#.','#...#'],
        'K': ['#...#','#..#.','#.#..','##...','#.#..','#..#.','#...#'],
        'Y': ['#...#','#...#','.#.#.','..#..','..#..','..#..','..#..'],
        'B': ['####.','#...#','#...#','####.','#...#','#...#','####.'],
        'U': ['#...#','#...#','#...#','#...#','#...#','#...#','.###.'],
        'G': ['.###.','#....','#....','#.##.','#...#','#...#','.###.'],
        'E': ['#####','#....','#....','####.','#....','#....','#####'],
        'S': ['.####','#....','#....','.###.','....#','....#','####.'],
        'F': ['#####','#....','#....','####.','#....','#....','#....'],
        'A': ['.###.','#...#','#...#','#####','#...#','#...#','#...#'],
        'M': ['#...#','##.##','#.#.#','#.#.#','#...#','#...#','#...#'],
        ' ': ['.....','.....','.....','.....','.....','.....','.....',],
    }

    def _draw_pixel_banner(self, cx: int, top_y: int):
        """Draw WORKY / BURGERS FARM pixel title with glow and shading."""
        lines = [("WORKY", (255, 200, 50), (180, 130, 20)),
                 ("BURGERS FARM", (240, 100, 40), (170, 55, 20))]
        PX = 3
        LW = 5; LH = 7; GAP = 2
        LINE_GAP = 14

        for li, (word, color, outline) in enumerate(lines):
            word_w = len(word) * (LW + GAP) * PX - GAP * PX
            sx = cx - word_w // 2
            by = top_y + li * (LH * PX + LINE_GAP)
            hi = tuple(min(255, c + 50) for c in color)

            for ci, ch in enumerate(word):
                bitmap = self._BANNER_FONT.get(ch, self._BANNER_FONT[' '])
                lx = sx + ci * (LW + GAP) * PX
                for row in range(LH):
                    for col in range(LW):
                        if bitmap[row][col] == '#':
                            px_x = lx + col * PX
                            px_y = by + row * PX
                            # Shadow
                            pygame.draw.rect(self.screen, (0, 0, 0, 40),
                                             (px_x + 1, px_y + 1, PX, PX))
                            # Outline
                            pygame.draw.rect(self.screen, outline,
                                             (px_x - 1, px_y - 1, PX + 2, PX + 2))
                            # Main
                            pygame.draw.rect(self.screen, color,
                                             (px_x, px_y, PX, PX))
                            # Highlight top edge
                            if row == 0 or bitmap[row - 1][col] == '.':
                                pygame.draw.rect(self.screen, hi,
                                                 (px_x, px_y, PX, 1))

    def _draw_bg_scene(self):
        """Animated kitchen background with floating particles and tiles."""
        # Tile floor bottom
        floor_y = self.sh - 60
        for gx in range(0, self.sw, 24):
            shade = 20 + (gx // 24 % 2) * 6
            pygame.draw.rect(self.screen, (shade, shade - 2, shade + 10),
                             (gx, floor_y, 24, self.sh - floor_y))
        pygame.draw.line(self.screen, (45, 40, 60),
                         (0, floor_y), (self.sw, floor_y), 2)

        # Floating ingredient particles
        for i in range(20):
            phase = i * 2.1 + self.anim_frame * 0.025
            px = int((i * 47 + 13) % self.sw)
            py = int((self.sh * 0.4 + math.sin(phase) * 250) % self.sh)
            alpha = int(25 + 20 * math.sin(phase * 1.7))
            size = 3 + i % 4

            if i % 4 == 0:
                col = (255, 200, 50)     # gold (coin)
            elif i % 4 == 1:
                col = (200, 100, 40)     # brown (bun)
            elif i % 4 == 2:
                col = (80, 180, 60)      # green (lettuce)
            else:
                col = (220, 60, 40)      # red (tomato)

            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, min(255, alpha)), (size, size), size)
            self.screen.blit(s, (px - size, py - size))

    def _draw_grill_scene(self, cx: int, cy: int):
        """Draw animated pixel grill with mascots on each side."""
        # Grill body
        gw, gh = 80, 24
        gx, gy = cx - gw // 2, cy
        pygame.draw.rect(self.screen, (60, 55, 65), (gx, gy, gw, gh),
                         border_radius=3)
        pygame.draw.rect(self.screen, (90, 85, 100), (gx, gy, gw, gh),
                         1, border_radius=3)
        # Grate lines
        for lx in range(gx + 6, gx + gw - 6, 8):
            pygame.draw.line(self.screen, (80, 75, 90),
                             (lx, gy + 4), (lx, gy + gh - 4), 1)

        # Flames under grill
        for fi in range(5):
            fx = gx + 10 + fi * 15
            fy = gy + gh
            flame_h = 5 + int(3 * math.sin(self.anim_frame * 0.3 + fi * 1.5))
            # Outer flame
            pygame.draw.rect(self.screen, (220, 80, 20),
                             (fx, fy, 6, flame_h))
            # Inner flame
            pygame.draw.rect(self.screen, (255, 200, 40),
                             (fx + 1, fy, 4, max(1, flame_h - 2)))

        # Patties on grill
        for pi in range(3):
            px = gx + 12 + pi * 22
            py_off = int(math.sin(self.anim_frame * 0.15 + pi) * 1)
            pygame.draw.ellipse(self.screen, (130, 65, 30),
                                (px, gy + 6 + py_off, 16, 8))
            pygame.draw.ellipse(self.screen, (160, 90, 45),
                                (px + 2, gy + 6 + py_off, 12, 4))

        # Smoke puffs
        for si in range(4):
            sp = si * 1.8 + self.anim_frame * 0.08
            sx = cx - 20 + si * 15 + int(math.sin(sp * 2) * 6)
            sy = gy - 8 - int((sp * 10) % 30)
            sa = max(0, 50 - int((sp * 10) % 30) * 2)
            if sa > 0:
                smoke_s = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(smoke_s, (160, 160, 170, sa), (5, 5), 4)
                self.screen.blit(smoke_s, (sx, sy))

        # Mascot left (burger chef, facing right)
        mascot_bob_l = int(math.sin(self.anim_frame * 0.2) * 2)
        self.mascot.draw(self.screen, cx - 65, cy + 5 + mascot_bob_l,
                         "right", self.anim_frame, "working", "legendary")

        # Second mascot right (facing left)
        if not hasattr(self, '_mascot2'):
            self._mascot2 = WorkySpriteRenderer("barista", (200, 200, 200))
        mascot_bob_r = int(math.sin(self.anim_frame * 0.2 + 1.5) * 2)
        self._mascot2.draw(self.screen, cx + 65, cy + 5 + mascot_bob_r,
                           "left", self.anim_frame, "working", "epic")

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

"""
menu.py — Start menu, registration, and game state management.
Handles: Main menu → Registration → Game → Prestige loop.
"""

import pygame
import math
import os
import random
from sprites import WorkySpriteRenderer, ARCHETYPES
from theme import (BG_DARK, BG_PANEL, BG_CARD, TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, TEXT_RED,
                   BTN_PRIMARY, BTN_PRIMARY_H, BTN_SECONDARY, BTN_SECONDARY_H,
                   BTN_DISABLED, BORDER_LIGHT as BORDER, ACCENT,
                   NEON_CYAN, NEON_YELLOW, NEON_MAGENTA, NEON_GREEN, NEON_BLUE, NEON_ORANGE)
from ui_components import draw_pixel_corners
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

        # ── Extra menu animations ──
        # Light rays behind banner
        self._menu_rays: list[dict] = []
        for i in range(6):
            self._menu_rays.append({
                "angle": i * (math.tau / 6) + random.uniform(-0.2, 0.2),
                "length": random.uniform(80, 160),
                "width": random.uniform(20, 40),
                "speed": random.uniform(0.1, 0.3),
                "color": random.choice([NEON_CYAN, NEON_YELLOW, ACCENT, NEON_GREEN]),
                "alpha": random.randint(10, 20),
            })

        # Twinkling sparkles
        self._menu_sparkles: list[dict] = []
        for _ in range(20):
            self._menu_sparkles.append({
                "x": random.uniform(0, self.sw),
                "y": random.uniform(0, self.sh * 0.5),
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(2, 5),
                "size": random.uniform(1.5, 3),
                "color": random.choice([NEON_CYAN, NEON_YELLOW, NEON_MAGENTA,
                                        (255, 255, 255), NEON_GREEN]),
            })

        # Floating menu food silhouettes
        self._menu_floats: list[dict] = []
        for _ in range(5):
            self._menu_floats.append({
                "x": random.uniform(10, self.sw - 10),
                "y": random.uniform(50, self.sh - 80),
                "phase": random.uniform(0, math.tau),
                "bob_speed": random.uniform(0.6, 1.5),
                "bob_amp": random.uniform(6, 14),
                "vx": random.uniform(-5, 5),
                "size": random.randint(10, 16),
                "alpha": random.randint(20, 40),
                "kind": random.choice(["burger", "fries", "coin"]),
                "rot": 0.0,
                "vr": random.uniform(-0.3, 0.3),
            })

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
        colors = [ACCENT, NEON_CYAN, NEON_YELLOW, NEON_GREEN,
                  NEON_MAGENTA, NEON_ORANGE]
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

        # Menu floats update
        for mf in self._menu_floats:
            mf["x"] += mf["vx"] * dt
            mf["rot"] += mf["vr"] * dt
            mf["phase"] += mf["bob_speed"] * dt
            if mf["x"] < -20:
                mf["x"] = self.sw + 10
            elif mf["x"] > self.sw + 20:
                mf["x"] = -10

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
    def _draw_text_with_shadow(self, font, text, color, pos, shadow_color=(0, 0, 0),
                                shadow_offset=1, center=False, alpha=255):
        """Render text with a shadow for better readability."""
        if alpha < 255:
            shadow = font.render(text, True, shadow_color)
            sh_surf = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
            sh_surf.blit(shadow, (0, 0))
            sh_surf.set_alpha(alpha // 2)
            main = font.render(text, True, color)
            m_surf = pygame.Surface(main.get_size(), pygame.SRCALPHA)
            m_surf.blit(main, (0, 0))
            m_surf.set_alpha(alpha)
            if center:
                sr = sh_surf.get_rect(center=(pos[0] + shadow_offset, pos[1] + shadow_offset))
                mr = m_surf.get_rect(center=pos)
            else:
                sr = (pos[0] + shadow_offset, pos[1] + shadow_offset)
                mr = pos
            self.screen.blit(sh_surf, sr)
            self.screen.blit(m_surf, mr)
        else:
            shadow = font.render(text, True, shadow_color)
            main = font.render(text, True, color)
            if center:
                sr = shadow.get_rect(center=(pos[0] + shadow_offset, pos[1] + shadow_offset))
                mr = main.get_rect(center=pos)
            else:
                sr = (pos[0] + shadow_offset, pos[1] + shadow_offset)
                mr = pos
            self.screen.blit(shadow, sr)
            self.screen.blit(main, mr)

    def _draw_main_menu(self):
        cx = self.sw // 2

        # Animated background — darker kitchen ambience
        self._draw_bg_scene()

        # ── Pixel banner: WORKY BURGERS FARM ──
        bob = math.sin(self.anim_frame * 0.12) * 3
        self._draw_pixel_banner(cx, 40 + int(bob))

        # ── Subtitle with shadow for readability ──
        self._draw_text_with_shadow(
            self.font_sub, "Burger Economy Simulator",
            TEXT_WHITE, (cx, 188), shadow_color=(200, 195, 185),
            shadow_offset=1, center=True)

        # Burger icons flanking subtitle
        sub_w = self.font_sub.size("Burger Economy Simulator")[0]
        bi = icons.get_scaled("burger", 20)
        self.screen.blit(bi, (cx - sub_w // 2 - 26, 180))
        self.screen.blit(bi, (cx + sub_w // 2 + 8, 180))

        # ── Animated mascots (two workers on each side of a pixel grill) ──
        self._draw_grill_scene(cx, 270)

        # Tagline with shadow
        self._draw_text_with_shadow(
            self.font_sm, '"Salute the people who keep this world running"',
            TEXT_WHITE, (cx, 350), shadow_color=(200, 195, 185),
            shadow_offset=1, center=True)

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
                            "LEADERBOARD", NEON_BLUE, (96, 165, 250), "leaderboard")

        self._draw_menu_btn(pygame.Rect(cx - 130, 565, 260, 50),
                            "QUIT", (180, 100, 100), (200, 130, 130), "quit")

        # Show leaderboard overlay if toggled
        if getattr(self, '_show_lb', False):
            self._draw_menu_leaderboard()

        # Version — with shadow
        self._draw_text_with_shadow(
            self.font_sm, "v0.2.0", TEXT_WHITE, (10, self.sh - 20),
            shadow_color=(200, 195, 185), shadow_offset=1)

        # Website — with shadow
        site_w = self.font_sm.size("workyworker.xyz")[0]
        self._draw_text_with_shadow(
            self.font_sm, "workyworker.xyz", NEON_CYAN,
            (self.sw - site_w - 10, self.sh - 20),
            shadow_color=(0, 100, 102), shadow_offset=1)

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
        lines = [("WORKY", NEON_CYAN, (0, 140, 142)),
                 ("BURGERS FARM", ACCENT, (180, 60, 60))]
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
                # Wave animation per letter
                wave_off = int(2 * math.sin(self.anim_frame * 0.08 + ci * 0.7 + li * 2))
                for row in range(LH):
                    for col in range(LW):
                        if bitmap[row][col] == '#':
                            px_x = lx + col * PX
                            px_y = by + row * PX + wave_off
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
        """Animated kitchen background — light theme with light rays, sparkles, and particles."""
        # Light rays behind banner area
        ray_cx = self.sw // 2
        ray_cy = 100
        for ray in self._menu_rays:
            angle = ray["angle"] + self.anim_timer * ray["speed"] * 5
            length = ray["length"] + 15 * math.sin(self.anim_timer * 7 + ray["angle"])
            w = ray["width"]
            alpha = ray["alpha"]
            end_x = ray_cx + math.cos(angle) * length
            end_y = ray_cy + math.sin(angle) * length
            perp_x = math.cos(angle + math.pi / 2) * w / 2
            perp_y = math.sin(angle + math.pi / 2) * w / 2
            pts = [(ray_cx, ray_cy),
                   (int(end_x + perp_x), int(end_y + perp_y)),
                   (int(end_x - perp_x), int(end_y - perp_y))]
            s = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*ray["color"], alpha), pts)
            self.screen.blit(s, (0, 0))

        # Twinkling sparkles
        t = self.anim_frame * 0.12 + self.anim_timer
        for sp in self._menu_sparkles:
            twinkle = 0.5 + 0.5 * math.sin(t * sp["speed"] + sp["phase"])
            alpha = int(25 + 60 * twinkle)
            size = sp["size"] * (0.6 + 0.4 * twinkle)
            r = max(1, int(size))
            surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            c = r * 2
            pygame.draw.rect(surf, (*sp["color"], alpha), (c - r, c - 1, r * 2, 2))
            pygame.draw.rect(surf, (*sp["color"], alpha), (c - 1, c - r, 2, r * 2))
            pygame.draw.circle(surf, (*sp["color"], min(255, alpha + 30)), (c, c), max(1, r // 2))
            self.screen.blit(surf, (int(sp["x"]) - c, int(sp["y"]) - c))

        # Tile floor bottom
        floor_y = self.sh - 60
        for gx in range(0, self.sw, 24):
            shade = 230 + (gx // 24 % 2) * 8
            pygame.draw.rect(self.screen, (shade, shade - 3, shade - 10),
                             (gx, floor_y, 24, self.sh - floor_y))
        pygame.draw.line(self.screen, (200, 195, 185),
                         (0, floor_y), (self.sw, floor_y), 2)

        # Floating food silhouettes
        for mf in self._menu_floats:
            bob_y = mf["bob_amp"] * math.sin(t * mf["bob_speed"] + mf["phase"])
            x, y = int(mf["x"]), int(mf["y"] + bob_y)
            sz, alpha = mf["size"], mf["alpha"]
            surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            if mf["kind"] == "burger":
                pygame.draw.ellipse(surf, (210, 160, 60, alpha), (2, 2, sz * 2 - 4, sz - 2))
                pygame.draw.ellipse(surf, (120, 60, 30, alpha), (4, sz // 2, sz * 2 - 8, sz // 2))
                pygame.draw.ellipse(surf, (200, 150, 55, alpha), (3, sz, sz * 2 - 6, sz - 4))
            elif mf["kind"] == "fries":
                pygame.draw.rect(surf, (220, 50, 40, alpha), (sz // 2, sz // 2, sz, sz), border_radius=2)
                for fx in range(3):
                    fx_x = sz // 2 + 3 + fx * (sz // 3)
                    pygame.draw.rect(surf, (255, 220, 50, alpha), (fx_x, 2, 3, sz // 2 + 2))
            else:  # coin
                pygame.draw.circle(surf, (255, 200, 50, alpha), (sz, sz), sz - 2)
                pygame.draw.circle(surf, (255, 230, 100, alpha // 2), (sz, sz), sz - 4)
            rotated = pygame.transform.rotate(surf, mf["rot"] * 57.3)
            self.screen.blit(rotated, (x - sz, y - sz))

        # Floating ingredient particles
        for i in range(20):
            phase = i * 2.1 + self.anim_frame * 0.025
            px = int((i * 47 + 13) % self.sw)
            py = int((self.sh * 0.4 + math.sin(phase) * 250) % self.sh)
            alpha = int(35 + 25 * math.sin(phase * 1.7))
            size = 3 + i % 4

            if i % 4 == 0:
                col = NEON_YELLOW
            elif i % 4 == 1:
                col = NEON_ORANGE
            elif i % 4 == 2:
                col = NEON_GREEN
            else:
                col = ACCENT

            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, min(255, alpha)), (size, size), size)
            self.screen.blit(s, (px - size, py - size))

    def _draw_grill_scene(self, cx: int, cy: int):
        """Draw animated pixel grill with mascots on each side."""
        # Grill body
        gw, gh = 80, 24
        gx, gy = cx - gw // 2, cy
        pygame.draw.rect(self.screen, (90, 85, 95), (gx, gy, gw, gh),
                         border_radius=3)
        pygame.draw.rect(self.screen, (120, 115, 130), (gx, gy, gw, gh),
                         1, border_radius=3)
        # Grate lines
        for lx in range(gx + 6, gx + gw - 6, 8):
            pygame.draw.line(self.screen, (110, 105, 120),
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
                pygame.draw.circle(smoke_s, (200, 200, 210, sa), (5, 5), 4)
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

        # Panel background (light theme)
        panel = pygame.Rect(cx - 200, 120, 400, 500)
        pygame.draw.rect(self.screen, BG_PANEL, panel, border_radius=8)
        pygame.draw.rect(self.screen, NEON_CYAN, panel, 2, border_radius=8)
        draw_pixel_corners(self.screen, panel, NEON_CYAN, 3)

        # Title with shadow
        self._draw_text_with_shadow(
            self.font_md, "OPEN YOUR BURGER JOINT",
            NEON_CYAN, (cx, 160), shadow_color=(0, 120, 122),
            shadow_offset=1, center=True)

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

        # Info text — darker for readability on white panel
        info = self.font_sm.render("You'll start with 1 worker + 50 coins", True, (60, 70, 75))
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
                            "BACK", (180, 180, 190), (200, 200, 210), "door")

    def _draw_input_field(self, rect, label, value, active, placeholder=""):
        # Label — bold dark color for readability on white panel
        lbl = self.font_sm.render(label, True, (30, 35, 40))
        self.screen.blit(lbl, (rect.x, rect.y - 18))

        # Field background (light theme)
        bg_color = (255, 255, 255) if active else (248, 245, 240)
        border_color = NEON_CYAN if active else BORDER
        # Active glow
        if active:
            glow = pygame.Surface((rect.w + 6, rect.h + 6), pygame.SRCALPHA)
            glow.fill((*NEON_CYAN, 25))
            self.screen.blit(glow, (rect.x - 3, rect.y - 3))
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)

        if value:
            txt = self.font_input.render(value, True, (25, 30, 35))
            self.screen.blit(txt, (rect.x + 10, rect.y + 8))
        else:
            txt = self.font_input.render(placeholder, True, (160, 170, 175))
            self.screen.blit(txt, (rect.x + 10, rect.y + 8))

        # Cursor
        if active and int(self.cursor_blink * 2) % 2 == 0:
            cursor_x = rect.x + 10 + 2
            if value:
                val_surf = self.font_input.render(value, True, (25, 30, 35))
                cursor_x += val_surf.get_width()
            pygame.draw.rect(self.screen, NEON_CYAN, (cursor_x, rect.y + 8, 2, 24))

    def _draw_menu_btn(self, rect, label, color, hover_color, icon_name=""):
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)
        c = hover_color if hovered else color
        pygame.draw.rect(self.screen, c, rect, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=8)
        draw_pixel_corners(self.screen, rect, c, 2)
        txt = self.font_md.render(label, True, (255, 255, 255))
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
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        # Panel (light theme)
        pygame.draw.rect(self.screen, BG_PANEL,
                         (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(self.screen, NEON_YELLOW,
                         (px, py, pw, ph), 2, border_radius=10)
        draw_pixel_corners(self.screen, pygame.Rect(px, py, pw, ph), NEON_YELLOW, 3)

        # Title with trophy icons
        title = self.font_md.render("LEADERBOARD", True, NEON_YELLOW)
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
                f"{entry['name'][:12]}  -  {entry['restaurant'][:12]}", True, (30, 35, 40))
            self.screen.blit(name_txt, (px + 60, y + 2))

            score_str = f"{entry['score']:,.0f}"
            score_txt = self.font_sm.render(score_str, True, NEON_YELLOW)
            self.screen.blit(score_txt, (px + pw - score_txt.get_width() - 16, y + 2))

            y += 30

        if not entries:
            no_data = self.font_sm.render("No entries yet \u2014 play a game first!", True, (60, 70, 75))
            self.screen.blit(no_data, no_data.get_rect(center=(cx, py + ph // 2)))

        # Close hint
        hint = self.font_sm.render("Click LEADERBOARD again to close", True, (60, 70, 75))
        self.screen.blit(hint, hint.get_rect(center=(cx, py + ph - 20)))

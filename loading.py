"""
loading.py — Animated loading / splash screen for WORKY: Burgers Farm.
Shows pixel-art animations while the game loads:
  - WORKY BURGERS FARM big pixel title with letter-by-letter reveal
  - Animated pixel burger being assembled layer by layer
  - Walking worker characters crossing the screen
  - Floating ingredient particles
  - Progress bar with loading tips
  - "CLICK TO START" pulsing prompt when done
"""

import pygame
import math
import random
import asyncio

from theme import (BG_DARK, TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, ACCENT, BG_PANEL,
                   NEON_CYAN, NEON_YELLOW, NEON_MAGENTA, NEON_GREEN, NEON_ORANGE)

# ── Pixel-art letter bitmaps (5×7 grid each) ─────────────────
# Each letter is a list of 7 rows, each row a string of 5 chars
# '#' = filled pixel, '.' = empty
_FONT_5x7 = {
    'W': [
        '#...#',
        '#...#',
        '#.#.#',
        '#.#.#',
        '#.#.#',
        '##.##',
        '#...#',
    ],
    'O': [
        '.###.',
        '#...#',
        '#...#',
        '#...#',
        '#...#',
        '#...#',
        '.###.',
    ],
    'R': [
        '####.',
        '#...#',
        '#...#',
        '####.',
        '#.#..',
        '#..#.',
        '#...#',
    ],
    'K': [
        '#...#',
        '#..#.',
        '#.#..',
        '##...',
        '#.#..',
        '#..#.',
        '#...#',
    ],
    'Y': [
        '#...#',
        '#...#',
        '.#.#.',
        '..#..',
        '..#..',
        '..#..',
        '..#..',
    ],
    'B': [
        '####.',
        '#...#',
        '#...#',
        '####.',
        '#...#',
        '#...#',
        '####.',
    ],
    'U': [
        '#...#',
        '#...#',
        '#...#',
        '#...#',
        '#...#',
        '#...#',
        '.###.',
    ],
    'G': [
        '.###.',
        '#....',
        '#....',
        '#.##.',
        '#...#',
        '#...#',
        '.###.',
    ],
    'E': [
        '#####',
        '#....',
        '#....',
        '####.',
        '#....',
        '#....',
        '#####',
    ],
    'S': [
        '.####',
        '#....',
        '#....',
        '.###.',
        '....#',
        '....#',
        '####.',
    ],
    'F': [
        '#####',
        '#....',
        '#....',
        '####.',
        '#....',
        '#....',
        '#....',
    ],
    'A': [
        '.###.',
        '#...#',
        '#...#',
        '#####',
        '#...#',
        '#...#',
        '#...#',
    ],
    'M': [
        '#...#',
        '##.##',
        '#.#.#',
        '#.#.#',
        '#...#',
        '#...#',
        '#...#',
    ],
    ' ': [
        '.....',
        '.....',
        '.....',
        '.....',
        '.....',
        '.....',
        '.....',
    ],
}

# ── Loading tips ──────────────────────────────────────────────
_TIPS = [
    "Hire more workers to boost income!",
    "Upgrade your kitchen for faster service",
    "Prestige at $1M for permanent bonuses",
    "Check the leaderboard to compete online",
    "Buy decorations to attract more customers",
    "Events happen randomly — stay ready!",
    "Better rarity workers earn more coins",
    "Unlock all shop upgrades to maximize profit",
]


class LoadingScreen:
    """Animated splash/loading screen with pixel art."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.time = 0.0
        self.done = False
        self._clicked = False

        # Fonts
        self.font_sm = pygame.font.SysFont("Consolas", 14)
        self.font_md = pygame.font.SysFont("Consolas", 18)
        self.font_lg = pygame.font.SysFont("Consolas", 24, bold=True)

        # Loading state
        self.progress = 0.0        # 0..1
        self.tip_idx = random.randint(0, len(_TIPS) - 1)
        self.tip_timer = 0.0

        # Pixel title reveal
        self._title_chars_revealed = 0
        self._title_reveal_timer = 0.0

        # Burger assembly animation
        self._burger_layers_shown = 0
        self._burger_timer = 0.0

        # Walking workers
        self._workers: list[dict] = []
        self._worker_spawn_timer = 0.0

        # Floating ingredients
        self._particles: list[dict] = []
        for _ in range(20):
            self._particles.append(self._make_particle())

        # Smoke puffs from grill
        self._smoke: list[dict] = []

        # ── Extra animations ──
        # Twinkling stars
        self._stars: list[dict] = []
        for _ in range(30):
            self._stars.append({
                "x": random.uniform(0, self.sw),
                "y": random.uniform(0, self.sh * 0.55),
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(1.5, 4.0),
                "size": random.uniform(1.5, 3.5),
                "color": random.choice([NEON_CYAN, NEON_YELLOW, NEON_MAGENTA,
                                        NEON_GREEN, (255, 255, 255)]),
            })

        # Light rays behind title
        self._rays: list[dict] = []
        for i in range(8):
            self._rays.append({
                "angle": i * (math.tau / 8),
                "length": random.uniform(100, 200),
                "width": random.uniform(15, 35),
                "speed": random.uniform(0.15, 0.4),
                "color": random.choice([NEON_CYAN, NEON_YELLOW, ACCENT, NEON_GREEN]),
                "alpha": random.randint(12, 25),
            })

        # Floating food items (larger, distinct shapes)
        self._food_items: list[dict] = []
        for _ in range(6):
            self._food_items.append(self._make_food_item())

        # Coin sparkle trail
        self._coin_sparkles: list[dict] = []

    def _make_particle(self) -> dict:
        kind = random.choice(["bun", "patty", "lettuce", "tomato", "cheese", "coin"])
        colors = {
            "bun":     (210, 160, 60),
            "patty":   (120, 60, 30),
            "lettuce": (80, 180, 60),
            "tomato":  (220, 60, 40),
            "cheese":  (255, 220, 50),
            "coin":    (255, 200, 50),
        }
        return {
            "x": random.uniform(0, self.sw),
            "y": random.uniform(-40, self.sh + 40),
            "vx": random.uniform(-15, 15),
            "vy": random.uniform(-30, -8),
            "size": random.randint(3, 6),
            "color": colors[kind],
            "kind": kind,
            "rot": random.uniform(0, 6.28),
            "vr": random.uniform(-2, 2),
            "alpha": random.randint(40, 90),
        }

    def _make_food_item(self) -> dict:
        """Create a larger floating food item with gentle drift."""
        kinds = ["burger", "fries", "drink", "coin_stack", "star"]
        kind = random.choice(kinds)
        return {
            "x": random.uniform(20, self.sw - 20),
            "y": random.uniform(30, self.sh - 100),
            "base_y": 0.0,  # set below
            "vx": random.uniform(-8, 8),
            "phase": random.uniform(0, math.tau),
            "bob_speed": random.uniform(0.8, 1.8),
            "bob_amp": random.uniform(8, 18),
            "size": random.randint(12, 20),
            "kind": kind,
            "rot": 0.0,
            "vr": random.uniform(-0.5, 0.5),
            "alpha": random.randint(35, 60),
        }

    def _spawn_worker(self):
        from_left = random.random() < 0.5
        archetypes = ["burger_chef", "office_grinder", "construction",
                      "barista", "delivery", "janitor"]
        colors = [(255, 215, 0), (200, 200, 200), (205, 127, 50),
                  (180, 50, 50), (50, 180, 50), (50, 50, 180)]
        idx = random.randint(0, len(archetypes) - 1)
        from sprites import WorkySpriteRenderer
        renderer = WorkySpriteRenderer(archetypes[idx], colors[idx])
        self._workers.append({
            "x": -40.0 if from_left else float(self.sw + 40),
            "y": float(self.sh - 70 + random.randint(-10, 10)),
            "vx": random.uniform(40, 80) * (1 if from_left else -1),
            "renderer": renderer,
            "dir": "right" if from_left else "left",
            "frame": random.randint(0, 100),
        })

    def update(self, dt: float):
        self.time += dt

        # Progress bar fills over ~3 seconds
        if self.progress < 1.0:
            self.progress = min(1.0, self.progress + dt / 3.0)
        elif not self.done:
            self.done = True

        # Title reveal (one letter every 0.08s)
        title = "WORKY  BURGERS  FARM"
        self._title_reveal_timer += dt
        if self._title_reveal_timer > 0.08 and self._title_chars_revealed < len(title):
            self._title_reveal_timer = 0.0
            self._title_chars_revealed += 1

        # Burger assembly (one layer every 0.4s)
        self._burger_timer += dt
        if self._burger_timer > 0.4 and self._burger_layers_shown < 7:
            self._burger_timer = 0.0
            self._burger_layers_shown += 1

        # Worker spawning
        self._worker_spawn_timer += dt
        if self._worker_spawn_timer > 1.2 and len(self._workers) < 6:
            self._worker_spawn_timer = 0.0
            self._spawn_worker()

        # Update workers
        alive_w = []
        for w in self._workers:
            w["x"] += w["vx"] * dt
            w["frame"] += 1
            if -80 < w["x"] < self.sw + 80:
                alive_w.append(w)
        self._workers = alive_w

        # Update particles
        for p in self._particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["rot"] += p["vr"] * dt
            if p["y"] < -50:
                p["y"] = self.sh + 20
                p["x"] = random.uniform(0, self.sw)

        # Smoke puffs
        if random.random() < dt * 3:
            cx = self.sw // 2
            self._smoke.append({
                "x": cx + random.uniform(-30, 30),
                "y": float(self.sh // 2 + 20),
                "vy": random.uniform(-40, -15),
                "life": random.uniform(1.0, 2.5),
                "max_life": 2.5,
                "size": random.uniform(4, 10),
            })
        alive_s = []
        for s in self._smoke:
            s["y"] += s["vy"] * dt
            s["x"] += math.sin(self.time * 3 + s["x"] * 0.1) * 8 * dt
            s["life"] -= dt
            s["size"] += dt * 3
            if s["life"] > 0:
                alive_s.append(s)
        self._smoke = alive_s[:30]

        # Food items bobbing
        for fi in self._food_items:
            fi["x"] += fi["vx"] * dt
            fi["rot"] += fi["vr"] * dt
            fi["phase"] += fi["bob_speed"] * dt
            # Wrap around screen edges
            if fi["x"] < -30:
                fi["x"] = self.sw + 20
            elif fi["x"] > self.sw + 30:
                fi["x"] = -20

        # Coin sparkles from progress bar
        if self.progress < 1.0 and random.random() < dt * 8:
            bar_fill_x = self.sw // 2 - 150 + int(296 * self.progress)
            self._coin_sparkles.append({
                "x": bar_fill_x + random.uniform(-3, 3),
                "y": float(self.sh - 100 + random.uniform(-2, 2)),
                "vy": random.uniform(-60, -20),
                "vx": random.uniform(-15, 15),
                "life": random.uniform(0.5, 1.2),
                "size": random.uniform(1.5, 3.0),
                "color": random.choice([NEON_YELLOW, (255, 215, 0), (255, 200, 50)]),
            })
        alive_cs = []
        for cs in self._coin_sparkles:
            cs["x"] += cs["vx"] * dt
            cs["y"] += cs["vy"] * dt
            cs["life"] -= dt
            if cs["life"] > 0:
                alive_cs.append(cs)
        self._coin_sparkles = alive_cs[:40]

        # Tip rotation
        self.tip_timer += dt
        if self.tip_timer > 3.0:
            self.tip_timer = 0.0
            self.tip_idx = (self.tip_idx + 1) % len(_TIPS)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when user clicks to start (after loading done)."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.done:
                self._clicked = True
                return True
        if event.type == pygame.KEYDOWN:
            if self.done:
                self._clicked = True
                return True
        return False

    @property
    def finished(self) -> bool:
        return self._clicked

    def draw(self):
        self.screen.fill((250, 248, 245))

        # Light rays behind title
        self._draw_light_rays()

        # Twinkling stars
        self._draw_stars()

        # Background particles
        self._draw_bg_particles()

        # Floating food items
        self._draw_food_items()

        # Smoke
        self._draw_smoke()

        cx = self.sw // 2
        cy = self.sh // 2

        # === Big pixel title: WORKY BURGERS FARM ===
        self._draw_pixel_title(cx, 80)

        # === Subtitle with shadow for readability ===
        sub_alpha = min(255, int(self.time * 120))
        sub_shadow = self.font_md.render(
            "Burger Economy Simulator", True, (180, 175, 165))
        sub_text = self.font_md.render(
            "Burger Economy Simulator", True, (45, 52, 54))
        if sub_alpha < 255:
            sh_s = pygame.Surface(sub_shadow.get_size(), pygame.SRCALPHA)
            sh_s.blit(sub_shadow, (0, 0))
            sh_s.set_alpha(sub_alpha // 2)
            tx_s = pygame.Surface(sub_text.get_size(), pygame.SRCALPHA)
            tx_s.blit(sub_text, (0, 0))
            tx_s.set_alpha(sub_alpha)
            self.screen.blit(sh_s, sh_s.get_rect(center=(cx + 1, 186)))
            self.screen.blit(tx_s, tx_s.get_rect(center=(cx, 185)))
        else:
            self.screen.blit(sub_shadow, sub_shadow.get_rect(center=(cx + 1, 186)))
            self.screen.blit(sub_text, sub_text.get_rect(center=(cx, 185)))

        # === Animated burger assembly ===
        self._draw_burger_assembly(cx, cy + 30)

        # === Walking workers along the bottom ===
        for w in self._workers:
            w["renderer"].draw(
                self.screen, int(w["x"]), int(w["y"]),
                w["dir"], w["frame"], "working")

        # === Ground line ===
        ground_y = self.sh - 50
        pygame.draw.line(self.screen, (200, 195, 185),
                         (0, ground_y), (self.sw, ground_y), 2)

        # Small tiles on ground
        for gx in range(0, self.sw, 20):
            shade = 230 + (gx // 20 % 2) * 8
            pygame.draw.rect(self.screen, (shade, shade - 3, shade - 10),
                             (gx, ground_y, 20, self.sh - ground_y))

        # === Progress bar ===
        self._draw_progress_bar(cx, self.sh - 100)

        # === Coin sparkles ===
        self._draw_coin_sparkles()

        # === Loading tip with shadow ===
        tip = _TIPS[self.tip_idx]
        tip_shadow = self.font_sm.render(f"TIP: {tip}", True, (180, 175, 165))
        tip_surf = self.font_sm.render(f"TIP: {tip}", True, (45, 52, 54))
        self.screen.blit(tip_shadow, tip_shadow.get_rect(center=(cx + 1, self.sh - 69)))
        self.screen.blit(tip_surf, tip_surf.get_rect(center=(cx, self.sh - 70)))

        # === "CLICK TO START" prompt ===
        if self.done:
            self._draw_click_prompt(cx, self.sh - 35)

        # === Version badge ===
        ver = self.font_sm.render("v0.2.0", True, (45, 52, 54))
        self.screen.blit(ver, (8, self.sh - 18))

    def _draw_pixel_title(self, cx: int, top_y: int):
        """Draw big pixel-art title letter by letter."""
        line1 = "WORKY"
        line2 = "BURGERS"
        line3 = "FARM"

        PX = 4          # each pixel = 4×4 screen pixels
        LETTER_W = 5    # letter grid width
        LETTER_H = 7    # letter grid height
        GAP = 2         # gap between letters in art-pixels
        LINE_GAP = 12   # gap between lines in screen pixels

        colors = [
            (255, 200, 50),   # WORKY — gold
            (220, 80, 40),    # BURGERS — red/orange
            (80, 200, 80),    # FARM — green
        ]
        outline_colors = [
            (180, 130, 20),
            (160, 40, 20),
            (40, 130, 40),
        ]

        total_revealed = self._title_chars_revealed
        char_idx = 0

        for line_idx, word in enumerate((line1, line2, line3)):
            word_w = len(word) * (LETTER_W + GAP) * PX - GAP * PX
            start_x = cx - word_w // 2
            y_base = top_y + line_idx * (LETTER_H * PX + LINE_GAP)

            color = colors[line_idx]
            outline = outline_colors[line_idx]
            highlight = tuple(min(255, c + 60) for c in color)

            for ci, ch in enumerate(word):
                if char_idx >= total_revealed:
                    break
                char_idx += 1

                bitmap = _FONT_5x7.get(ch, _FONT_5x7[' '])
                lx = start_x + ci * (LETTER_W + GAP) * PX

                # Drop-in animation for recently revealed letters
                age = total_revealed - char_idx
                if age < 3:
                    bounce = int((3 - age) * 4 * math.sin(self.time * 12))
                else:
                    # Gentle continuous wave after settled
                    bounce = int(2 * math.sin(self.time * 2.5 + char_idx * 0.6))

                for row in range(LETTER_H):
                    for col in range(LETTER_W):
                        if bitmap[row][col] == '#':
                            px_x = lx + col * PX
                            px_y = y_base + row * PX + bounce

                            # Outline (1px offset)
                            pygame.draw.rect(self.screen, outline,
                                             (px_x - 1, px_y - 1, PX + 2, PX + 2))
                            # Main pixel
                            pygame.draw.rect(self.screen, color,
                                             (px_x, px_y, PX, PX))
                            # Highlight top-left corner
                            if row == 0 or (row > 0 and bitmap[row - 1][col] == '.'):
                                pygame.draw.rect(self.screen, highlight,
                                                 (px_x, px_y, PX, 1))
            else:
                continue  # only break inner loop

    def _draw_burger_assembly(self, cx: int, cy: int):
        """Draw a big pixel burger being assembled layer by layer."""
        layers = [
            # (name, color, highlight, width, height, y_offset)
            ("plate",    (100, 95, 110), (130, 125, 140), 80, 6,  60),
            ("bun_bot",  (210, 160, 60), (240, 190, 80),  60, 12, 48),
            ("patty",    (120, 60, 30),  (160, 85, 45),   56, 10, 38),
            ("cheese",   (255, 210, 40), (255, 235, 100), 58, 6,  32),
            ("lettuce",  (60, 170, 50),  (100, 210, 80),  62, 8,  26),
            ("tomato",   (220, 50, 40),  (255, 90, 70),   50, 6,  20),
            ("bun_top",  (220, 170, 65), (250, 200, 90),  58, 14, 6),
        ]

        for i, (name, col, hi, w, h, yoff) in enumerate(layers):
            if i >= self._burger_layers_shown:
                break

            # Drop-in animation
            age = self._burger_layers_shown - i - 1
            if age == 0:
                drop = max(0, int(20 * (1 - self._burger_timer / 0.4)))
            else:
                drop = 0

            rx = cx - w // 2
            ry = cy + yoff - drop

            # Shadow
            if name != "plate":
                shadow = pygame.Surface((w + 4, h + 2), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 30))
                self.screen.blit(shadow, (rx - 2, ry + 2))

            # Main shape
            pygame.draw.rect(self.screen, col, (rx, ry, w, h),
                             border_radius=3 if name.startswith("bun") else 1)
            # Highlight
            pygame.draw.rect(self.screen, hi, (rx + 2, ry, w - 4, max(1, h // 3)),
                             border_radius=2)

            # Sesame seeds on top bun
            if name == "bun_top":
                seed_col = (240, 220, 160)
                for sx, sy in [(cx - 12, ry + 3), (cx + 6, ry + 2),
                               (cx - 4, ry + 5), (cx + 14, ry + 4)]:
                    pygame.draw.ellipse(self.screen, seed_col, (sx, sy, 4, 2))

            # Lettuce wavy edge
            if name == "lettuce":
                for lx in range(rx, rx + w, 6):
                    wave_y = ry + h + int(math.sin(lx * 0.5) * 2)
                    pygame.draw.circle(self.screen, (50, 150, 40),
                                       (lx + 3, wave_y), 3)

            # Flag on top when fully assembled
            if self._burger_layers_shown >= 7 and name == "bun_top":
                flag_x = cx
                flag_y = ry - 18
                pygame.draw.line(self.screen, (200, 200, 200),
                                 (flag_x, ry), (flag_x, flag_y), 2)
                # Flag triangle
                pts = [(flag_x, flag_y), (flag_x + 14, flag_y + 5),
                       (flag_x, flag_y + 10)]
                pygame.draw.polygon(self.screen, (220, 60, 40), pts)
                pygame.draw.polygon(self.screen, (180, 40, 30), pts, 1)
                # "W" on flag
                w_text = self.font_sm.render("W", True, TEXT_WHITE)
                self.screen.blit(w_text, (flag_x + 2, flag_y + 1))

    def _draw_bg_particles(self):
        for p in self._particles:
            s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            alpha = p["alpha"]
            col = (*p["color"], alpha)

            if p["kind"] == "coin":
                pygame.draw.circle(s, col, (p["size"], p["size"]), p["size"])
                # Inner highlight
                pygame.draw.circle(s, (*p["color"][:2], min(255, p["color"][2] + 60), alpha // 2),
                                   (p["size"], p["size"]), max(1, p["size"] - 2))
            else:
                pygame.draw.rect(s, col, (1, 1, p["size"] * 2 - 2, p["size"] * 2 - 2),
                                 border_radius=2)

            rotated = pygame.transform.rotate(s, p["rot"] * 57.3)
            self.screen.blit(rotated, (int(p["x"]) - p["size"],
                                       int(p["y"]) - p["size"]))

    def _draw_smoke(self):
        for s in self._smoke:
            alpha = int(60 * (s["life"] / s["max_life"]))
            r = int(s["size"])
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 180, 190, alpha), (r, r), r)
            self.screen.blit(surf, (int(s["x"]) - r, int(s["y"]) - r))

    def _draw_progress_bar(self, cx: int, y: int):
        bar_w = 300
        bar_h = 12
        bx = cx - bar_w // 2
        by = y

        # Background
        pygame.draw.rect(self.screen, (230, 230, 235), (bx, by, bar_w, bar_h),
                         border_radius=6)
        # Border
        pygame.draw.rect(self.screen, (200, 195, 210), (bx, by, bar_w, bar_h),
                         1, border_radius=6)

        # Fill
        fill_w = int((bar_w - 4) * self.progress)
        if fill_w > 0:
            fill_color = ACCENT if self.done else (200, 140, 40)
            pygame.draw.rect(self.screen, fill_color,
                             (bx + 2, by + 2, fill_w, bar_h - 4),
                             border_radius=4)
            # Shine
            pygame.draw.rect(self.screen, tuple(min(255, c + 40) for c in fill_color),
                             (bx + 2, by + 2, fill_w, 2), border_radius=2)

        # Percentage text
        pct = int(self.progress * 100)
        pct_text = self.font_sm.render(f"{pct}%", True, TEXT_WHITE)
        self.screen.blit(pct_text, pct_text.get_rect(center=(cx, by + bar_h // 2)))

    def _draw_click_prompt(self, cx: int, y: int):
        """Pulsing 'CLICK TO START' prompt."""
        pulse = 0.5 + 0.5 * math.sin(self.time * 4)
        alpha = int(120 + 135 * pulse)

        prompt_surf = pygame.Surface((300, 30), pygame.SRCALPHA)
        text = self.font_lg.render("CLICK TO START", True,
                                   (*TEXT_GOLD[:3], alpha))
        tr = text.get_rect(center=(150, 15))
        prompt_surf.blit(text, tr)

        # Glow behind
        glow = pygame.Surface((320, 40), pygame.SRCALPHA)
        glow.fill((*ACCENT[:3], int(20 * pulse)))
        self.screen.blit(glow, (cx - 160, y - 20))

        self.screen.blit(prompt_surf, (cx - 150, y - 15))

        # Arrow indicators
        arrow_off = int(6 * pulse)
        arr_col = (*TEXT_GOLD[:3], alpha)
        # Left arrows
        for dx in [0, 10]:
            ax = cx - 170 - dx - arrow_off
            pts = [(ax + 8, y - 5), (ax, y), (ax + 8, y + 5)]
            s = pygame.Surface((12, 14), pygame.SRCALPHA)
            pygame.draw.polygon(s, arr_col,
                                [(8, 0), (0, 5), (8, 10)])
            self.screen.blit(s, (ax, y - 7))
        # Right arrows
        for dx in [0, 10]:
            ax = cx + 158 + dx + arrow_off
            s = pygame.Surface((12, 14), pygame.SRCALPHA)
            pygame.draw.polygon(s, arr_col,
                                [(0, 0), (8, 5), (0, 10)])
            self.screen.blit(s, (ax, y - 7))

    def _draw_light_rays(self):
        """Draw subtle rotating light rays behind the title area."""
        cx = self.sw // 2
        cy = 120  # center of title area
        for ray in self._rays:
            angle = ray["angle"] + self.time * ray["speed"]
            length = ray["length"] + 20 * math.sin(self.time * 1.5 + ray["angle"])
            w = ray["width"]
            alpha = ray["alpha"]

            # Calculate ray triangle points
            end_x = cx + math.cos(angle) * length
            end_y = cy + math.sin(angle) * length
            perp_x = math.cos(angle + math.pi / 2) * w / 2
            perp_y = math.sin(angle + math.pi / 2) * w / 2

            pts = [
                (cx, cy),
                (int(end_x + perp_x), int(end_y + perp_y)),
                (int(end_x - perp_x), int(end_y - perp_y)),
            ]

            s = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*ray["color"], alpha), pts)
            self.screen.blit(s, (0, 0))

    def _draw_stars(self):
        """Draw twinkling star particles across the upper screen."""
        for star in self._stars:
            twinkle = 0.5 + 0.5 * math.sin(self.time * star["speed"] + star["phase"])
            alpha = int(30 + 70 * twinkle)
            size = star["size"] * (0.7 + 0.3 * twinkle)
            r = max(1, int(size))

            # Star shape — cross pattern
            s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            center = r * 2
            # Horizontal bar
            pygame.draw.rect(s, (*star["color"], alpha),
                             (center - r, center - 1, r * 2, 2))
            # Vertical bar
            pygame.draw.rect(s, (*star["color"], alpha),
                             (center - 1, center - r, 2, r * 2))
            # Center bright dot
            pygame.draw.circle(s, (*star["color"], min(255, alpha + 40)),
                               (center, center), max(1, r // 2))

            self.screen.blit(s, (int(star["x"]) - center,
                                  int(star["y"]) - center))

    def _draw_food_items(self):
        """Draw larger floating food silhouettes."""
        for fi in self._food_items:
            bob_y = fi["bob_amp"] * math.sin(self.time * fi["bob_speed"] + fi["phase"])
            x = int(fi["x"])
            y = int(fi["y"] + bob_y)
            sz = fi["size"]
            alpha = fi["alpha"]
            kind = fi["kind"]

            s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)

            if kind == "burger":
                # Bun
                pygame.draw.ellipse(s, (210, 160, 60, alpha),
                                    (2, 2, sz * 2 - 4, sz - 2))
                # Patty
                pygame.draw.ellipse(s, (120, 60, 30, alpha),
                                    (4, sz // 2 + 2, sz * 2 - 8, sz // 2))
                # Bottom bun
                pygame.draw.ellipse(s, (200, 150, 55, alpha),
                                    (3, sz, sz * 2 - 6, sz - 4))
            elif kind == "fries":
                # Cup
                pygame.draw.rect(s, (220, 50, 40, alpha),
                                 (sz // 2, sz // 2, sz, sz), border_radius=2)
                # Fries sticking out
                for fx in range(3):
                    fx_x = sz // 2 + 3 + fx * (sz // 3)
                    pygame.draw.rect(s, (255, 220, 50, alpha),
                                     (fx_x, 2, 3, sz // 2 + 2))
            elif kind == "drink":
                pygame.draw.rect(s, (80, 180, 220, alpha),
                                 (sz // 3, sz // 4, sz, sz + sz // 3),
                                 border_radius=3)
                # Straw
                pygame.draw.line(s, (220, 220, 220, alpha),
                                 (sz, 0), (sz - 2, sz // 4), 2)
            elif kind == "coin_stack":
                for ci in range(3):
                    cy_off = sz + ci * 4 - 8
                    pygame.draw.ellipse(s, (255, 200, 50, alpha),
                                        (sz // 3, cy_off, sz, sz // 2))
                    pygame.draw.ellipse(s, (255, 230, 100, alpha // 2),
                                        (sz // 3 + 2, cy_off, sz - 4, sz // 4))
            else:  # star
                # Five-pointed star
                cx_s, cy_s = sz, sz
                for i in range(5):
                    angle = i * (math.tau / 5) - math.pi / 2
                    px = cx_s + int(sz * 0.8 * math.cos(angle))
                    py = cy_s + int(sz * 0.8 * math.sin(angle))
                    pygame.draw.line(s, (255, 215, 0, alpha),
                                     (cx_s, cy_s), (px, py), 2)

            rotated = pygame.transform.rotate(s, fi["rot"] * 57.3)
            self.screen.blit(rotated, (x - sz, y - sz))

    def _draw_coin_sparkles(self):
        """Draw sparkle particles rising from the progress bar fill edge."""
        for cs in self._coin_sparkles:
            alpha = int(200 * (cs["life"] / 1.2))
            r = max(1, int(cs["size"]))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cs["color"], min(255, alpha)), (r, r), r)
            self.screen.blit(s, (int(cs["x"]) - r, int(cs["y"]) - r))

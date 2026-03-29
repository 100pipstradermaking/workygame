"""
icons.py — Procedural pixel-art icon sprites for WORKY.
All icons are 16×16 px surfaces drawn once and cached.
"""

import pygame
import math

_cache: dict[str, pygame.Surface] = {}


def _s() -> pygame.Surface:
    return pygame.Surface((16, 16), pygame.SRCALPHA)


def get(name: str) -> pygame.Surface:
    """Return a 16×16 icon Surface by name (cached)."""
    if name not in _cache:
        fn = _DRAW_MAP.get(name)
        if fn:
            _cache[name] = fn()
        else:
            _cache[name] = _draw_placeholder()
    return _cache[name]


def get_scaled(name: str, size: int) -> pygame.Surface:
    """Return icon scaled to size×size."""
    key = f"{name}_{size}"
    if key not in _cache:
        base = get(name)
        _cache[key] = pygame.transform.scale(base, (size, size))
    return _cache[key]


# ── Drawing helpers ──────────────────────────────────────────

def _px(surf, x, y, color):
    if 0 <= x < 16 and 0 <= y < 16:
        surf.set_at((x, y), color)


def _rect(surf, x, y, w, h, color):
    pygame.draw.rect(surf, color, (x, y, w, h))


# ── Icon definitions ─────────────────────────────────────────

def _draw_placeholder():
    s = _s()
    pygame.draw.rect(s, (120, 120, 120), (2, 2, 12, 12), 1)
    pygame.draw.line(s, (120, 120, 120), (2, 2), (13, 13))
    return s


def _draw_coin():
    """Gold coin with C."""
    s = _s()
    pygame.draw.circle(s, (255, 210, 50), (8, 8), 7)
    pygame.draw.circle(s, (200, 160, 30), (8, 8), 7, 1)
    pygame.draw.circle(s, (255, 235, 100), (7, 6), 3, 1)  # highlight
    f = pygame.font.SysFont("Consolas", 10, bold=True)
    t = f.render("C", True, (140, 90, 20))
    s.blit(t, t.get_rect(center=(8, 9)))
    return s


def _draw_burger():
    """Burger — top bun, lettuce, patty, cheese, bottom bun."""
    s = _s()
    _rect(s, 4, 3, 8, 2, (220, 170, 70))   # top bun
    _rect(s, 5, 2, 6, 1, (230, 185, 80))    # bun dome
    _rect(s, 3, 5, 10, 1, (60, 180, 60))    # lettuce
    _rect(s, 3, 6, 10, 2, (130, 60, 20))    # patty
    _rect(s, 3, 8, 10, 1, (255, 200, 50))   # cheese
    _rect(s, 4, 9, 8, 2, (200, 150, 60))    # bottom bun
    # sesame seeds
    _px(s, 6, 3, (255, 250, 200))
    _px(s, 9, 3, (255, 250, 200))
    return s


def _draw_fire():
    """Flame / grill icon."""
    s = _s()
    # Outer flame (orange)
    for dx, h in [(-1, 4), (0, 7), (1, 6), (2, 5), (3, 4)]:
        _rect(s, 6 + dx, 12 - h, 2, h, (255, 140, 30))
    # Inner flame (yellow)
    for dx, h in [(0, 4), (1, 3), (2, 2)]:
        _rect(s, 7 + dx, 12 - h, 1, h, (255, 220, 60))
    # Core (white-hot)
    _px(s, 7, 10, (255, 255, 200))
    _px(s, 8, 9, (255, 255, 200))
    # Grill base
    _rect(s, 3, 12, 10, 1, (80, 80, 90))
    _rect(s, 4, 13, 8, 1, (60, 60, 70))
    return s


def _draw_snowflake():
    """Snowflake / cold / fridge."""
    s = _s()
    c = (120, 200, 255)
    # Cross
    _rect(s, 7, 2, 2, 12, c)
    _rect(s, 2, 7, 12, 2, c)
    # Diagonals
    for i in range(5):
        _px(s, 3 + i, 3 + i, c)
        _px(s, 4 + i, 3 + i, c)
        _px(s, 12 - i, 3 + i, c)
        _px(s, 11 - i, 3 + i, c)
    # Center bright
    _rect(s, 7, 7, 2, 2, (200, 240, 255))
    return s


def _draw_fries():
    """French fries in a red box."""
    s = _s()
    # Box
    _rect(s, 4, 8, 8, 5, (220, 50, 40))
    _rect(s, 4, 8, 8, 1, (240, 80, 70))
    # Fries sticking out
    for fx, fy, fh in [(5, 3, 5), (7, 2, 6), (9, 4, 4), (6, 4, 4), (10, 3, 5)]:
        _rect(s, fx, fy, 1, fh, (255, 210, 80))
        _px(s, fx, fy, (255, 230, 120))
    return s


def _draw_knife():
    """Kitchen knife / prep."""
    s = _s()
    # Blade
    for i in range(8):
        _rect(s, 3 + i, 2 + i, 2, 1, (200, 210, 220))
    # Sharp edge highlight
    for i in range(8):
        _px(s, 3 + i, 2 + i, (230, 240, 250))
    # Handle
    _rect(s, 10, 9, 2, 4, (120, 70, 40))
    _rect(s, 11, 9, 1, 4, (100, 55, 30))
    # Guard
    _rect(s, 9, 9, 4, 1, (180, 170, 150))
    return s


def _draw_chair():
    """Chair / seating."""
    s = _s()
    seat = (160, 110, 70)
    dark = (120, 80, 50)
    # Seat
    _rect(s, 4, 7, 8, 2, seat)
    # Back
    _rect(s, 4, 2, 2, 5, seat)
    _rect(s, 10, 2, 2, 5, seat)
    _rect(s, 4, 2, 8, 2, seat)
    # Legs
    _rect(s, 4, 9, 2, 4, dark)
    _rect(s, 10, 9, 2, 4, dark)
    return s


def _draw_neon():
    """Neon sign / lightbulb."""
    s = _s()
    # Glow
    glow = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 80, 200, 40), (8, 7), 7)
    s.blit(glow, (0, 0))
    # Bulb
    pygame.draw.circle(s, (255, 220, 100), (8, 6), 4)
    pygame.draw.circle(s, (255, 255, 200), (7, 5), 2)  # highlight
    # Base
    _rect(s, 7, 10, 2, 2, (180, 180, 180))
    _rect(s, 6, 12, 4, 1, (160, 160, 160))
    # Rays
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = math.radians(angle)
        ex = int(8 + math.cos(rad) * 6)
        ey = int(6 + math.sin(rad) * 6)
        _px(s, ex, ey, (255, 240, 150))
    return s


def _draw_floor():
    """Checkerboard floor tile."""
    s = _s()
    for ty in range(4):
        for tx in range(4):
            c1 = (180, 160, 130) if (tx + ty) % 2 == 0 else (140, 120, 100)
            _rect(s, tx * 4, ty * 4, 4, 4, c1)
    # Border
    pygame.draw.rect(s, (100, 85, 70), (0, 0, 16, 16), 1)
    return s


def _draw_paint():
    """Paint palette / art."""
    s = _s()
    # Palette shape (oval)
    pygame.draw.ellipse(s, (200, 170, 120), (1, 4, 14, 10))
    pygame.draw.ellipse(s, (180, 150, 100), (1, 4, 14, 10), 1)
    # Paint dots
    for cx, cy, col in [(5, 7, (255, 60, 60)), (8, 6, (60, 60, 255)),
                         (11, 7, (60, 200, 60)), (7, 10, (255, 220, 50)),
                         (10, 10, (200, 60, 200))]:
        pygame.draw.circle(s, col, (cx, cy), 1)
    # Thumb hole
    pygame.draw.circle(s, (160, 130, 90), (4, 10), 2)
    return s


def _draw_music():
    """Music note."""
    s = _s()
    c = (200, 130, 255)
    # Note head
    pygame.draw.ellipse(s, c, (3, 9, 4, 3))
    pygame.draw.ellipse(s, c, (9, 7, 4, 3))
    # Stems
    _rect(s, 6, 3, 1, 7, c)
    _rect(s, 12, 1, 1, 7, c)
    # Beam
    _rect(s, 6, 3, 7, 2, c)
    return s


def _draw_ac():
    """Air conditioning unit."""
    s = _s()
    # Body
    _rect(s, 2, 4, 12, 8, (200, 220, 240))
    _rect(s, 2, 4, 12, 8, (170, 190, 210))
    pygame.draw.rect(s, (150, 170, 190), (2, 4, 12, 8), 1)
    # Grille lines
    for gy in [6, 8, 10]:
        _rect(s, 4, gy, 8, 1, (160, 180, 200))
    # Mount
    _rect(s, 3, 3, 2, 1, (120, 120, 130))
    _rect(s, 11, 3, 2, 1, (120, 120, 130))
    # LED
    _px(s, 12, 5, (0, 220, 0))
    return s


def _draw_megaphone():
    """Megaphone / ad / announce."""
    s = _s()
    c = (255, 100, 80)
    # Cone
    pts = [(4, 5), (12, 2), (12, 12), (4, 9)]
    pygame.draw.polygon(s, c, pts)
    # Opening
    _rect(s, 12, 3, 2, 9, (220, 80, 60))
    # Handle
    _rect(s, 2, 6, 3, 2, (180, 160, 120))
    # Sound waves
    for wx in [14, 15]:
        for wy in [4, 7, 10]:
            _px(s, wx, wy, (255, 200, 150))
    return s


def _draw_scooter():
    """Delivery scooter."""
    s = _s()
    body = (100, 180, 100)
    # Body
    _rect(s, 4, 5, 7, 4, body)
    _rect(s, 3, 6, 2, 3, body)
    # Seat
    _rect(s, 6, 4, 4, 1, (60, 60, 70))
    # Wheels
    pygame.draw.circle(s, (50, 50, 55), (5, 12), 2)
    pygame.draw.circle(s, (50, 50, 55), (11, 12), 2)
    pygame.draw.circle(s, (180, 180, 180), (5, 12), 1)
    pygame.draw.circle(s, (180, 180, 180), (11, 12), 1)
    # Handlebar
    _rect(s, 3, 4, 1, 3, (140, 140, 150))
    # Delivery box
    _rect(s, 8, 2, 4, 3, (200, 80, 60))
    return s


def _draw_building():
    """Building / franchise."""
    s = _s()
    # Main building
    _rect(s, 3, 4, 10, 10, (160, 150, 130))
    _rect(s, 3, 4, 10, 1, (180, 170, 150))
    # Windows
    for wx in [5, 9]:
        for wy in [6, 9]:
            _rect(s, wx, wy, 2, 2, (100, 180, 255))
    # Door
    _rect(s, 7, 11, 2, 3, (120, 80, 50))
    # Roof
    pts = [(2, 4), (8, 1), (14, 4)]
    pygame.draw.polygon(s, (180, 60, 50), pts)
    return s


def _draw_crown():
    """Crown / VIP."""
    s = _s()
    gold = (255, 215, 0)
    dark = (200, 170, 0)
    # Base band
    _rect(s, 3, 9, 10, 3, gold)
    _rect(s, 3, 12, 10, 1, dark)
    # Points
    pts = [(3, 9), (3, 5), (5, 7), (8, 3), (11, 7), (13, 5), (13, 9)]
    pygame.draw.polygon(s, gold, pts)
    pygame.draw.polygon(s, dark, pts, 1)
    # Jewels
    _px(s, 5, 7, (255, 50, 50))
    _px(s, 8, 5, (50, 50, 255))
    _px(s, 11, 7, (50, 200, 50))
    # Jewels on band
    for jx in [5, 8, 11]:
        _px(s, jx, 10, (255, 100, 100))
    return s


def _draw_star():
    """5-point star."""
    s = _s()
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 7 if i % 2 == 0 else 3
        pts.append((8 + r * math.cos(angle), 8 + r * math.sin(angle)))
    pygame.draw.polygon(s, (255, 210, 50), pts)
    pygame.draw.polygon(s, (200, 160, 30), pts, 1)
    return s


def _draw_trophy():
    """Trophy cup."""
    s = _s()
    gold = (255, 210, 50)
    dark = (200, 160, 30)
    # Cup body
    _rect(s, 4, 2, 8, 6, gold)
    _rect(s, 5, 8, 6, 1, gold)
    # Handles
    _rect(s, 2, 3, 2, 3, gold)
    _rect(s, 12, 3, 2, 3, gold)
    # Stem
    _rect(s, 7, 9, 2, 3, dark)
    # Base
    _rect(s, 5, 12, 6, 2, gold)
    # Highlight
    _rect(s, 5, 3, 1, 4, (255, 240, 120))
    return s


def _draw_person():
    """Person / staff icon."""
    s = _s()
    skin = (220, 180, 140)
    shirt = (200, 120, 40)
    # Head
    pygame.draw.circle(s, skin, (8, 4), 3)
    # Body
    _rect(s, 5, 7, 6, 5, shirt)
    # Legs
    _rect(s, 5, 12, 2, 3, (50, 45, 55))
    _rect(s, 9, 12, 2, 3, (50, 45, 55))
    # Arms
    _rect(s, 3, 7, 2, 4, shirt)
    _rect(s, 11, 7, 2, 4, shirt)
    return s


def _draw_chef_hat():
    """Chef hat."""
    s = _s()
    w = (250, 250, 255)
    # Puffy top
    pygame.draw.circle(s, w, (8, 4), 4)
    pygame.draw.circle(s, w, (5, 5), 3)
    pygame.draw.circle(s, w, (11, 5), 3)
    # Band
    _rect(s, 4, 7, 8, 3, w)
    _rect(s, 4, 9, 8, 1, (220, 220, 230))
    return s


def _draw_pot():
    """Cooking pot / kitchen."""
    s = _s()
    body = (140, 140, 150)
    # Pot body
    _rect(s, 3, 6, 10, 7, body)
    pygame.draw.rect(s, (120, 120, 130), (3, 6, 10, 7), 1)
    # Rim
    _rect(s, 2, 6, 12, 1, (180, 180, 190))
    # Handles
    _rect(s, 1, 7, 2, 2, (160, 160, 170))
    _rect(s, 13, 7, 2, 2, (160, 160, 170))
    # Lid
    _rect(s, 3, 5, 10, 1, (170, 170, 180))
    _rect(s, 6, 3, 4, 2, (180, 180, 190))
    # Steam
    for sx, sy in [(6, 1), (8, 0), (10, 1)]:
        _px(s, sx, sy, (200, 200, 220))
    return s


def _draw_paintbrush():
    """Paintbrush / design."""
    s = _s()
    # Handle
    for i in range(7):
        _rect(s, 2 + i, 9 - i, 2, 2, (180, 140, 80))
    # Ferrule
    _rect(s, 8, 3, 2, 2, (180, 180, 190))
    # Bristles
    _rect(s, 10, 1, 3, 3, (60, 140, 220))
    _px(s, 11, 1, (80, 160, 240))
    return s


def _draw_chart():
    """Bar chart / business."""
    s = _s()
    # Axes
    _rect(s, 3, 2, 1, 12, (180, 180, 190))
    _rect(s, 3, 13, 11, 1, (180, 180, 190))
    # Bars
    bars = [(5, 5, (80, 200, 120)), (7, 3, (100, 180, 255)),
            (9, 7, (255, 180, 80)), (11, 2, (200, 100, 255))]
    for bx, bh, bc in bars:
        _rect(s, bx, 13 - bh, 2, bh, bc)
    return s


def _draw_speed():
    """Speed / lightning bolt."""
    s = _s()
    pts = [(9, 1), (5, 7), (8, 7), (6, 15), (11, 6), (8, 6)]
    pygame.draw.polygon(s, (255, 220, 60), pts)
    pygame.draw.polygon(s, (200, 170, 30), pts, 1)
    return s


def _draw_heart():
    """Heart / health / happiness."""
    s = _s()
    c = (255, 70, 70)
    pygame.draw.circle(s, c, (5, 5), 3)
    pygame.draw.circle(s, c, (11, 5), 3)
    pts = [(2, 6), (8, 14), (14, 6)]
    pygame.draw.polygon(s, c, pts)
    _px(s, 5, 4, (255, 140, 140))  # highlight
    return s


def _draw_shop_bag():
    """Shopping bag."""
    s = _s()
    bag = (200, 160, 100)
    # Bag body
    _rect(s, 4, 6, 8, 8, bag)
    pygame.draw.rect(s, (160, 120, 70), (4, 6, 8, 8), 1)
    # Handle
    pygame.draw.arc(s, (160, 120, 70), (5, 2, 6, 6), 0.1, 3.1, 2)
    # Label
    _rect(s, 6, 9, 4, 2, (255, 210, 80))
    return s


def _draw_sparkle():
    """Sparkle / effect."""
    s = _s()
    c = (255, 240, 100)
    # Cross sparkle
    _rect(s, 7, 2, 2, 12, c)
    _rect(s, 2, 7, 12, 2, c)
    # Diag
    for i in range(3):
        _px(s, 4 + i, 4 + i, c)
        _px(s, 11 - i, 4 + i, c)
        _px(s, 4 + i, 11 - i, c)
        _px(s, 11 - i, 11 - i, c)
    # Center bright
    _rect(s, 7, 7, 2, 2, (255, 255, 255))
    return s


def _draw_arrow_up():
    """Up arrow / upgrade."""
    s = _s()
    c = (80, 230, 120)
    pts = [(8, 2), (13, 8), (10, 8), (10, 14), (6, 14), (6, 8), (3, 8)]
    pygame.draw.polygon(s, c, pts)
    pygame.draw.polygon(s, (50, 180, 80), pts, 1)
    return s


def _draw_medal_gold():
    s = _s()
    pygame.draw.circle(s, (255, 215, 0), (8, 6), 5)
    pygame.draw.circle(s, (200, 170, 0), (8, 6), 5, 1)
    _rect(s, 6, 11, 4, 3, (255, 50, 50))
    _px(s, 7, 5, (255, 240, 120))
    f = pygame.font.SysFont("Consolas", 8, bold=True)
    t = f.render("1", True, (140, 100, 0))
    s.blit(t, t.get_rect(center=(8, 7)))
    return s


def _draw_medal_silver():
    s = _s()
    pygame.draw.circle(s, (192, 192, 192), (8, 6), 5)
    pygame.draw.circle(s, (140, 140, 140), (8, 6), 5, 1)
    _rect(s, 6, 11, 4, 3, (80, 80, 200))
    f = pygame.font.SysFont("Consolas", 8, bold=True)
    t = f.render("2", True, (80, 80, 80))
    s.blit(t, t.get_rect(center=(8, 7)))
    return s


def _draw_medal_bronze():
    s = _s()
    pygame.draw.circle(s, (205, 127, 50), (8, 6), 5)
    pygame.draw.circle(s, (160, 95, 30), (8, 6), 5, 1)
    _rect(s, 6, 11, 4, 3, (60, 120, 60))
    f = pygame.font.SysFont("Consolas", 8, bold=True)
    t = f.render("3", True, (100, 60, 20))
    s.blit(t, t.get_rect(center=(8, 7)))
    return s


def _draw_door():
    """Door / exit."""
    s = _s()
    _rect(s, 4, 2, 8, 12, (120, 80, 50))
    _rect(s, 4, 2, 8, 12, (100, 65, 40))
    pygame.draw.rect(s, (90, 55, 30), (4, 2, 8, 12), 1)
    # Handle
    _px(s, 10, 8, (200, 180, 100))
    _px(s, 10, 9, (200, 180, 100))
    # Arrow out
    _rect(s, 0, 7, 4, 2, (80, 230, 120))
    pts = [(0, 6), (0, 10), (-2, 8)]  # too small, skip polygon
    return s


def _draw_play():
    """Play / start triangle."""
    s = _s()
    pts = [(5, 3), (13, 8), (5, 13)]
    pygame.draw.polygon(s, (80, 230, 120), pts)
    pygame.draw.polygon(s, (50, 180, 80), pts, 1)
    return s


def _draw_continue():
    """Continue / save arrow."""
    s = _s()
    # Floppy + arrow
    _rect(s, 3, 3, 10, 10, (80, 140, 220))
    _rect(s, 5, 3, 6, 4, (60, 60, 70))
    _rect(s, 5, 9, 6, 3, (240, 240, 245))
    _rect(s, 6, 10, 4, 1, (180, 180, 190))
    return s


def _draw_leaderboard_icon():
    """Podium icon."""
    s = _s()
    # Podiums (1st tall, 2nd mid, 3rd short)
    _rect(s, 6, 4, 4, 10, (255, 215, 0))   # 1st
    _rect(s, 1, 7, 5, 7, (192, 192, 192))   # 2nd
    _rect(s, 10, 9, 5, 5, (205, 127, 50))   # 3rd
    # Numbers
    f = pygame.font.SysFont("Consolas", 7, bold=True)
    for txt, x, y in [("1", 8, 6), ("2", 3, 9), ("3", 12, 11)]:
        t = f.render(txt, True, (40, 40, 50))
        s.blit(t, t.get_rect(center=(x, y)))
    return s


def _draw_quit():
    """X / quit."""
    s = _s()
    c = (220, 70, 70)
    for i in range(10):
        _rect(s, 3 + i, 3 + i, 2, 2, c)
        _rect(s, 13 - i, 3 + i, 2, 2, c)
    return s


def _draw_prestige():
    """Prestige / rebirth star."""
    s = _s()
    # Circular arrows
    pygame.draw.arc(s, (180, 120, 255), (2, 2, 12, 12), 0.3, 2.8, 2)
    pygame.draw.arc(s, (180, 120, 255), (2, 2, 12, 12), 3.5, 5.8, 2)
    # Arrow heads
    _rect(s, 11, 3, 2, 2, (180, 120, 255))
    _rect(s, 3, 11, 2, 2, (180, 120, 255))
    # Star center
    _px(s, 7, 7, (255, 210, 80))
    _px(s, 8, 7, (255, 210, 80))
    _px(s, 7, 8, (255, 210, 80))
    _px(s, 8, 8, (255, 210, 80))
    return s


# ── Name → draw function mapping ────────────────────────────

_DRAW_MAP = {
    "coin":          _draw_coin,
    "burger":        _draw_burger,
    "fire":          _draw_fire,
    "snowflake":     _draw_snowflake,
    "fries":         _draw_fries,
    "knife":         _draw_knife,
    "chair":         _draw_chair,
    "neon":          _draw_neon,
    "floor":         _draw_floor,
    "paint":         _draw_paint,
    "music":         _draw_music,
    "ac":            _draw_ac,
    "megaphone":     _draw_megaphone,
    "scooter":       _draw_scooter,
    "building":      _draw_building,
    "crown":         _draw_crown,
    "star":          _draw_star,
    "trophy":        _draw_trophy,
    "person":        _draw_person,
    "chef_hat":      _draw_chef_hat,
    "pot":           _draw_pot,
    "paintbrush":    _draw_paintbrush,
    "chart":         _draw_chart,
    "speed":         _draw_speed,
    "heart":         _draw_heart,
    "shop_bag":      _draw_shop_bag,
    "sparkle":       _draw_sparkle,
    "arrow_up":      _draw_arrow_up,
    "medal_gold":    _draw_medal_gold,
    "medal_silver":  _draw_medal_silver,
    "medal_bronze":  _draw_medal_bronze,
    "door":          _draw_door,
    "play":          _draw_play,
    "continue":      _draw_continue,
    "leaderboard":   _draw_leaderboard_icon,
    "quit":          _draw_quit,
    "prestige":      _draw_prestige,
}

# Map shop item IDs to icon names
ITEM_ICONS = {
    "kitchen_oven":   "fire",
    "kitchen_fridge": "snowflake",
    "kitchen_fryer":  "fries",
    "kitchen_prep":   "knife",
    "design_seats":   "chair",
    "design_neon":    "neon",
    "design_floor":   "floor",
    "design_paint":   "paint",
    "design_music":   "music",
    "design_ac":      "ac",
    "biz_ads":        "megaphone",
    "biz_delivery":   "scooter",
    "biz_franchise":  "building",
    "biz_vip":        "crown",
}

# Map shop tab names to icon names
TAB_ICONS = {
    "Staff":    "person",
    "Kitchen":  "pot",
    "Design":   "paintbrush",
    "Business": "chart",
}

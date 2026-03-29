"""
icons.py — Procedural pixel-art icon sprites for WORKY.
All icons are 16×16 px surfaces drawn once and cached.
Style: clean outlines, bold saturated fills, 1-2 tone shading.
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


def _outline_rect(surf, x, y, w, h, fill, border):
    """Filled rect with 1px border — classic pixel icon style."""
    pygame.draw.rect(surf, fill, (x, y, w, h))
    pygame.draw.rect(surf, border, (x, y, w, h), 1)


# ── Icon definitions ─────────────────────────────────────────

def _draw_placeholder():
    s = _s()
    _outline_rect(s, 2, 2, 12, 12, (60, 55, 75), (100, 95, 115))
    pygame.draw.line(s, (100, 95, 115), (2, 2), (13, 13))
    pygame.draw.line(s, (100, 95, 115), (13, 2), (2, 13))
    return s


def _draw_coin():
    """Shiny gold coin with W for WORKY."""
    s = _s()
    # Shadow
    pygame.draw.circle(s, (160, 120, 10), (8, 9), 7)
    # Main disc
    pygame.draw.circle(s, (255, 200, 40), (8, 8), 7)
    # Outline
    pygame.draw.circle(s, (180, 130, 10), (8, 8), 7, 1)
    # Inner ring
    pygame.draw.circle(s, (220, 170, 20), (8, 8), 5, 1)
    # Top-left highlight arc
    for dx, dy in [(0, -1), (-1, 0), (1, -1), (-1, 1)]:
        _px(s, 6 + dx, 5 + dy, (255, 240, 120))
    # "W" glyph
    for row, cols in [(6, [5, 6, 9, 10]), (7, [5, 6, 9, 10]),
                      (8, [5, 7, 8, 10]), (9, [6, 7, 8, 9]),
                      (10, [6, 7, 8, 9])]:
        for c in cols:
            _px(s, c, row, (140, 90, 0))
    return s


def _draw_burger():
    """Chunky burger with outline."""
    s = _s()
    ol = (80, 45, 10)  # outline
    # Top bun dome
    _rect(s, 5, 2, 6, 1, (240, 190, 80))
    _rect(s, 4, 3, 8, 2, (230, 175, 70))
    _px(s, 5, 2, ol); _px(s, 10, 2, ol)
    _rect(s, 4, 2, 1, 1, ol); _rect(s, 11, 2, 1, 1, ol)
    _px(s, 3, 3, ol); _px(s, 12, 3, ol)
    _px(s, 3, 4, ol); _px(s, 12, 4, ol)
    # Sesame
    _px(s, 6, 3, (255, 250, 210)); _px(s, 9, 3, (255, 250, 210))
    # Lettuce (wavy green)
    for x in range(3, 13):
        _px(s, x, 5, (50, 190, 60) if x % 2 == 0 else (80, 220, 90))
    # Patty
    _rect(s, 3, 6, 10, 2, (120, 55, 15))
    _rect(s, 3, 6, 10, 1, (145, 70, 20))  # highlight top
    # Cheese drip
    _rect(s, 3, 8, 10, 1, (255, 210, 40))
    _px(s, 4, 9, (255, 210, 40)); _px(s, 10, 9, (255, 210, 40))
    # Bottom bun
    _rect(s, 4, 9, 8, 2, (210, 155, 55))
    _rect(s, 4, 9, 8, 1, (225, 175, 70))  # highlight
    # Full outline bottom
    _px(s, 3, 5, ol); _px(s, 12, 5, ol)
    _px(s, 2, 6, ol); _px(s, 13, 6, ol)
    _px(s, 2, 7, ol); _px(s, 13, 7, ol)
    _px(s, 2, 8, ol); _px(s, 13, 8, ol)
    _px(s, 3, 9, ol); _px(s, 12, 9, ol)
    _px(s, 3, 10, ol); _px(s, 12, 10, ol)
    _px(s, 3, 11, ol); _px(s, 12, 11, ol)
    _rect(s, 4, 11, 8, 1, ol)
    return s


def _draw_fire():
    """Flame icon with clean pixel shape."""
    s = _s()
    # Outer flame (red-orange)
    flame_r = (240, 80, 20)
    for x, y in [(7, 3), (8, 3), (6, 4), (7, 4), (8, 4), (9, 4),
                 (5, 5), (6, 5), (9, 5), (10, 5),
                 (5, 6), (10, 6), (4, 7), (11, 7),
                 (4, 8), (11, 8), (4, 9), (11, 9),
                 (5, 10), (10, 10), (5, 11), (10, 11)]:
        _px(s, x, y, flame_r)
    # Mid flame (orange)
    flame_o = (255, 160, 30)
    for x, y in [(7, 4), (8, 4), (6, 5), (7, 5), (8, 5), (9, 5),
                 (6, 6), (7, 6), (8, 6), (9, 6),
                 (5, 7), (6, 7), (9, 7), (10, 7),
                 (5, 8), (6, 8), (9, 8), (10, 8),
                 (6, 9), (9, 9), (6, 10), (9, 10)]:
        _px(s, x, y, flame_o)
    # Inner flame (yellow)
    flame_y = (255, 230, 60)
    for x, y in [(7, 6), (8, 6), (7, 7), (8, 7),
                 (7, 8), (8, 8), (7, 9), (8, 9),
                 (7, 10), (8, 10)]:
        _px(s, x, y, flame_y)
    # Core (white-hot)
    _px(s, 7, 9, (255, 255, 200)); _px(s, 8, 9, (255, 255, 200))
    _px(s, 7, 10, (255, 255, 220)); _px(s, 8, 10, (255, 255, 220))
    # Grill base
    _outline_rect(s, 3, 12, 10, 2, (70, 70, 80), (50, 50, 60))
    # Grill slits
    for gx in [5, 7, 9, 11]:
        _px(s, gx, 12, (50, 50, 60))
    return s


def _draw_snowflake():
    """Crisp snowflake / fridge."""
    s = _s()
    hi = (180, 230, 255)
    c  = (100, 190, 255)
    dk = (60, 130, 200)
    # Main cross
    _rect(s, 7, 1, 2, 14, c)
    _rect(s, 1, 7, 14, 2, c)
    # Center bright
    _rect(s, 7, 7, 2, 2, hi)
    # Diagonal arms
    for i in range(4):
        _px(s, 3 + i, 3 + i, c); _px(s, 12 - i, 3 + i, c)
        _px(s, 3 + i, 12 - i, c); _px(s, 12 - i, 12 - i, c)
    # Branch tips
    for tx, ty in [(7, 1), (8, 1), (7, 14), (8, 14),
                   (1, 7), (1, 8), (14, 7), (14, 8)]:
        _px(s, tx, ty, hi)
    # Outline hint on tips
    for tx, ty in [(7, 0), (8, 0), (7, 15), (8, 15),
                   (0, 7), (0, 8), (15, 7), (15, 8)]:
        _px(s, tx, ty, dk)
    return s


def _draw_fries():
    """French fries in red carton."""
    s = _s()
    ol = (150, 25, 20)
    # Fries sticking out
    fry = (255, 215, 70)
    fry_hi = (255, 240, 140)
    for fx, fy, fh in [(5, 3, 5), (7, 2, 6), (9, 4, 4), (6, 4, 4), (10, 3, 5)]:
        _rect(s, fx, fy, 1, fh, fry)
        _px(s, fx, fy, fry_hi)
    # Carton
    _outline_rect(s, 4, 8, 8, 6, (220, 45, 35), ol)
    # Carton highlight stripe
    _rect(s, 4, 8, 8, 1, (245, 80, 65))
    # Carton "M" logo
    _px(s, 7, 10, (255, 220, 50)); _px(s, 8, 10, (255, 220, 50))
    _px(s, 6, 11, (255, 220, 50)); _px(s, 9, 11, (255, 220, 50))
    return s


def _draw_knife():
    """Kitchen knife with clean outline."""
    s = _s()
    blade = (210, 220, 230)
    blade_hi = (240, 245, 255)
    blade_dk = (160, 170, 180)
    handle = (140, 80, 40)
    handle_dk = (100, 55, 25)
    # Blade body (diagonal)
    for i in range(8):
        _px(s, 3 + i, 2 + i, blade)
        _px(s, 4 + i, 2 + i, blade)
    # Blade highlight (top edge)
    for i in range(7):
        _px(s, 3 + i, 2 + i, blade_hi)
    # Blade shadow (bottom edge)
    for i in range(7):
        _px(s, 5 + i, 3 + i, blade_dk)
    # Guard
    _rect(s, 9, 9, 1, 3, (180, 175, 160))
    _rect(s, 10, 8, 1, 3, (180, 175, 160))
    # Handle
    _rect(s, 10, 10, 2, 4, handle)
    _rect(s, 11, 10, 1, 4, handle_dk)
    _px(s, 10, 13, (120, 65, 30))  # handle end
    return s


def _draw_chair():
    """Chair with clean outline."""
    s = _s()
    wood = (180, 130, 75)
    wood_dk = (130, 90, 50)
    ol = (90, 60, 30)
    # Back rest
    _outline_rect(s, 4, 1, 8, 3, wood, ol)
    _rect(s, 5, 2, 6, 1, (200, 150, 90))  # highlight
    # Back legs/posts
    _rect(s, 4, 4, 2, 4, wood_dk)
    _rect(s, 10, 4, 2, 4, wood_dk)
    # Seat
    _outline_rect(s, 3, 7, 10, 2, wood, ol)
    _rect(s, 4, 7, 8, 1, (200, 150, 90))  # highlight
    # Front legs
    _rect(s, 4, 9, 2, 5, wood_dk)
    _rect(s, 10, 9, 2, 5, wood_dk)
    _px(s, 4, 9, ol); _px(s, 5, 9, ol)
    _px(s, 10, 9, ol); _px(s, 11, 9, ol)
    _px(s, 4, 13, ol); _px(s, 5, 13, ol)
    _px(s, 10, 13, ol); _px(s, 11, 13, ol)
    return s


def _draw_neon():
    """Neon lightbulb with glow."""
    s = _s()
    # Soft glow halo
    glow = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 100, 220, 35), (8, 6), 7)
    s.blit(glow, (0, 0))
    # Bulb glass
    pygame.draw.circle(s, (255, 235, 120), (8, 6), 4)
    pygame.draw.circle(s, (200, 170, 50), (8, 6), 4, 1)
    # Filament
    _px(s, 7, 6, (255, 200, 60)); _px(s, 8, 5, (255, 200, 60))
    _px(s, 9, 6, (255, 200, 60))
    # Highlight
    _px(s, 6, 4, (255, 255, 220)); _px(s, 7, 4, (255, 255, 220))
    # Screw base
    _outline_rect(s, 6, 10, 4, 1, (190, 190, 200), (140, 140, 150))
    _outline_rect(s, 7, 11, 2, 2, (170, 170, 180), (130, 130, 140))
    # Rays
    ray = (255, 240, 120)
    for ox, oy in [(-6, 0), (6, 0), (0, -5), (-4, -4), (4, -4),
                   (-5, 3), (5, 3)]:
        _px(s, 8 + ox, 6 + oy, ray)
    return s


def _draw_floor():
    """Checkerboard floor tile with outline."""
    s = _s()
    c1, c2 = (195, 175, 145), (155, 135, 110)
    ol = (110, 95, 75)
    for ty in range(4):
        for tx in range(4):
            c = c1 if (tx + ty) % 2 == 0 else c2
            _rect(s, tx * 4, ty * 4, 4, 4, c)
    # Grid lines
    for g in [4, 8, 12]:
        _rect(s, g, 0, 1, 16, ol)
        _rect(s, 0, g, 16, 1, ol)
    pygame.draw.rect(s, ol, (0, 0, 16, 16), 1)
    return s


def _draw_paint():
    """Paint palette with bold dots."""
    s = _s()
    pal = (215, 185, 135)
    ol  = (160, 130, 85)
    # Palette body
    pygame.draw.ellipse(s, pal, (1, 3, 14, 11))
    pygame.draw.ellipse(s, ol, (1, 3, 14, 11), 1)
    # Highlight
    pygame.draw.ellipse(s, (235, 210, 165), (3, 4, 6, 4))
    # Thumb hole
    pygame.draw.circle(s, (140, 110, 70), (4, 10), 2)
    pygame.draw.circle(s, ol, (4, 10), 2, 1)
    # Paint blobs (bold colors)
    for cx, cy, col in [(6, 6, (240, 50, 50)), (9, 5, (50, 80, 240)),
                         (12, 7, (50, 200, 70)), (8, 9, (255, 200, 40)),
                         (11, 10, (200, 50, 200))]:
        pygame.draw.circle(s, col, (cx, cy), 1)
    return s


def _draw_music():
    """Double music note."""
    s = _s()
    c  = (210, 130, 255)
    dk = (160, 80, 210)
    # Note heads
    pygame.draw.ellipse(s, c, (3, 10, 4, 3))
    pygame.draw.ellipse(s, dk, (3, 10, 4, 3), 1)
    pygame.draw.ellipse(s, c, (9, 8, 4, 3))
    pygame.draw.ellipse(s, dk, (9, 8, 4, 3), 1)
    # Stems
    _rect(s, 6, 2, 1, 9, c)
    _rect(s, 12, 1, 1, 8, c)
    # Beam
    _rect(s, 6, 2, 7, 2, c)
    _rect(s, 6, 2, 7, 1, (230, 170, 255))  # highlight
    return s


def _draw_ac():
    """Air conditioning unit with vents."""
    s = _s()
    body = (190, 210, 230)
    ol   = (130, 150, 170)
    # Wall mounts
    _rect(s, 4, 3, 2, 1, (140, 140, 150))
    _rect(s, 10, 3, 2, 1, (140, 140, 150))
    # Body
    _outline_rect(s, 2, 4, 12, 7, body, ol)
    # Top highlight
    _rect(s, 3, 4, 10, 1, (220, 235, 250))
    # Vent slits
    for gy in [6, 8, 10]:
        _rect(s, 4, gy, 8, 1, ol)
    # LED indicator
    _px(s, 12, 5, (0, 230, 80))
    _px(s, 11, 5, (0, 180, 60))
    # Cold air wisps below
    for wx, wy in [(5, 12), (8, 13), (11, 12)]:
        _px(s, wx, wy, (150, 210, 255))
        _px(s, wx, wy - 1, (120, 190, 240))
    return s


def _draw_megaphone():
    """Megaphone with sound waves."""
    s = _s()
    c  = (245, 90, 65)
    dk = (190, 55, 35)
    # Handle
    _outline_rect(s, 1, 6, 3, 3, (180, 150, 110), (130, 100, 60))
    # Cone body
    pts = [(4, 5), (11, 2), (11, 12), (4, 9)]
    pygame.draw.polygon(s, c, pts)
    pygame.draw.polygon(s, dk, pts, 1)
    # Cone opening
    _outline_rect(s, 11, 2, 2, 11, dk, (150, 40, 25))
    # Sound waves
    wave = (255, 180, 130)
    for wy in [4, 7, 10]:
        _px(s, 14, wy, wave)
    _px(s, 15, 5, (255, 200, 160))
    _px(s, 15, 9, (255, 200, 160))
    return s


def _draw_scooter():
    """Delivery scooter with box."""
    s = _s()
    body = (90, 180, 110)
    dk   = (55, 130, 70)
    # Delivery box (on back)
    _outline_rect(s, 8, 1, 5, 4, (220, 75, 50), (160, 45, 25))
    _rect(s, 9, 2, 3, 1, (240, 100, 70))  # highlight
    # Body frame
    _rect(s, 4, 5, 8, 4, body)
    _rect(s, 3, 6, 2, 3, body)
    _rect(s, 4, 5, 8, 1, (120, 210, 140))  # highlight
    # Outline
    _px(s, 3, 5, dk); _px(s, 12, 5, dk)
    _px(s, 2, 6, dk); _px(s, 2, 8, dk)
    _px(s, 12, 8, dk)
    # Seat
    _rect(s, 6, 4, 4, 1, (55, 55, 65))
    # Handlebar
    _rect(s, 2, 4, 2, 1, (160, 160, 170))
    _rect(s, 2, 3, 1, 2, (160, 160, 170))
    # Wheels
    pygame.draw.circle(s, (45, 45, 50), (5, 12), 3)
    pygame.draw.circle(s, (180, 180, 190), (5, 12), 1)
    pygame.draw.circle(s, (45, 45, 50), (11, 12), 3)
    pygame.draw.circle(s, (180, 180, 190), (11, 12), 1)
    return s


def _draw_building():
    """Building / franchise with clean outline."""
    s = _s()
    wall = (170, 160, 140)
    ol   = (100, 90, 75)
    # Building body
    _outline_rect(s, 3, 5, 10, 10, wall, ol)
    # Roof
    pts = [(2, 5), (8, 1), (14, 5)]
    pygame.draw.polygon(s, (200, 60, 45), pts)
    pygame.draw.polygon(s, (150, 35, 20), pts, 1)
    # Roof highlight
    _px(s, 5, 3, (230, 90, 70)); _px(s, 6, 3, (230, 90, 70))
    # Windows (lit)
    for wx, wy in [(5, 7), (9, 7), (5, 10)]:
        _outline_rect(s, wx, wy, 2, 2, (100, 190, 255), ol)
    # Door
    _outline_rect(s, 9, 10, 2, 5, (130, 90, 50), ol)
    _px(s, 10, 12, (220, 200, 100))  # doorknob
    return s


def _draw_crown():
    """Royal crown with jewels."""
    s = _s()
    gold = (255, 215, 0)
    hi   = (255, 240, 100)
    dk   = (190, 150, 0)
    # Crown points
    pts = [(2, 10), (2, 5), (5, 7), (8, 2), (11, 7), (14, 5), (14, 10)]
    pygame.draw.polygon(s, gold, pts)
    pygame.draw.polygon(s, dk, pts, 1)
    # Base band
    _outline_rect(s, 2, 10, 12, 3, gold, dk)
    # Top highlight on points
    _px(s, 3, 6, hi); _px(s, 8, 3, hi); _px(s, 13, 6, hi)
    # Jewels on points
    _px(s, 5, 7, (255, 40, 40))   # ruby
    _px(s, 8, 4, (40, 60, 255))   # sapphire
    _px(s, 11, 7, (40, 220, 60))  # emerald
    # Jewels on band
    _px(s, 5, 11, (255, 80, 80))
    _px(s, 8, 11, (80, 80, 255))
    _px(s, 11, 11, (80, 220, 80))
    # Band highlight
    _rect(s, 3, 10, 10, 1, hi)
    return s


def _draw_star():
    """Crisp 5-point star."""
    s = _s()
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 7 if i % 2 == 0 else 3
        pts.append((8 + r * math.cos(angle), 8 + r * math.sin(angle)))
    pygame.draw.polygon(s, (255, 215, 40), pts)
    pygame.draw.polygon(s, (190, 150, 10), pts, 1)
    # Inner highlight
    _px(s, 7, 6, (255, 245, 150))
    _px(s, 8, 6, (255, 245, 150))
    _px(s, 7, 7, (255, 240, 120))
    return s


def _draw_trophy():
    """Trophy cup with detail."""
    s = _s()
    gold = (255, 210, 40)
    dk   = (190, 150, 10)
    hi   = (255, 240, 110)
    # Cup body
    _outline_rect(s, 4, 2, 8, 6, gold, dk)
    _rect(s, 5, 3, 1, 4, hi)  # left highlight
    # Tapered bottom
    _rect(s, 5, 8, 6, 1, gold)
    # Handles
    _rect(s, 2, 3, 2, 1, gold); _rect(s, 2, 3, 1, 3, gold)
    _rect(s, 2, 5, 2, 1, gold)
    _rect(s, 12, 3, 2, 1, gold); _rect(s, 13, 3, 1, 3, gold)
    _rect(s, 12, 5, 2, 1, gold)
    # Stem
    _rect(s, 7, 9, 2, 2, dk)
    # Base
    _outline_rect(s, 5, 11, 6, 3, gold, dk)
    _rect(s, 6, 11, 4, 1, hi)  # base highlight
    # Star on cup
    _px(s, 8, 4, (255, 255, 200))
    _px(s, 7, 5, (255, 255, 200)); _px(s, 9, 5, (255, 255, 200))
    return s


def _draw_person():
    """Person icon with clean pixel style."""
    s = _s()
    skin  = (230, 190, 150)
    skin_dk = (200, 160, 120)
    shirt = (220, 130, 40)
    shirt_dk = (180, 95, 20)
    pants = (55, 50, 65)
    # Head
    pygame.draw.circle(s, skin, (8, 4), 3)
    pygame.draw.circle(s, skin_dk, (8, 4), 3, 1)
    _px(s, 7, 3, (245, 210, 175))  # face highlight
    # Hair
    _rect(s, 6, 1, 4, 2, (70, 50, 30))
    # Body
    _outline_rect(s, 5, 7, 6, 4, shirt, shirt_dk)
    _rect(s, 6, 7, 4, 1, (240, 150, 60))  # collar highlight
    # Arms
    _rect(s, 3, 7, 2, 4, shirt)
    _rect(s, 11, 7, 2, 4, shirt)
    _px(s, 3, 10, skin); _px(s, 12, 10, skin)  # hands
    # Legs
    _rect(s, 5, 11, 2, 4, pants)
    _rect(s, 9, 11, 2, 4, pants)
    return s


def _draw_chef_hat():
    """Chef hat (toque)."""
    s = _s()
    w  = (250, 250, 255)
    sh = (215, 215, 225)
    ol = (180, 180, 195)
    # Puffy top
    pygame.draw.circle(s, w, (8, 4), 4)
    pygame.draw.circle(s, w, (5, 5), 3)
    pygame.draw.circle(s, w, (11, 5), 3)
    # Outline
    pygame.draw.circle(s, ol, (8, 4), 4, 1)
    pygame.draw.circle(s, ol, (5, 5), 3, 1)
    pygame.draw.circle(s, ol, (11, 5), 3, 1)
    # Band
    _outline_rect(s, 4, 7, 8, 3, w, ol)
    _rect(s, 4, 9, 8, 1, sh)
    # Highlight
    _px(s, 7, 2, (255, 255, 255)); _px(s, 8, 2, (255, 255, 255))
    return s


def _draw_pot():
    """Cooking pot with steam."""
    s = _s()
    body = (150, 150, 165)
    dk   = (110, 110, 125)
    hi   = (185, 185, 200)
    ol   = (85, 85, 100)
    # Steam puffs
    _px(s, 6, 1, (200, 200, 220)); _px(s, 7, 0, (180, 180, 200))
    _px(s, 9, 1, (200, 200, 220)); _px(s, 10, 0, (180, 180, 200))
    # Lid knob
    _outline_rect(s, 6, 2, 4, 2, hi, ol)
    # Lid
    _rect(s, 2, 4, 12, 1, hi)
    _px(s, 2, 4, ol); _px(s, 13, 4, ol)
    # Rim
    _outline_rect(s, 2, 5, 12, 1, hi, ol)
    # Pot body
    _outline_rect(s, 3, 6, 10, 7, body, ol)
    _rect(s, 4, 6, 1, 6, hi)  # left highlight
    _rect(s, 11, 6, 1, 6, dk)  # right shadow
    # Handles
    _rect(s, 1, 7, 2, 2, dk)
    _px(s, 1, 7, ol); _px(s, 1, 8, ol)
    _rect(s, 13, 7, 2, 2, dk)
    _px(s, 14, 7, ol); _px(s, 14, 8, ol)
    return s


def _draw_paintbrush():
    """Paintbrush with colored tip."""
    s = _s()
    handle = (200, 160, 90)
    h_dk   = (160, 120, 60)
    # Handle (diagonal)
    for i in range(7):
        _px(s, 1 + i, 13 - i, handle)
        _px(s, 2 + i, 13 - i, handle)
        _px(s, 1 + i, 14 - i, h_dk)
    # Ferrule (metal band)
    _px(s, 8, 6, (190, 190, 200)); _px(s, 9, 6, (190, 190, 200))
    _px(s, 8, 5, (190, 190, 200)); _px(s, 9, 5, (190, 190, 200))
    # Bristles (blue paint)
    brush = (60, 140, 230)
    brush_hi = (100, 175, 250)
    _rect(s, 10, 3, 3, 3, brush)
    _px(s, 12, 2, brush); _px(s, 13, 1, brush)
    _px(s, 10, 3, brush_hi); _px(s, 11, 2, brush_hi)
    # Paint dab
    _px(s, 13, 1, (50, 120, 210))
    _px(s, 14, 0, (40, 100, 190))
    return s


def _draw_chart():
    """Bar chart with rising bars."""
    s = _s()
    ol = (140, 140, 155)
    # Axes
    _rect(s, 2, 1, 1, 13, ol)
    _rect(s, 2, 13, 12, 1, ol)
    # Axis arrow tip
    _px(s, 1, 2, ol); _px(s, 3, 2, ol); _px(s, 2, 1, ol)
    # Bars (rising pattern)
    bars = [(4, 6, (80, 210, 130), (50, 170, 90)),
            (7, 4, (80, 180, 255), (40, 130, 210)),
            (10, 8, (255, 180, 60), (210, 140, 30)),
            (13, 2, (210, 100, 255), (160, 60, 210))]
    for bx, bh, bc, bdk in bars:
        h = 13 - bh
        _rect(s, bx, bh, 2, h, bc)
        _px(s, bx, bh, bdk)       # top outline
        _px(s, bx + 1, bh, bdk)
        _rect(s, bx + 1, bh + 1, 1, h - 1, bdk)  # right shadow
    return s


def _draw_speed():
    """Lightning bolt — clean pixel art."""
    s = _s()
    bolt = (255, 225, 50)
    dk   = (200, 170, 20)
    # Bolt shape
    pts = [(9, 0), (4, 7), (7, 7), (5, 15), (12, 6), (8, 6)]
    pygame.draw.polygon(s, bolt, pts)
    pygame.draw.polygon(s, dk, pts, 1)
    # Core highlight
    _px(s, 7, 5, (255, 255, 180))
    _px(s, 8, 4, (255, 255, 180))
    _px(s, 6, 8, (255, 255, 180))
    return s


def _draw_heart():
    """Bold pixel heart."""
    s = _s()
    c  = (255, 55, 70)
    dk = (200, 25, 40)
    # Left and right bumps
    pygame.draw.circle(s, c, (5, 5), 4)
    pygame.draw.circle(s, c, (11, 5), 4)
    # Bottom triangle
    pts = [(1, 6), (8, 14), (15, 6)]
    pygame.draw.polygon(s, c, pts)
    # Outline
    pygame.draw.circle(s, dk, (5, 5), 4, 1)
    pygame.draw.circle(s, dk, (11, 5), 4, 1)
    pygame.draw.polygon(s, dk, pts, 1)
    # Highlight
    _px(s, 4, 3, (255, 140, 150))
    _px(s, 5, 3, (255, 140, 150))
    _px(s, 4, 4, (255, 120, 130))
    return s


def _draw_shop_bag():
    """Shopping bag with crisp outline."""
    s = _s()
    bag = (210, 170, 110)
    dk  = (160, 120, 65)
    ol  = (120, 85, 40)
    # Bag body
    _outline_rect(s, 3, 6, 10, 8, bag, ol)
    _rect(s, 4, 6, 1, 7, (230, 195, 140))  # left highlight
    _rect(s, 12, 6, 1, 7, dk)  # right shadow
    # Handle
    pygame.draw.arc(s, ol, (5, 1, 6, 7), 0.3, 2.9, 2)
    # Label/logo
    _outline_rect(s, 6, 9, 4, 3, (255, 215, 70), (200, 165, 30))
    return s


def _draw_sparkle():
    """4-point sparkle."""
    s = _s()
    c  = (255, 245, 100)
    hi = (255, 255, 220)
    # Vertical beam
    _rect(s, 7, 1, 2, 14, c)
    # Horizontal beam
    _rect(s, 1, 7, 14, 2, c)
    # Shorter diagonals
    for i in range(4):
        _px(s, 4 + i, 4 + i, c)
        _px(s, 11 - i, 4 + i, c)
        _px(s, 4 + i, 11 - i, c)
        _px(s, 11 - i, 11 - i, c)
    # Center bright
    _rect(s, 7, 7, 2, 2, hi)
    # Tips
    _px(s, 7, 1, hi); _px(s, 8, 1, hi)
    _px(s, 7, 14, hi); _px(s, 8, 14, hi)
    _px(s, 1, 7, hi); _px(s, 1, 8, hi)
    _px(s, 14, 7, hi); _px(s, 14, 8, hi)
    return s


def _draw_arrow_up():
    """Up arrow with outline."""
    s = _s()
    c  = (70, 230, 110)
    dk = (35, 170, 65)
    pts = [(8, 1), (14, 8), (10, 8), (10, 14), (6, 14), (6, 8), (2, 8)]
    pygame.draw.polygon(s, c, pts)
    pygame.draw.polygon(s, dk, pts, 1)
    # Highlight on shaft
    _rect(s, 7, 8, 1, 5, (110, 250, 150))
    # Arrow tip highlight
    _px(s, 7, 3, (130, 255, 170)); _px(s, 8, 3, (130, 255, 170))
    return s


def _draw_medal_gold():
    s = _s()
    # Ribbon
    _rect(s, 6, 0, 2, 3, (255, 60, 60))
    _rect(s, 8, 0, 2, 3, (200, 40, 40))
    # Medal disc
    pygame.draw.circle(s, (255, 215, 0), (8, 7), 5)
    pygame.draw.circle(s, (190, 155, 0), (8, 7), 5, 1)
    # Inner ring
    pygame.draw.circle(s, (220, 180, 0), (8, 7), 3, 1)
    # Highlight
    _px(s, 6, 5, (255, 245, 130)); _px(s, 7, 5, (255, 240, 100))
    # Number
    _px(s, 8, 6, (150, 110, 0)); _px(s, 7, 7, (150, 110, 0))
    _px(s, 9, 7, (150, 110, 0)); _px(s, 8, 8, (150, 110, 0))
    _px(s, 8, 9, (150, 110, 0))
    return s


def _draw_medal_silver():
    s = _s()
    # Ribbon
    _rect(s, 6, 0, 2, 3, (80, 80, 210))
    _rect(s, 8, 0, 2, 3, (60, 60, 170))
    # Medal disc
    pygame.draw.circle(s, (200, 200, 210), (8, 7), 5)
    pygame.draw.circle(s, (140, 140, 155), (8, 7), 5, 1)
    # Inner ring
    pygame.draw.circle(s, (160, 160, 175), (8, 7), 3, 1)
    # Highlight
    _px(s, 6, 5, (230, 230, 240)); _px(s, 7, 5, (220, 220, 230))
    # "2"
    _rect(s, 7, 6, 3, 1, (100, 100, 115))
    _px(s, 9, 7, (100, 100, 115))
    _rect(s, 7, 8, 3, 1, (100, 100, 115))
    _px(s, 7, 9, (100, 100, 115))
    _rect(s, 7, 10, 3, 1, (100, 100, 115))
    return s


def _draw_medal_bronze():
    s = _s()
    # Ribbon
    _rect(s, 6, 0, 2, 3, (60, 140, 60))
    _rect(s, 8, 0, 2, 3, (40, 110, 40))
    # Medal disc
    pygame.draw.circle(s, (210, 140, 55), (8, 7), 5)
    pygame.draw.circle(s, (155, 95, 30), (8, 7), 5, 1)
    # Inner ring
    pygame.draw.circle(s, (170, 110, 40), (8, 7), 3, 1)
    # Highlight
    _px(s, 6, 5, (235, 175, 90)); _px(s, 7, 5, (230, 165, 80))
    # "3"
    _rect(s, 7, 6, 3, 1, (110, 70, 20))
    _px(s, 9, 7, (110, 70, 20))
    _rect(s, 7, 8, 3, 1, (110, 70, 20))
    _px(s, 9, 9, (110, 70, 20))
    _rect(s, 7, 10, 3, 1, (110, 70, 20))
    return s


def _draw_door():
    """Door with exit arrow."""
    s = _s()
    wood = (130, 85, 45)
    dk   = (95, 60, 30)
    ol   = (70, 45, 20)
    # Door frame
    _outline_rect(s, 5, 1, 9, 14, dk, ol)
    # Door panel
    _outline_rect(s, 6, 2, 7, 12, wood, ol)
    # Panel detail
    _outline_rect(s, 7, 3, 5, 4, dk, ol)
    _outline_rect(s, 7, 9, 5, 4, dk, ol)
    # Handle
    _px(s, 12, 8, (220, 200, 100))
    _px(s, 12, 9, (200, 180, 80))
    # Exit arrow (green, left side)
    _rect(s, 0, 7, 4, 2, (70, 220, 100))
    _px(s, 0, 6, (70, 220, 100)); _px(s, 0, 9, (70, 220, 100))
    return s


def _draw_play():
    """Play triangle with outline."""
    s = _s()
    c  = (70, 230, 110)
    dk = (35, 170, 65)
    pts = [(5, 2), (13, 8), (5, 14)]
    pygame.draw.polygon(s, c, pts)
    pygame.draw.polygon(s, dk, pts, 1)
    # Highlight edge
    _px(s, 6, 4, (130, 255, 165)); _px(s, 6, 5, (120, 250, 155))
    _px(s, 7, 5, (110, 245, 145))
    return s


def _draw_continue():
    """Floppy disk / save icon."""
    s = _s()
    body = (75, 135, 220)
    dk   = (45, 95, 175)
    # Main body
    _outline_rect(s, 2, 2, 12, 12, body, dk)
    # Top highlight
    _rect(s, 3, 2, 10, 1, (100, 160, 240))
    # Metal shutter (top)
    _outline_rect(s, 5, 2, 6, 4, (65, 65, 75), (45, 45, 55))
    _rect(s, 9, 3, 1, 2, body)  # shutter window
    # Label area (bottom)
    _outline_rect(s, 4, 8, 8, 5, (240, 240, 245), (190, 190, 200))
    _rect(s, 5, 9, 6, 1, (180, 180, 190))   # line
    _rect(s, 5, 11, 4, 1, (190, 190, 200))   # line
    return s


def _draw_leaderboard_icon():
    """Podium with medals."""
    s = _s()
    ol = (50, 45, 60)
    # 2nd place (left, silver)
    _outline_rect(s, 1, 7, 5, 7, (192, 192, 200), ol)
    _rect(s, 2, 7, 3, 1, (220, 220, 230))  # highlight
    # 1st place (center, gold)
    _outline_rect(s, 6, 3, 4, 11, (255, 215, 30), ol)
    _rect(s, 7, 3, 2, 1, (255, 240, 100))  # highlight
    # 3rd place (right, bronze)
    _outline_rect(s, 10, 9, 5, 5, (210, 140, 55), ol)
    _rect(s, 11, 9, 3, 1, (235, 170, 80))  # highlight
    # Rank numbers
    _px(s, 8, 5, ol); _px(s, 7, 6, ol)  # "1"
    _px(s, 8, 6, ol)
    _px(s, 3, 9, ol); _px(s, 4, 9, ol)  # "2"
    _px(s, 3, 10, ol)
    _px(s, 12, 11, ol); _px(s, 13, 11, ol)  # "3"
    return s


def _draw_quit():
    """X / quit with outline."""
    s = _s()
    # Circle background
    pygame.draw.circle(s, (200, 55, 55), (8, 8), 6)
    pygame.draw.circle(s, (150, 30, 30), (8, 8), 6, 1)
    # X
    for i in range(7):
        _px(s, 4 + i, 4 + i, (255, 220, 220))
        _px(s, 5 + i, 4 + i, (255, 220, 220))
        _px(s, 11 - i, 4 + i, (255, 220, 220))
        _px(s, 10 - i, 4 + i, (255, 220, 220))
    return s


def _draw_prestige():
    """Prestige / rebirth — circular arrows with star center."""
    s = _s()
    c  = (190, 120, 255)
    dk = (140, 70, 210)
    hi = (220, 170, 255)
    # Circular arrows (thicker)
    pygame.draw.arc(s, c, (2, 2, 12, 12), 0.3, 2.8, 2)
    pygame.draw.arc(s, c, (2, 2, 12, 12), 3.5, 5.8, 2)
    # Highlight arcs
    pygame.draw.arc(s, hi, (3, 3, 10, 10), 0.5, 2.0, 1)
    pygame.draw.arc(s, hi, (3, 3, 10, 10), 3.7, 5.0, 1)
    # Arrow heads (triangular)
    _px(s, 11, 2, c); _px(s, 12, 3, c); _px(s, 12, 4, c)
    _px(s, 3, 12, c); _px(s, 4, 11, c); _px(s, 4, 12, c)
    # Central star
    star = (255, 215, 50)
    _px(s, 8, 6, star); _px(s, 7, 7, star)
    _px(s, 8, 7, star); _px(s, 9, 7, star)
    _px(s, 8, 8, star); _px(s, 7, 8, star)
    _px(s, 9, 8, star); _px(s, 8, 9, star)
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

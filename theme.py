"""
theme.py — Shared color palette and font factory for WORKY.
All UI modules should import colors from here for consistency.
"""

import pygame

# ── Background tones ──────────────────────────────────────────
BG_DARK   = (18, 16, 24)       # deepest (menu background)
BG        = (22, 20, 32)       # standard dark bg (shop, ui panels)
BG_PANEL  = (30, 28, 42)       # raised panel surfaces
BG_CARD   = (42, 38, 58)       # card / row background
BG_CARD_H = (55, 48, 72)       # card hover

# ── Text colors ───────────────────────────────────────────────
TEXT_WHITE = (245, 245, 250)
TEXT_GOLD  = (255, 215, 70)
TEXT_GRAY  = (150, 148, 165)
TEXT_DIM   = (120, 120, 135)
TEXT_RED   = (255, 80, 80)
TEXT_GREEN = (80, 230, 120)
TEXT_CYAN  = (80, 220, 255)
TEXT_PINK  = (255, 130, 200)

# ── Accent / brand ────────────────────────────────────────────
ACCENT       = (255, 180, 50)
ACCENT_GLOW  = (255, 200, 80)
BORDER       = (75, 70, 100)
BORDER_LIGHT = (100, 100, 120)

# ── Buttons ───────────────────────────────────────────────────
BTN_PRIMARY   = (200, 120, 40)
BTN_PRIMARY_H = (240, 150, 50)
BTN_SECONDARY = (60, 100, 160)
BTN_SECONDARY_H = (80, 130, 200)
BTN_BUY       = (50, 170, 80)
BTN_BUY_H     = (70, 210, 100)
BTN_DISABLED  = (50, 48, 55)
BTN_DIS_TXT   = (90, 88, 100)

# ── Medal colors ──────────────────────────────────────────────
GOLD   = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

# ── Star (voting) ────────────────────────────────────────────
STAR_ON    = (255, 210, 50)
STAR_OFF   = (60, 58, 75)
STAR_HOVER = (255, 240, 130)

# ── Rarity (matches worker.py RARITIES) ─────────────────────
RARITY_COMMON    = (180, 180, 180)
RARITY_UNCOMMON  = (100, 200, 100)
RARITY_RARE      = (80, 140, 240)
RARITY_EPIC      = (180, 80, 240)
RARITY_LEGENDARY = (255, 200, 50)

# ── Font size hierarchy ──────────────────────────────────────
FONT_NAME = "Consolas"

def make_fonts():
    """Return a dict of pre-built fonts. Call after pygame.font.init()."""
    return {
        "xs":    pygame.font.SysFont(FONT_NAME, 10),
        "sm":    pygame.font.SysFont(FONT_NAME, 13),
        "md":    pygame.font.SysFont(FONT_NAME, 16),
        "lg":    pygame.font.SysFont(FONT_NAME, 20),
        "lgb":   pygame.font.SysFont(FONT_NAME, 20, bold=True),
        "xl":    pygame.font.SysFont(FONT_NAME, 24),
        "xlb":   pygame.font.SysFont(FONT_NAME, 24, bold=True),
        "xxl":   pygame.font.SysFont(FONT_NAME, 28, bold=True),
        "title": pygame.font.SysFont(FONT_NAME, 48, bold=True),
    }

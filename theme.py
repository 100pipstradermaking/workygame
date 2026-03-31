"""
theme.py — Shared color palette and font factory for WORKY.
Neon pixel-art theme based on Figma design:
light warm cream backgrounds with vibrant neon accent colors.
"""

import pygame

# ── Background tones (warm cream palette from Figma) ─────────
BG_DARK   = (250, 248, 245)    # --game-bg: #faf8f5
BG        = (245, 241, 235)    # --game-surface: #f5f1eb
BG_PANEL  = (255, 255, 255)    # --game-surface-light / card bg
BG_CARD   = (255, 255, 255)    # white cards
BG_CARD_H = (248, 245, 240)    # card hover (slightly tinted)

# ── Text colors ───────────────────────────────────────────────
TEXT_WHITE = (45, 52, 54)      # --neutral-dark: #2d3436 (dark on light bg)
TEXT_GOLD  = (255, 215, 70)    # keep gold for coins/highlights
TEXT_GRAY  = (99, 110, 114)    # --neutral-medium: #636e72
TEXT_DIM   = (178, 190, 195)   # --neutral-light/--text-muted: #b2bec3
TEXT_RED   = (255, 118, 117)   # --danger: #ff7675
TEXT_GREEN = (85, 239, 196)    # --success: #55efc4
TEXT_CYAN  = (0, 206, 209)     # neon-cyan accent
TEXT_PINK  = (236, 72, 153)    # neon-magenta / --primary-accent nearby

# ── Neon accent colors (from Figma design) ────────────────────
NEON_CYAN    = (0, 206, 209)
NEON_YELLOW  = (253, 216, 53)
NEON_MAGENTA = (236, 72, 153)
NEON_GREEN   = (34, 197, 94)
NEON_BLUE    = (59, 130, 246)
NEON_ORANGE  = (249, 115, 22)

# ── Accent / brand (from Figma) ──────────────────────────────
ACCENT       = (255, 107, 107)   # --primary-accent: #ff6b6b
ACCENT_GLOW  = (255, 140, 140)
BORDER       = (178, 190, 195)   # --neutral-light: #b2bec3
BORDER_LIGHT = (210, 215, 220)

# ── Buttons ───────────────────────────────────────────────────
BTN_PRIMARY   = (78, 205, 196)   # --secondary-accent: #4ecdc4
BTN_PRIMARY_H = (100, 220, 210)
BTN_SECONDARY = (59, 130, 246)   # neon-blue
BTN_SECONDARY_H = (96, 165, 250)
BTN_BUY       = (34, 197, 94)    # neon-green
BTN_BUY_H     = (74, 222, 128)
BTN_DISABLED  = (229, 231, 235)  # light gray for disabled
BTN_DIS_TXT   = (178, 190, 195)

# ── Medal colors ──────────────────────────────────────────────
GOLD   = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

# ── Star (voting) ────────────────────────────────────────────
STAR_ON    = (253, 216, 53)   # neon-yellow
STAR_OFF   = (210, 215, 220)
STAR_HOVER = (255, 240, 130)

# ── Rarity colors (from Figma: R0 mapping) ──────────────────
RARITY_COMMON    = (156, 163, 175)   # text-gray-400
RARITY_UNCOMMON  = (34, 197, 94)     # neon-green
RARITY_RARE      = (59, 130, 246)    # neon-blue
RARITY_EPIC      = (236, 72, 153)    # neon-magenta
RARITY_LEGENDARY = (253, 216, 53)    # neon-yellow

# ── Font ──────────────────────────────────────────────────────
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

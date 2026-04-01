"""
ui_components.py — Reusable pixel-art UI components for WORKY.
Light cream theme with neon accents and pixel-corner effects,
matching the Figma design specification.
"""

import pygame
import math
from theme import (
    BG, BG_DARK, BG_PANEL, BG_CARD, BG_CARD_H,
    TEXT_WHITE, TEXT_GOLD, TEXT_GRAY, TEXT_DIM, TEXT_RED, TEXT_GREEN,
    TEXT_CYAN, TEXT_PINK,
    ACCENT, ACCENT_GLOW, BORDER, BORDER_LIGHT,
    BTN_PRIMARY, BTN_PRIMARY_H, BTN_SECONDARY, BTN_SECONDARY_H,
    BTN_BUY, BTN_BUY_H, BTN_DISABLED, BTN_DIS_TXT,
    NEON_CYAN, NEON_YELLOW, NEON_MAGENTA, NEON_GREEN, NEON_BLUE, NEON_ORANGE,
)
import icons

# ── Font cache ───────────────────────────────────────────────
_font_cache: dict[tuple, pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("Consolas", size, bold=bold)
    return _font_cache[key]


# ── Pixel-corner helper (Figma pixel-border box-shadow style) ─
def draw_pixel_corners(surf: pygame.Surface, rect: pygame.Rect,
                       color: tuple, size: int = 2):
    """Draw pixel-art corner notches on a rect (Figma pixel-border style)."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    s = size
    # Top-left
    pygame.draw.rect(surf, color, (x, y, s, s))
    # Top-right
    pygame.draw.rect(surf, color, (x + w - s, y, s, s))
    # Bottom-left
    pygame.draw.rect(surf, color, (x, y + h - s, s, s))
    # Bottom-right
    pygame.draw.rect(surf, color, (x + w - s, y + h - s, s, s))


# ── Neon glow helper ─────────────────────────────────────────
def draw_neon_glow(surf: pygame.Surface, rect: pygame.Rect,
                   color: tuple, glow_t: float = 0, intensity: int = 25):
    """Draw a pulsing neon glow around a rect."""
    pulse = int(intensity * (0.6 + 0.4 * math.sin(glow_t * 2.5)))
    for spread in range(3, 0, -1):
        gs = pygame.Surface((rect.w + spread * 4, rect.h + spread * 4), pygame.SRCALPHA)
        gs.fill((*color[:3], max(0, pulse // spread)))
        surf.blit(gs, (rect.x - spread * 2, rect.y - spread * 2))


# ── Drawing primitives ───────────────────────────────────────

def draw_card(surf: pygame.Surface, x: int, y: int, w: int, h: int,
              hover: bool = False, accent_color: tuple = None,
              glow_t: float = 0, special: bool = False) -> pygame.Rect:
    """Draw a styled card — white bg with subtle shadow, pixel-corners."""
    rect = pygame.Rect(x, y, w, h)
    bg = BG_CARD_H if hover else BG_CARD

    # Subtle shadow (light theme)
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 12))
    surf.blit(shadow, (x + 2, y + 2))

    # Card fill
    pygame.draw.rect(surf, bg, rect, border_radius=8)

    if special:
        glow_a = int(15 + 10 * math.sin(glow_t * 2))
        gs = pygame.Surface((w, h), pygame.SRCALPHA)
        gs.fill((*NEON_YELLOW[:3], max(0, glow_a)))
        surf.blit(gs, (x, y))
        pygame.draw.rect(surf, NEON_YELLOW, rect, 2, border_radius=8)
        draw_pixel_corners(surf, rect, NEON_YELLOW, 3)
    elif accent_color:
        # Neon left accent bar
        pygame.draw.rect(surf, accent_color, (x, y + 4, 3, h - 8), border_radius=1)
        # Subtle tint overlay
        tint = pygame.Surface((20, h), pygame.SRCALPHA)
        tint.fill((*accent_color[:3], 12))
        surf.blit(tint, (x, y))
        border_c = accent_color if hover else BORDER_LIGHT
        pygame.draw.rect(surf, border_c, rect, 1, border_radius=8)
        draw_pixel_corners(surf, rect, accent_color, 2)
    else:
        pygame.draw.rect(surf, BORDER_LIGHT, rect, 1, border_radius=8)

    return rect


def draw_button(surf: pygame.Surface, rect: pygame.Rect, label: str,
                enabled: bool = True, color: tuple = None,
                hover_color: tuple = None, font_size: int = 13,
                icon_surf: pygame.Surface = None) -> bool:
    """Draw a styled button (neon style). Returns True if hovered and enabled."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)

    if enabled:
        if color:
            c = hover_color if (hovered and hover_color) else color
        else:
            c = BTN_BUY_H if hovered else BTN_BUY
        txt_c = (255, 255, 255)  # white text on colored buttons
        if hovered:
            # Neon glow on hover
            gs = pygame.Surface((rect.w + 6, rect.h + 6), pygame.SRCALPHA)
            gs.fill((*c[:3], 25))
            surf.blit(gs, (rect.x - 3, rect.y - 3))
    else:
        c = BTN_DISABLED
        txt_c = BTN_DIS_TXT

    pygame.draw.rect(surf, c, rect, border_radius=6)
    draw_pixel_corners(surf, rect, c, 2)

    font = get_font(font_size, bold=True)
    txt = font.render(label, True, txt_c)

    if icon_surf:
        total_w = icon_surf.get_width() + 4 + txt.get_width()
        ix = rect.centerx - total_w // 2
        surf.blit(icon_surf, (ix, rect.centery - icon_surf.get_height() // 2))
        surf.blit(txt, (ix + icon_surf.get_width() + 4,
                        rect.centery - txt.get_height() // 2))
    else:
        surf.blit(txt, txt.get_rect(center=rect.center))
    return hovered and enabled


def draw_progress_bar(surf: pygame.Surface, x: int, y: int, w: int, h: int,
                      progress: float, color: tuple = NEON_GREEN,
                      bg_color: tuple = (230, 230, 235),
                      show_shimmer: bool = False, glow_t: float = 0):
    """Draw a progress bar (progress 0..1) — light theme."""
    pygame.draw.rect(surf, bg_color, (x, y, w, h), border_radius=h // 2)
    fill_w = int(w * max(0, min(1, progress)))
    if fill_w > 0:
        pygame.draw.rect(surf, color, (x, y, fill_w, h), border_radius=h // 2)
        if show_shimmer:
            shimmer_x = int((glow_t * 40) % (w + 20)) - 10
            if 0 < shimmer_x < fill_w:
                sh = pygame.Surface((8, h), pygame.SRCALPHA)
                sh.fill((255, 255, 255, 50))
                surf.blit(sh, (x + shimmer_x, y))


def draw_badge(surf: pygame.Surface, x: int, y: int,
               text: str, color: tuple, font_size: int = 11) -> int:
    """Draw a small neon-colored badge. Returns badge width."""
    font = get_font(font_size, bold=True)
    txt = font.render(text, True, (255, 255, 255))
    pw, ph = txt.get_width() + 10, txt.get_height() + 4
    pygame.draw.rect(surf, color, (x, y, pw, ph), border_radius=4)
    draw_pixel_corners(surf, pygame.Rect(x, y, pw, ph), color, 2)
    surf.blit(txt, (x + 5, y + 2))
    return pw


def draw_separator(surf: pygame.Surface, x: int, y: int, w: int,
                   color: tuple = BORDER_LIGHT):
    """Draw a subtle separator line."""
    pygame.draw.line(surf, color, (x, y), (x + w, y), 1)


def draw_section_header(surf: pygame.Surface, x: int, y: int, w: int,
                        title: str, color: tuple = NEON_CYAN,
                        icon_name: str = None) -> int:
    """Draw an uppercase section header (Figma style). Returns new y."""
    font = get_font(14, bold=True)
    txt = font.render(title.upper(), True, color)
    if icon_name:
        ico = icons.get_scaled(icon_name, 14)
        surf.blit(ico, (x, y + 1))
        surf.blit(txt, (x + 18, y))
    else:
        surf.blit(txt, (x, y))
    # Neon-colored underline
    pygame.draw.line(surf, (*color[:3],), (x, y + txt.get_height() + 3),
                     (x + w, y + txt.get_height() + 3), 1)
    return y + txt.get_height() + 10


def draw_stat_row(surf: pygame.Surface, x: int, y: int,
                  icon_name: str, label: str, value: str,
                  label_color: tuple = TEXT_GRAY,
                  value_color: tuple = TEXT_WHITE) -> int:
    """Draw icon + label + value on one row. Returns new y."""
    ico = icons.get_scaled(icon_name, 14)
    surf.blit(ico, (x, y + 1))
    font = get_font(13)
    ltxt = font.render(label, True, label_color)
    vtxt = font.render(value, True, value_color)
    surf.blit(ltxt, (x + 18, y))
    surf.blit(vtxt, (x + 18 + ltxt.get_width() + 6, y))
    return y + 18


def draw_panel_bg(surf: pygame.Surface, rect: pygame.Rect, glow_t: float = 0):
    """Draw a light panel background with subtle dot pattern and edge shadow."""
    pygame.draw.rect(surf, BG, rect)
    # Left edge inner shadow for depth
    shadow = pygame.Surface((6, rect.height), pygame.SRCALPHA)
    for x in range(6):
        alpha = int(12 * (1 - x / 6))
        pygame.draw.line(shadow, (0, 0, 0, alpha), (x, 0), (x, rect.height))
    surf.blit(shadow, (rect.x, rect.y))
    # Subtle dot grid pattern (light theme equivalent of scanlines)
    for gy in range(0, rect.height, 16):
        for gx in range(0, rect.width, 16):
            pygame.draw.rect(surf, (0, 0, 0, 6),
                             (rect.x + gx, rect.y + gy, 1, 1))


def draw_glow_border(surf: pygame.Surface, rect: pygame.Rect,
                     color: tuple = NEON_CYAN, glow_t: float = 0,
                     thickness: int = 2):
    """Draw a pulsing neon glow border around a rect."""
    alpha = int(40 + 25 * math.sin(glow_t * 2))
    for i in range(thickness + 2):
        gr = pygame.Rect(rect.x - i, rect.y - i,
                         rect.width + i * 2, rect.height + i * 2)
        gs = pygame.Surface((gr.w, gr.h), pygame.SRCALPHA)
        border_a = max(0, alpha - i * 12)
        pygame.draw.rect(gs, (*color[:3], border_a), gs.get_rect(), 1,
                         border_radius=8)
        surf.blit(gs, gr.topleft)


def draw_icon_button(surf: pygame.Surface, rect: pygame.Rect,
                     icon_name: str, label: str, active: bool = False,
                     color: tuple = BG, active_color: tuple = None,
                     label_color: tuple = TEXT_GRAY,
                     active_label_color: tuple = NEON_CYAN,
                     glow_t: float = 0) -> bool:
    """Draw a bottom nav icon button (Figma style). Returns True if hovered."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    if active_color is None:
        active_color = BG_CARD

    if active:
        c = active_color
        # Neon cyan top border (Figma: border-t-2 border-neon-cyan)
        pygame.draw.rect(surf, NEON_CYAN,
                         (rect.x + 4, rect.y, rect.width - 8, 3),
                         border_radius=1)
    elif hovered:
        c = BG_CARD_H
    else:
        c = color

    pygame.draw.rect(surf, c, rect)

    # Icon centered above label
    ico = icons.get_scaled(icon_name, 18)
    ico_x = rect.centerx - 9
    ico_y = rect.y + 8
    surf.blit(ico, (ico_x, ico_y))

    # Label below icon
    font = get_font(10, bold=active)
    tc = active_label_color if active else label_color
    txt = font.render(label, True, tc)
    surf.blit(txt, txt.get_rect(centerx=rect.centerx, top=ico_y + 22))

    return hovered


def draw_coins_display(surf: pygame.Surface, x: int, y: int,
                       coins: float, font_size: int = 20) -> int:
    """Draw coin icon + amount (neon-yellow style). Returns width used."""
    ico = icons.get("coin")
    font = get_font(font_size, bold=True)
    txt = font.render(f"{coins:,.0f}", True, NEON_YELLOW)
    surf.blit(ico, (x, y + 2))
    surf.blit(txt, (x + 20, y))
    return 20 + txt.get_width()


def draw_locked_overlay(surf: pygame.Surface, rect: pygame.Rect,
                        label: str = "COMING SOON", glow_t: float = 0):
    """Draw a 'locked / coming soon' overlay on a card — light theme."""
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((250, 248, 245, 180))
    surf.blit(overlay, rect.topleft)

    font = get_font(16, bold=True)
    pulse = int(20 * math.sin(glow_t * 2))
    color = (max(0, NEON_CYAN[0] - pulse), NEON_CYAN[1],
             min(255, NEON_CYAN[2] + pulse))
    txt = font.render(label, True, color)
    surf.blit(txt, txt.get_rect(center=rect.center))

    # Lock icon
    lock_ico = icons.get_scaled("door", 16)
    surf.blit(lock_ico, (rect.centerx - 8, rect.centery - 28))


def draw_neon_tab(surf: pygame.Surface, rect: pygame.Rect,
                  label: str, active: bool = False,
                  color: tuple = NEON_CYAN, glow_t: float = 0) -> bool:
    """Draw a neon-styled sub-tab button. Returns True if hovered."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)

    if active:
        pygame.draw.rect(surf, color, rect, border_radius=6)
        draw_pixel_corners(surf, rect, color, 2)
        txt_c = (255, 255, 255)
    elif hovered:
        pygame.draw.rect(surf, BG_CARD, rect, border_radius=6)
        pygame.draw.rect(surf, color, rect, 1, border_radius=6)
        txt_c = color
    else:
        pygame.draw.rect(surf, BG_CARD, rect, border_radius=6)
        pygame.draw.rect(surf, BORDER_LIGHT, rect, 1, border_radius=6)
        txt_c = TEXT_GRAY

    font = get_font(11, bold=active)
    txt = font.render(label.upper(), True, txt_c)
    surf.blit(txt, txt.get_rect(center=rect.center))
    return hovered

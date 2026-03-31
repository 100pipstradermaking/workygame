"""
ui_components.py — Reusable pixel-art UI components for WORKY.
Modern idle-game style: soft dark theme, neon highlights, rounded cards.
All drawing primitives used by game_screen.py screens.
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
)
import icons

# ── Font cache ───────────────────────────────────────────────
_font_cache: dict[tuple, pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("Consolas", size, bold=bold)
    return _font_cache[key]


# ── Drawing primitives ───────────────────────────────────────

def draw_card(surf: pygame.Surface, x: int, y: int, w: int, h: int,
              hover: bool = False, accent_color: tuple = None,
              glow_t: float = 0, special: bool = False) -> pygame.Rect:
    """Draw a styled card background. Returns the rect."""
    rect = pygame.Rect(x, y, w, h)
    bg = BG_CARD_H if hover else BG_CARD
    pygame.draw.rect(surf, bg, rect, border_radius=6)

    if special:
        glow_a = int(20 + 10 * math.sin(glow_t * 2))
        gs = pygame.Surface((w, h), pygame.SRCALPHA)
        gs.fill((*ACCENT[:3], max(0, glow_a)))
        surf.blit(gs, (x, y))
        pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=6)
    elif accent_color:
        pygame.draw.rect(surf, accent_color, (x, y + 3, 3, h - 6), border_radius=2)
        ig = pygame.Surface((20, h), pygame.SRCALPHA)
        ig.fill((*accent_color[:3], 15))
        surf.blit(ig, (x, y))
        border_c = accent_color if hover else BORDER
        pygame.draw.rect(surf, border_c, rect, 1, border_radius=6)
    else:
        pygame.draw.rect(surf, BORDER, rect, 1, border_radius=6)
    return rect


def draw_button(surf: pygame.Surface, rect: pygame.Rect, label: str,
                enabled: bool = True, color: tuple = None,
                hover_color: tuple = None, font_size: int = 13,
                icon_surf: pygame.Surface = None) -> bool:
    """Draw a styled button. Returns True if hovered and enabled."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)

    if enabled:
        if color:
            c = hover_color if (hovered and hover_color) else color
        else:
            c = BTN_BUY_H if hovered else BTN_BUY
        txt_c = TEXT_WHITE
        if hovered:
            gs = pygame.Surface((rect.w + 4, rect.h + 4), pygame.SRCALPHA)
            gs.fill((80, 255, 120, 20))
            surf.blit(gs, (rect.x - 2, rect.y - 2))
    else:
        c = BTN_DISABLED
        txt_c = BTN_DIS_TXT

    pygame.draw.rect(surf, c, rect, border_radius=4)
    font = get_font(font_size)
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
                      progress: float, color: tuple = ACCENT,
                      bg_color: tuple = (25, 25, 35),
                      show_shimmer: bool = False, glow_t: float = 0):
    """Draw a progress bar (progress 0..1)."""
    pygame.draw.rect(surf, bg_color, (x, y, w, h), border_radius=h // 2)
    fill_w = int(w * max(0, min(1, progress)))
    if fill_w > 0:
        pygame.draw.rect(surf, color, (x, y, fill_w, h), border_radius=h // 2)
        if show_shimmer:
            shimmer_x = int((glow_t * 40) % (w + 20)) - 10
            if 0 < shimmer_x < fill_w:
                sh = pygame.Surface((8, h), pygame.SRCALPHA)
                sh.fill((255, 255, 255, 30))
                surf.blit(sh, (x + shimmer_x, y))


def draw_badge(surf: pygame.Surface, x: int, y: int,
               text: str, color: tuple, font_size: int = 11) -> int:
    """Draw a small colored badge. Returns badge width."""
    font = get_font(font_size)
    txt = font.render(text, True, TEXT_WHITE)
    pw, ph = txt.get_width() + 8, txt.get_height() + 4
    pygame.draw.rect(surf, color, (x, y, pw, ph), border_radius=3)
    surf.blit(txt, (x + 4, y + 2))
    return pw


def draw_separator(surf: pygame.Surface, x: int, y: int, w: int,
                   color: tuple = TEXT_GRAY):
    """Draw a gradient fade-out separator line."""
    for sx in range(w):
        alpha = int(40 * (1 - abs(sx / w - 0.5) * 2))
        pygame.draw.rect(surf, (*color[:3], max(0, alpha)),
                         (x + sx, y, 1, 1))


def draw_section_header(surf: pygame.Surface, x: int, y: int, w: int,
                        title: str, color: tuple = TEXT_CYAN,
                        icon_name: str = None) -> int:
    """Draw a section header with optional icon. Returns new y below it."""
    font = get_font(14, bold=True)
    txt = font.render(title, True, color)
    if icon_name:
        ico = icons.get_scaled(icon_name, 14)
        surf.blit(ico, (x, y + 1))
        surf.blit(txt, (x + 18, y))
    else:
        surf.blit(txt, (x, y))
    draw_separator(surf, x, y + txt.get_height() + 2, w, color)
    return y + txt.get_height() + 8


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
    """Draw a full panel background with subtle grid pattern."""
    pygame.draw.rect(surf, BG_PANEL, rect)
    # Subtle scanline pattern
    for i in range(0, rect.height, 4):
        alpha = int(4 + 2 * math.sin(i * 0.08 + glow_t * 0.5))
        ls = pygame.Surface((rect.width, 1), pygame.SRCALPHA)
        ls.fill((100, 90, 140, max(0, min(255, alpha))))
        surf.blit(ls, (rect.x, rect.y + i))


def draw_glow_border(surf: pygame.Surface, rect: pygame.Rect,
                     color: tuple = ACCENT, glow_t: float = 0,
                     thickness: int = 2):
    """Draw a pulsing glow border around a rect."""
    alpha = int(40 + 20 * math.sin(glow_t * 2))
    for i in range(thickness):
        gs = pygame.Surface((rect.width, 1), pygame.SRCALPHA)
        gs.fill((*color[:3], max(0, alpha - i * 10)))
        surf.blit(gs, (rect.x, rect.y + i))


def draw_icon_button(surf: pygame.Surface, rect: pygame.Rect,
                     icon_name: str, label: str, active: bool = False,
                     color: tuple = BG_CARD, active_color: tuple = None,
                     label_color: tuple = TEXT_GRAY,
                     active_label_color: tuple = TEXT_WHITE,
                     glow_t: float = 0) -> bool:
    """Draw an icon button (for nav). Returns True if hovered."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    if active_color is None:
        active_color = BTN_PRIMARY

    if active:
        c = active_color
        # Top indicator line
        pygame.draw.rect(surf, ACCENT, (rect.x + 8, rect.y, rect.width - 16, 3),
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
    font = get_font(10)
    tc = active_label_color if active else label_color
    txt = font.render(label, True, tc)
    surf.blit(txt, txt.get_rect(centerx=rect.centerx, top=ico_y + 22))

    return hovered


def draw_coins_display(surf: pygame.Surface, x: int, y: int,
                       coins: float, font_size: int = 20) -> int:
    """Draw coin icon + amount. Returns width used."""
    ico = icons.get("coin")
    font = get_font(font_size, bold=True)
    txt = font.render(f"{coins:,.0f}", True, TEXT_GOLD)
    surf.blit(ico, (x, y + 2))
    surf.blit(txt, (x + 20, y))
    return 20 + txt.get_width()


def draw_locked_overlay(surf: pygame.Surface, rect: pygame.Rect,
                        label: str = "COMING SOON", glow_t: float = 0):
    """Draw a 'locked / coming soon' overlay on a card."""
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((18, 16, 24, 160))
    surf.blit(overlay, rect.topleft)

    font = get_font(16, bold=True)
    pulse = int(20 * math.sin(glow_t * 2))
    color = (ACCENT[0], min(255, ACCENT[1] + pulse), ACCENT[2])
    txt = font.render(label, True, color)
    surf.blit(txt, txt.get_rect(center=rect.center))

    # Lock icon
    lock_ico = icons.get_scaled("door", 16)
    surf.blit(lock_ico, (rect.centerx - 8, rect.centery - 28))

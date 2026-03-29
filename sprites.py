"""
sprites.py — WORKY pixel character sprites.
Detailed pixel art worker archetypes inspired by the WORKY brand:
"caffeine-fueled warriors, spreadsheet soldiers, wrench-wielding wizards"

Each archetype has unique outfit, accessory, and work animation.
Sprites are drawn procedurally with Pygame — no image files needed.
"""

import pygame
import math
import random

# ── Pixel size & scale ────────────────────────────────────────
PX = 2          # base pixel size (each "pixel" = 2x2 screen pixels)
SPRITE_W = 12   # character width in art-pixels
SPRITE_H = 18   # character height in art-pixels

# ── Skin tones (randomly assigned) ───────────────────────────
SKIN_TONES = [
    (240, 200, 160),  # light
    (220, 180, 140),  # medium light
    (190, 140, 100),  # medium
    (160, 110, 70),   # medium dark
    (120, 80, 50),    # dark
]

# ── WORKY Archetypes ─────────────────────────────────────────
# Each archetype defines: name, outfit colors, hat/accessory type,
# held item, and unique animation details.

ARCHETYPES = {
    "burger_chef": {
        "name": "Burger Chef",
        "shirt": (255, 255, 255),
        "pants": (40, 40, 50),
        "hat_type": "chef_hat",
        "hat_color": (255, 255, 255),
        "apron": (220, 60, 60),
        "accessory": "spatula",
    },
    "office_grinder": {
        "name": "Office Grinder",
        "shirt": (60, 100, 180),
        "pants": (50, 50, 60),
        "hat_type": "none",
        "hat_color": None,
        "apron": None,
        "accessory": "coffee_cup",
    },
    "construction": {
        "name": "Hard Hat Hero",
        "shirt": (255, 160, 30),
        "pants": (70, 70, 50),
        "hat_type": "hardhat",
        "hat_color": (255, 220, 40),
        "apron": None,
        "accessory": "wrench",
    },
    "barista": {
        "name": "Caffeine Warrior",
        "shirt": (60, 50, 40),
        "pants": (50, 45, 40),
        "hat_type": "beanie",
        "hat_color": (80, 60, 50),
        "apron": (90, 140, 60),
        "accessory": "coffee_cup",
    },
    "delivery": {
        "name": "Speed Runner",
        "shirt": (200, 50, 50),
        "pants": (40, 40, 50),
        "hat_type": "cap",
        "hat_color": (200, 50, 50),
        "apron": None,
        "accessory": "box",
    },
    "janitor": {
        "name": "Clean Machine",
        "shirt": (100, 140, 180),
        "pants": (100, 140, 180),
        "hat_type": "none",
        "hat_color": None,
        "apron": None,
        "accessory": "mop",
    },
}

# Map rarity to archetype pool weighting
RARITY_ARCHETYPES = {
    "common":    ["burger_chef", "janitor"],
    "uncommon":  ["burger_chef", "delivery", "barista"],
    "rare":      ["office_grinder", "barista", "construction"],
    "epic":      ["construction", "office_grinder"],
    "legendary": ["office_grinder", "construction", "barista"],
}


def pick_archetype(rarity: str) -> str:
    pool = RARITY_ARCHETYPES.get(rarity, ["burger_chef"])
    return random.choice(pool)


def pick_skin_tone() -> tuple:
    return random.choice(SKIN_TONES)


# ── Sprite drawing ────────────────────────────────────────────

def _px(surf, color, x, y, w=1, h=1):
    """Draw pixel(s) at art-pixel coords scaled by PX."""
    pygame.draw.rect(surf, color, (x * PX, y * PX, w * PX, h * PX))


class WorkySpriteRenderer:
    """Draws a detailed WORKY character with blinking eyes, emotions,
    and smoother walk/work animations."""

    def __init__(self, archetype_id: str, rarity_color: tuple, skin: tuple = None):
        self.arch = ARCHETYPES[archetype_id]
        self.archetype_id = archetype_id
        self.rarity_color = rarity_color
        self.skin = skin or pick_skin_tone()
        self._cache = {}
        # Blink state
        self._blink_timer = random.uniform(2.0, 5.0)
        self._is_blinking = False
        self._blink_dur = 0.0

    def update_blink(self, dt: float):
        """Call once per frame to manage blink timing."""
        if self._is_blinking:
            self._blink_dur -= dt
            if self._blink_dur <= 0:
                self._is_blinking = False
                self._blink_timer = random.uniform(2.0, 6.0)
        else:
            self._blink_timer -= dt
            if self._blink_timer <= 0:
                self._is_blinking = True
                self._blink_dur = 0.12  # blink closed duration

    def draw(self, surf: pygame.Surface, cx: int, cy: int,
             direction: str = "down", anim_frame: int = 0,
             state: str = "idle", rarity: str = "common"):
        """Draw the WORKY sprite centered at (cx, cy)."""
        x0 = cx - (SPRITE_W * PX) // 2
        y0 = cy - (SPRITE_H * PX) // 2

        sw = SPRITE_W * PX + 4
        sh = (SPRITE_H + 6) * PX
        sprite_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

        ox = 2
        oy = 4 * PX

        # Smooth walking: use sin-based leg offset for smoother gait
        walk_offset = 0
        if state == "walking":
            walk_offset = 1 if anim_frame % 2 == 0 else -1

        # ── Shadow (slightly larger) ──
        pygame.draw.ellipse(sprite_surf, (0, 0, 0, 70),
                            (ox + 1 * PX, oy + 16 * PX, 10 * PX, 4 * PX))

        # ── Feet / Shoes ──
        shoe_color = (50, 40, 35)
        _px(sprite_surf, shoe_color, ox // PX + 3, oy // PX + 15 + walk_offset, 2, 2)
        _px(sprite_surf, shoe_color, ox // PX + 7, oy // PX + 15 - walk_offset, 2, 2)

        # ── Pants ──
        pants = self.arch["pants"]
        _px(sprite_surf, pants, ox // PX + 3, oy // PX + 12, 3, 3)
        _px(sprite_surf, pants, ox // PX + 6, oy // PX + 12, 3, 3)

        # ── Shirt / Body ──
        shirt = self.arch["shirt"]
        _px(sprite_surf, shirt, ox // PX + 3, oy // PX + 8, 6, 4)

        # Apron overlay
        if self.arch["apron"]:
            apron = self.arch["apron"]
            _px(sprite_surf, apron, ox // PX + 4, oy // PX + 9, 4, 3)

        # ── Arms ──
        arm_color = self.skin
        arm_anim = 0
        if state == "working":
            arm_anim = 1 if anim_frame % 2 == 0 else -1

        _px(sprite_surf, arm_color, ox // PX + 2, oy // PX + 9 + arm_anim, 1, 3)
        _px(sprite_surf, arm_color, ox // PX + 9, oy // PX + 9 - arm_anim, 1, 3)
        # Hands (tiny fists)
        hand_c = (max(0, self.skin[0] - 15), max(0, self.skin[1] - 15),
                  max(0, self.skin[2] - 10))
        _px(sprite_surf, hand_c, ox // PX + 2, oy // PX + 11 + arm_anim, 1, 1)
        _px(sprite_surf, hand_c, ox // PX + 9, oy // PX + 11 - arm_anim, 1, 1)

        # ── Head ──
        _px(sprite_surf, self.skin, ox // PX + 3, oy // PX + 2, 6, 6)

        # ── Eyes (with blinking) ──
        eye_c = (255, 255, 255) if self.skin[0] < 140 else (20, 20, 30)  # better contrast
        pupil_c = (20, 20, 30)
        blinking = self._is_blinking

        if direction == "down":
            if blinking:
                # Closed eyes — horizontal line
                _px(sprite_surf, pupil_c, ox // PX + 4, oy // PX + 5, 2, 1)
                _px(sprite_surf, pupil_c, ox // PX + 7, oy // PX + 5, 2, 1)
            else:
                # Open eyes with white highlight
                _px(sprite_surf, eye_c, ox // PX + 4, oy // PX + 4, 2, 2)
                _px(sprite_surf, eye_c, ox // PX + 7, oy // PX + 4, 2, 2)
                _px(sprite_surf, pupil_c, ox // PX + 5, oy // PX + 5, 1, 1)
                _px(sprite_surf, pupil_c, ox // PX + 8, oy // PX + 5, 1, 1)
            # Mouth — changes with state
            if state == "working":
                # Happy smile (wider)
                _px(sprite_surf, (200, 110, 100), ox // PX + 5, oy // PX + 6, 2, 1)
                _px(sprite_surf, (200, 110, 100), ox // PX + 4, oy // PX + 6, 1, 1)
            elif state == "idle":
                # Neutral
                _px(sprite_surf, (180, 100, 90), ox // PX + 5, oy // PX + 6, 2, 1)
            else:
                _px(sprite_surf, (180, 100, 90), ox // PX + 5, oy // PX + 6, 2, 1)
        elif direction == "up":
            hair_c = (60, 40, 30)
            _px(sprite_surf, hair_c, ox // PX + 3, oy // PX + 2, 6, 3)
        elif direction == "left":
            if not blinking:
                _px(sprite_surf, eye_c, ox // PX + 3, oy // PX + 4, 2, 2)
                _px(sprite_surf, pupil_c, ox // PX + 3, oy // PX + 5, 1, 1)
            else:
                _px(sprite_surf, pupil_c, ox // PX + 3, oy // PX + 5, 2, 1)
            _px(sprite_surf, (180, 100, 90), ox // PX + 4, oy // PX + 6, 1, 1)
        elif direction == "right":
            if not blinking:
                _px(sprite_surf, eye_c, ox // PX + 7, oy // PX + 4, 2, 2)
                _px(sprite_surf, pupil_c, ox // PX + 8, oy // PX + 5, 1, 1)
            else:
                _px(sprite_surf, pupil_c, ox // PX + 7, oy // PX + 5, 2, 1)
            _px(sprite_surf, (180, 100, 90), ox // PX + 7, oy // PX + 6, 1, 1)

        # ── Hair ──
        hair_c = (60, 40, 30)
        _px(sprite_surf, hair_c, ox // PX + 3, oy // PX + 2, 6, 1)
        if direction != "up":
            _px(sprite_surf, hair_c, ox // PX + 3, oy // PX + 3, 1, 1)
            _px(sprite_surf, hair_c, ox // PX + 8, oy // PX + 3, 1, 1)

        # ── Hat / Headgear ──
        self._draw_hat(sprite_surf, ox // PX, oy // PX)

        # ── Held item (right hand) ──
        if state == "working":
            self._draw_accessory(sprite_surf, ox // PX, oy // PX, anim_frame)

        # ── Rarity glow outline (pulsing) ──
        if rarity in ("epic", "legendary"):
            glow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            alpha = int(60 + 50 * math.sin(anim_frame * 0.3))
            for gx in range(-1, 2):
                for gy in range(-1, 2):
                    if gx == 0 and gy == 0:
                        continue
                    glow_surf.blit(sprite_surf, (gx, gy))
            tint = pygame.Surface((sw, sh), pygame.SRCALPHA)
            tint.fill((*self.rarity_color, max(0, alpha)))
            glow_surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(glow_surf, (x0 - 2, y0 - 4 * PX))

        # Blit sprite
        surf.blit(sprite_surf, (x0 - 2, y0 - 4 * PX))

        # ── Rarity indicator ──
        if rarity == "legendary":
            star_y = y0 - 6 * PX
            self._draw_star(surf, cx, star_y, (255, 220, 50), anim_frame)
        elif rarity == "epic":
            star_y = y0 - 5 * PX
            self._draw_diamond(surf, cx, star_y, (180, 80, 240), anim_frame)

    def _draw_hat(self, sprite_surf, ox, oy):
        hat = self.arch["hat_type"]
        hc = self.arch["hat_color"]

        if hat == "chef_hat":
            # Tall white chef hat
            _px(sprite_surf, hc, ox + 4, oy - 2, 4, 4)
            _px(sprite_surf, hc, ox + 3, oy + 1, 6, 1)
            # Poof on top
            _px(sprite_surf, (245, 245, 250), ox + 5, oy - 3, 2, 1)

        elif hat == "hardhat":
            # Yellow construction helmet
            _px(sprite_surf, hc, ox + 2, oy + 1, 8, 2)
            _px(sprite_surf, hc, ox + 3, oy, 6, 1)
            # Brim
            _px(sprite_surf, (200, 180, 30), ox + 2, oy + 2, 8, 1)

        elif hat == "beanie":
            # Knit beanie
            _px(sprite_surf, hc, ox + 3, oy, 6, 2)
            _px(sprite_surf, hc, ox + 4, oy - 1, 4, 1)
            # Fold line
            _px(sprite_surf, (hc[0] + 20, hc[1] + 20, hc[2] + 20),
                ox + 3, oy + 1, 6, 1)

        elif hat == "cap":
            # Baseball cap with brim
            _px(sprite_surf, hc, ox + 3, oy + 1, 6, 1)
            _px(sprite_surf, hc, ox + 4, oy, 4, 1)
            # Brim (forward)
            _px(sprite_surf, (hc[0] - 30, hc[1] - 30, max(0, hc[2] - 30)),
                ox + 2, oy + 2, 4, 1)

    def _draw_accessory(self, sprite_surf, ox, oy, frame):
        acc = self.arch["accessory"]
        # Position near right hand
        ax = ox + 10
        ay = oy + 9 + (1 if frame % 2 == 0 else 0)

        if acc == "spatula":
            # Metal spatula
            _px(sprite_surf, (180, 180, 190), ax, ay - 2, 1, 4)
            _px(sprite_surf, (200, 200, 210), ax, ay - 3, 2, 1)
            _px(sprite_surf, (100, 70, 40), ax, ay + 1, 1, 2)  # handle

        elif acc == "coffee_cup":
            # Paper coffee cup
            _px(sprite_surf, (240, 230, 210), ax, ay - 1, 2, 3)
            _px(sprite_surf, (160, 100, 60), ax, ay, 2, 1)  # sleeve
            # Steam
            if frame % 3 == 0:
                _px(sprite_surf, (200, 200, 200), ax, ay - 3, 1, 1)
                _px(sprite_surf, (200, 200, 200), ax + 1, ay - 2, 1, 1)

        elif acc == "wrench":
            # Silver wrench
            _px(sprite_surf, (170, 170, 180), ax, ay - 1, 1, 3)
            _px(sprite_surf, (170, 170, 180), ax - 1, ay - 1, 3, 1)
            _px(sprite_surf, (120, 80, 40), ax, ay + 1, 1, 2)

        elif acc == "box":
            # Delivery box
            _px(sprite_surf, (190, 160, 110), ax - 1, ay - 1, 3, 3)
            _px(sprite_surf, (160, 130, 90), ax, ay, 1, 1)

        elif acc == "mop":
            # Mop
            _px(sprite_surf, (160, 140, 100), ax, ay - 3, 1, 5)
            _px(sprite_surf, (200, 200, 210), ax - 1, ay + 1, 3, 1)
            _px(sprite_surf, (180, 180, 190), ax - 1, ay + 2, 3, 1)

    def _draw_star(self, surf, cx, cy, color, frame):
        """Tiny animated star above legendary workers."""
        bob = int(math.sin(frame * 0.3) * 2)
        ps = PX
        pygame.draw.rect(surf, color, (cx - ps, cy + bob, ps * 2, ps))
        pygame.draw.rect(surf, color, (cx - ps // 2, cy + bob - ps, ps, ps * 3))

    def _draw_diamond(self, surf, cx, cy, color, frame):
        """Small diamond above epic workers."""
        bob = int(math.sin(frame * 0.25) * 2)
        ps = PX
        pygame.draw.rect(surf, color, (cx - ps // 2, cy + bob - ps, ps, ps))
        pygame.draw.rect(surf, color, (cx - ps, cy + bob, ps * 2, ps))
        pygame.draw.rect(surf, color, (cx - ps // 2, cy + bob + ps, ps, ps))


# ── Emoji/Status bubbles ─────────────────────────────────────

def draw_speech_bubble(surf: pygame.Surface, cx: int, cy: int,
                       text: str, color: tuple, font: pygame.font.Font):
    """Draw a tiny speech bubble above a worker."""
    txt_surf = font.render(text, True, color)
    tw, th = txt_surf.get_size()
    bx = cx - tw // 2 - 3
    by = cy - th - 4

    # Bubble background
    bg_rect = pygame.Rect(bx, by, tw + 6, th + 4)
    pygame.draw.rect(surf, (30, 30, 40, 200), bg_rect, border_radius=3)
    pygame.draw.rect(surf, color, bg_rect, 1, border_radius=3)

    # Tail
    pygame.draw.polygon(surf, (30, 30, 40),
                        [(cx - 2, by + th + 4), (cx + 2, by + th + 4),
                         (cx, by + th + 8)])

    surf.blit(txt_surf, (bx + 3, by + 2))

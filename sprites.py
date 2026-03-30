"""
sprites.py — WORKY pixel character sprites.
Detailed pixel art worker archetypes inspired by the WORKY brand:
"caffeine-fueled warriors, spreadsheet soldiers, wrench-wielding wizards"

Each archetype has unique outfit, accessory, and work animation.
Sprites are drawn procedurally with Pygame — no image files needed.
Enhanced version with shading, outlines, hair variety, clothing detail.
"""

import pygame
import math
import random

# ── Pixel size & scale ────────────────────────────────────────
PX = 2          # base pixel size (each "pixel" = 2x2 screen pixels)
SPRITE_W = 16   # character width in art-pixels (was 12)
SPRITE_H = 24   # character height in art-pixels (was 18)

# ── Skin tones (randomly assigned) ───────────────────────────
SKIN_TONES = [
    (240, 200, 160),  # light
    (220, 180, 140),  # medium light
    (190, 140, 100),  # medium
    (160, 110, 70),   # medium dark
    (120, 80, 50),    # dark
]

# Hair colors per archetype (each archetype gets a pool)
HAIR_COLORS = [
    (40, 30, 20),     # black
    (80, 50, 30),     # dark brown
    (140, 90, 50),    # light brown
    (200, 160, 80),   # blonde
    (180, 60, 40),    # auburn
    (60, 60, 70),     # dark gray
]

# Hair style IDs: 0=short, 1=spiky, 2=side part, 3=buzz, 4=curly
HAIR_STYLES = [0, 1, 2, 3, 4]

# ── WORKY Archetypes ─────────────────────────────────────────
ARCHETYPES = {
    "burger_chef": {
        "name": "Burger Chef",
        "shirt": (255, 255, 255),
        "shirt_shade": (230, 230, 235),
        "pants": (40, 40, 50),
        "pants_shade": (30, 30, 40),
        "hat_type": "chef_hat",
        "hat_color": (255, 255, 255),
        "apron": (220, 60, 60),
        "apron_shade": (180, 45, 45),
        "accessory": "spatula",
        "collar": (240, 240, 245),
        "shoe_color": (50, 40, 35),
        "detail_type": "buttons",
    },
    "office_grinder": {
        "name": "Office Grinder",
        "shirt": (60, 100, 180),
        "shirt_shade": (45, 80, 150),
        "pants": (50, 50, 60),
        "pants_shade": (38, 38, 48),
        "hat_type": "none",
        "hat_color": None,
        "apron": None,
        "apron_shade": None,
        "accessory": "coffee_cup",
        "collar": (80, 120, 200),
        "shoe_color": (35, 30, 30),
        "detail_type": "tie",
    },
    "construction": {
        "name": "Hard Hat Hero",
        "shirt": (255, 160, 30),
        "shirt_shade": (220, 135, 20),
        "pants": (70, 70, 50),
        "pants_shade": (55, 55, 38),
        "hat_type": "hardhat",
        "hat_color": (255, 220, 40),
        "apron": None,
        "apron_shade": None,
        "accessory": "wrench",
        "collar": (240, 150, 25),
        "shoe_color": (80, 60, 40),
        "detail_type": "vest_stripes",
    },
    "barista": {
        "name": "Caffeine Warrior",
        "shirt": (60, 50, 40),
        "shirt_shade": (45, 38, 30),
        "pants": (50, 45, 40),
        "pants_shade": (38, 33, 28),
        "hat_type": "beanie",
        "hat_color": (80, 60, 50),
        "apron": (90, 140, 60),
        "apron_shade": (70, 115, 45),
        "accessory": "coffee_cup",
        "collar": (70, 60, 50),
        "shoe_color": (45, 38, 30),
        "detail_type": "pocket",
    },
    "delivery": {
        "name": "Speed Runner",
        "shirt": (200, 50, 50),
        "shirt_shade": (170, 38, 38),
        "pants": (40, 40, 50),
        "pants_shade": (30, 30, 40),
        "hat_type": "cap",
        "hat_color": (200, 50, 50),
        "apron": None,
        "apron_shade": None,
        "accessory": "box",
        "collar": (220, 60, 60),
        "shoe_color": (60, 50, 40),
        "detail_type": "logo",
    },
    "janitor": {
        "name": "Clean Machine",
        "shirt": (100, 140, 180),
        "shirt_shade": (80, 118, 155),
        "pants": (100, 140, 180),
        "pants_shade": (80, 118, 155),
        "hat_type": "none",
        "hat_color": None,
        "apron": None,
        "apron_shade": None,
        "accessory": "mop",
        "collar": (115, 155, 195),
        "shoe_color": (50, 45, 40),
        "detail_type": "name_tag",
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


# ── Helpers ───────────────────────────────────────────────────

def _shade(color, amount=-25):
    """Darken or lighten a color."""
    return tuple(max(0, min(255, c + amount)) for c in color)


def _outline_color(color):
    """Get a dark outline for a given color."""
    return _shade(color, -50)


def _px(surf, color, x, y, w=1, h=1):
    """Draw pixel(s) at art-pixel coords scaled by PX."""
    pygame.draw.rect(surf, color, (x * PX, y * PX, w * PX, h * PX))


def _opx(surf, color, x, y, w=1, h=1):
    """Draw pixel with 1px outline (for important details)."""
    oc = _outline_color(color)
    pygame.draw.rect(surf, oc, (x * PX - 1, y * PX - 1, w * PX + 2, h * PX + 2))
    pygame.draw.rect(surf, color, (x * PX, y * PX, w * PX, h * PX))


# ── Sprite drawing ────────────────────────────────────────────

class WorkySpriteRenderer:
    """Draws a detailed WORKY character with blinking eyes, emotions,
    shading, outlines, varied hair, and smoother walk/work animations."""

    def __init__(self, archetype_id: str, rarity_color: tuple, skin: tuple = None):
        self.arch = ARCHETYPES[archetype_id]
        self.archetype_id = archetype_id
        self.rarity_color = rarity_color
        self.skin = skin or pick_skin_tone()
        self.skin_shade = _shade(self.skin, -20)
        self.hair_color = random.choice(HAIR_COLORS)
        self.hair_style = random.choice(HAIR_STYLES)
        self._cache = {}
        # Blink state
        self._blink_timer = random.uniform(2.0, 5.0)
        self._is_blinking = False
        self._blink_dur = 0.0
        # Idle bob
        self._idle_bob = random.uniform(0, math.pi * 2)

    def update_blink(self, dt: float):
        """Call once per frame to manage blink timing."""
        self._idle_bob += dt * 1.5
        if self._is_blinking:
            self._blink_dur -= dt
            if self._blink_dur <= 0:
                self._is_blinking = False
                self._blink_timer = random.uniform(2.0, 6.0)
        else:
            self._blink_timer -= dt
            if self._blink_timer <= 0:
                self._is_blinking = True
                self._blink_dur = 0.12

    def draw(self, surf: pygame.Surface, cx: int, cy: int,
             direction: str = "down", anim_frame: int = 0,
             state: str = "idle", rarity: str = "common"):
        """Draw the WORKY sprite centered at (cx, cy)."""
        x0 = cx - (SPRITE_W * PX) // 2
        y0 = cy - (SPRITE_H * PX) // 2

        sw = SPRITE_W * PX + 8
        sh = (SPRITE_H + 8) * PX
        sprite_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

        ox = 4
        oy = 6 * PX
        bx = ox // PX  # base x in art-pixels
        by = oy // PX  # base y in art-pixels

        # Walk animation with smoother sine
        walk_phase = math.sin(anim_frame * 0.5) if state == "walking" else 0
        walk_offset = int(walk_phase * 1.5)
        body_bob = int(abs(walk_phase) * 0.5) if state == "walking" else 0

        # Idle breathing bob
        idle_bob = int(math.sin(self._idle_bob) * 0.5) if state == "idle" else 0

        # Work arm animation
        arm_anim = 0
        if state == "working":
            arm_anim = 1 if anim_frame % 2 == 0 else -1

        a = self.arch
        skin = self.skin
        skin_s = self.skin_shade

        # ── Shadow ──
        shadow_w = 12 if state == "walking" else 10
        pygame.draw.ellipse(sprite_surf, (0, 0, 0, 50),
                            (bx * PX + 1 * PX, (by + 21) * PX, shadow_w * PX, 4 * PX))

        # ── Feet / Shoes ──
        shoe = a.get("shoe_color", (50, 40, 35))
        shoe_s = _shade(shoe, -15)
        # Left foot
        lf_y = by + 20 + walk_offset
        _px(sprite_surf, shoe, bx + 3, lf_y, 3, 2)
        _px(sprite_surf, shoe_s, bx + 3, lf_y + 1, 3, 1)  # sole shade
        # Right foot
        rf_y = by + 20 - walk_offset
        _px(sprite_surf, shoe, bx + 9, rf_y, 3, 2)
        _px(sprite_surf, shoe_s, bx + 9, rf_y + 1, 3, 1)

        # ── Legs / Pants ──
        pants = a["pants"]
        pants_s = a.get("pants_shade", _shade(pants))
        _px(sprite_surf, pants, bx + 4, by + 16 - body_bob, 3, 4 + walk_offset)
        _px(sprite_surf, pants, bx + 9, by + 16 - body_bob, 3, 4 - walk_offset)
        # Inner shade on legs
        _px(sprite_surf, pants_s, bx + 6, by + 16 - body_bob, 1, 4)
        _px(sprite_surf, pants_s, bx + 8, by + 16 - body_bob, 1, 4)
        # Belt
        belt_c = (60, 50, 40)
        _px(sprite_surf, belt_c, bx + 4, by + 15 - body_bob, 8, 1)
        # Belt buckle
        _px(sprite_surf, (200, 180, 80), bx + 7, by + 15 - body_bob, 2, 1)

        # ── Shirt / Torso ──
        shirt = a["shirt"]
        shirt_s = a.get("shirt_shade", _shade(shirt))
        torso_y = by + 9 - body_bob + idle_bob
        _px(sprite_surf, shirt, bx + 3, torso_y, 10, 6)
        # Shirt shading (right side darker)
        _px(sprite_surf, shirt_s, bx + 10, torso_y, 3, 6)
        _px(sprite_surf, shirt_s, bx + 3, torso_y + 5, 10, 1)
        # Collar
        collar = a.get("collar", _shade(shirt, 20))
        _px(sprite_surf, collar, bx + 5, torso_y, 6, 1)

        # Clothing detail
        detail = a.get("detail_type", "")
        if detail == "buttons":
            _px(sprite_surf, (200, 200, 210), bx + 8, torso_y + 2, 1, 1)
            _px(sprite_surf, (200, 200, 210), bx + 8, torso_y + 4, 1, 1)
        elif detail == "tie":
            _px(sprite_surf, (180, 50, 50), bx + 7, torso_y + 1, 2, 1)
            _px(sprite_surf, (160, 40, 40), bx + 7, torso_y + 2, 2, 3)
            _px(sprite_surf, (140, 35, 35), bx + 8, torso_y + 4, 1, 1)
        elif detail == "vest_stripes":
            _px(sprite_surf, (255, 255, 80), bx + 5, torso_y + 1, 6, 1)
            _px(sprite_surf, (255, 255, 80), bx + 5, torso_y + 4, 6, 1)
        elif detail == "logo":
            _px(sprite_surf, (255, 255, 255), bx + 5, torso_y + 2, 3, 2)
            _px(sprite_surf, shirt, bx + 6, torso_y + 2, 1, 1)
        elif detail == "pocket":
            _px(sprite_surf, shirt_s, bx + 5, torso_y + 2, 3, 2)
            _px(sprite_surf, _shade(shirt_s, 10), bx + 5, torso_y + 2, 3, 1)
        elif detail == "name_tag":
            _px(sprite_surf, (240, 240, 240), bx + 5, torso_y + 2, 3, 2)
            _px(sprite_surf, (60, 60, 80), bx + 5, torso_y + 3, 2, 1)

        # Apron overlay
        if a["apron"]:
            apron = a["apron"]
            apron_s = a.get("apron_shade", _shade(apron))
            _px(sprite_surf, apron, bx + 4, torso_y + 1, 8, 5)
            _px(sprite_surf, apron_s, bx + 4, torso_y + 5, 8, 1)
            # Apron strings
            _px(sprite_surf, _shade(apron, 15), bx + 4, torso_y + 2, 1, 1)
            _px(sprite_surf, _shade(apron, 15), bx + 11, torso_y + 2, 1, 1)

        # ── Arms ──
        arm_y = torso_y + 1 + arm_anim
        # Left arm (upper + forearm + hand)
        _px(sprite_surf, shirt, bx + 2, arm_y, 1, 3)
        _px(sprite_surf, shirt_s, bx + 2, arm_y + 2, 1, 1)
        _px(sprite_surf, skin, bx + 2, arm_y + 3, 1, 2)
        _px(sprite_surf, skin_s, bx + 2, arm_y + 4, 1, 1)  # hand shade

        # Right arm
        r_arm_y = torso_y + 1 - arm_anim
        _px(sprite_surf, shirt, bx + 13, r_arm_y, 1, 3)
        _px(sprite_surf, shirt_s, bx + 13, r_arm_y + 2, 1, 1)
        _px(sprite_surf, skin, bx + 13, r_arm_y + 3, 1, 2)
        _px(sprite_surf, skin_s, bx + 13, r_arm_y + 4, 1, 1)

        # ── Head ──
        head_y = by + 2 + idle_bob - body_bob
        # Head outline
        _px(sprite_surf, _outline_color(skin), bx + 4, head_y - 1, 8, 8)
        # Head fill
        _px(sprite_surf, skin, bx + 4, head_y, 8, 7)
        # Face shading
        _px(sprite_surf, skin_s, bx + 11, head_y, 1, 7)
        _px(sprite_surf, skin_s, bx + 4, head_y + 6, 8, 1)
        # Ears
        _px(sprite_surf, skin, bx + 3, head_y + 2, 1, 2)
        _px(sprite_surf, skin, bx + 12, head_y + 2, 1, 2)
        _px(sprite_surf, skin_s, bx + 3, head_y + 3, 1, 1)
        _px(sprite_surf, skin_s, bx + 12, head_y + 3, 1, 1)

        # ── Eyes (with blinking, direction) ──
        blinking = self._is_blinking
        eye_white = (245, 245, 255)
        pupil_c = (25, 25, 35)
        highlight_c = (255, 255, 255)

        if direction == "down":
            if blinking:
                _px(sprite_surf, pupil_c, bx + 5, head_y + 4, 2, 1)
                _px(sprite_surf, pupil_c, bx + 9, head_y + 4, 2, 1)
            else:
                # Eye whites
                _px(sprite_surf, eye_white, bx + 5, head_y + 3, 3, 2)
                _px(sprite_surf, eye_white, bx + 9, head_y + 3, 3, 2)
                # Pupils
                _px(sprite_surf, pupil_c, bx + 6, head_y + 4, 1, 1)
                _px(sprite_surf, pupil_c, bx + 10, head_y + 4, 1, 1)
                # Highlights
                _px(sprite_surf, highlight_c, bx + 5, head_y + 3, 1, 1)
                _px(sprite_surf, highlight_c, bx + 9, head_y + 3, 1, 1)
                # Eyebrows
                _px(sprite_surf, self.hair_color, bx + 5, head_y + 2, 3, 1)
                _px(sprite_surf, self.hair_color, bx + 9, head_y + 2, 3, 1)
            # Mouth
            mouth_c = (200, 110, 100)
            if state == "working":
                # Big smile
                _px(sprite_surf, mouth_c, bx + 6, head_y + 5, 4, 1)
                _px(sprite_surf, (180, 90, 80), bx + 7, head_y + 6, 2, 1)
            elif state == "idle":
                _px(sprite_surf, (180, 100, 90), bx + 7, head_y + 5, 2, 1)
            else:
                # Walking — slight open
                _px(sprite_surf, mouth_c, bx + 7, head_y + 5, 2, 1)
                _px(sprite_surf, (160, 80, 70), bx + 7, head_y + 6, 1, 1)
            # Nose
            _px(sprite_surf, skin_s, bx + 8, head_y + 4, 1, 1)

        elif direction == "up":
            # Back of head — just hair
            self._draw_hair_back(sprite_surf, bx, head_y)
        elif direction == "left":
            if not blinking:
                _px(sprite_surf, eye_white, bx + 4, head_y + 3, 2, 2)
                _px(sprite_surf, pupil_c, bx + 4, head_y + 4, 1, 1)
                _px(sprite_surf, highlight_c, bx + 5, head_y + 3, 1, 1)
                _px(sprite_surf, self.hair_color, bx + 4, head_y + 2, 2, 1)
            else:
                _px(sprite_surf, pupil_c, bx + 4, head_y + 4, 2, 1)
            _px(sprite_surf, (180, 100, 90), bx + 5, head_y + 5, 1, 1)
            _px(sprite_surf, skin_s, bx + 4, head_y + 4, 1, 1)
        elif direction == "right":
            if not blinking:
                _px(sprite_surf, eye_white, bx + 10, head_y + 3, 2, 2)
                _px(sprite_surf, pupil_c, bx + 11, head_y + 4, 1, 1)
                _px(sprite_surf, highlight_c, bx + 10, head_y + 3, 1, 1)
                _px(sprite_surf, self.hair_color, bx + 10, head_y + 2, 2, 1)
            else:
                _px(sprite_surf, pupil_c, bx + 10, head_y + 4, 2, 1)
            _px(sprite_surf, (180, 100, 90), bx + 10, head_y + 5, 1, 1)
            _px(sprite_surf, skin_s, bx + 11, head_y + 4, 1, 1)

        # ── Hair (direction-aware) ──
        if direction != "up":
            self._draw_hair(sprite_surf, bx, head_y, direction)

        # ── Hat / Headgear ──
        self._draw_hat(sprite_surf, bx, head_y - 1)

        # ── Held item (right hand) ──
        if state == "working":
            self._draw_accessory(sprite_surf, bx, torso_y, anim_frame)

        # ── Rarity glow outline ──
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
            surf.blit(glow_surf, (x0 - 4, y0 - 6 * PX))

        # Blit sprite
        surf.blit(sprite_surf, (x0 - 4, y0 - 6 * PX))

        # ── Rarity indicator ──
        if rarity == "legendary":
            star_y = y0 - 8 * PX
            self._draw_star(surf, cx, star_y, (255, 220, 50), anim_frame)
        elif rarity == "epic":
            star_y = y0 - 7 * PX
            self._draw_diamond(surf, cx, star_y, (180, 80, 240), anim_frame)

    def _draw_hair(self, sprite_surf, bx, head_y, direction):
        hc = self.hair_color
        hc_s = _shade(hc, -20)
        style = self.hair_style

        if style == 0:  # Short cropped
            _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 2)
            _px(sprite_surf, hc_s, bx + 4, head_y, 8, 1)
            if direction == "left":
                _px(sprite_surf, hc, bx + 3, head_y, 1, 2)
            elif direction == "right":
                _px(sprite_surf, hc, bx + 12, head_y, 1, 2)
        elif style == 1:  # Spiky
            _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 2)
            _px(sprite_surf, hc, bx + 5, head_y - 2, 2, 1)
            _px(sprite_surf, hc, bx + 8, head_y - 2, 2, 1)
            _px(sprite_surf, hc, bx + 10, head_y - 2, 1, 1)
            _px(sprite_surf, hc_s, bx + 4, head_y, 2, 1)
        elif style == 2:  # Side part
            _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 2)
            _px(sprite_surf, hc_s, bx + 7, head_y - 1, 1, 2)  # part line
            if direction in ("down", "right"):
                _px(sprite_surf, hc, bx + 4, head_y, 3, 2)  # side bang
                _px(sprite_surf, hc_s, bx + 4, head_y + 1, 3, 1)
            else:
                _px(sprite_surf, hc, bx + 9, head_y, 3, 2)
                _px(sprite_surf, hc_s, bx + 9, head_y + 1, 3, 1)
        elif style == 3:  # Buzz cut
            _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 1)
            _px(sprite_surf, hc_s, bx + 5, head_y, 6, 1)
        elif style == 4:  # Curly
            _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 2)
            _px(sprite_surf, hc, bx + 3, head_y, 2, 2)
            _px(sprite_surf, hc, bx + 11, head_y, 2, 2)
            _px(sprite_surf, hc_s, bx + 5, head_y - 2, 1, 1)
            _px(sprite_surf, hc_s, bx + 7, head_y - 2, 1, 1)
            _px(sprite_surf, hc_s, bx + 10, head_y - 2, 1, 1)

    def _draw_hair_back(self, sprite_surf, bx, head_y):
        hc = self.hair_color
        hc_s = _shade(hc, -20)
        _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 3)
        _px(sprite_surf, hc_s, bx + 4, head_y + 2, 8, 1)
        if self.hair_style == 4:  # Curly has more volume
            _px(sprite_surf, hc, bx + 3, head_y, 1, 3)
            _px(sprite_surf, hc, bx + 12, head_y, 1, 3)

    def _draw_hat(self, sprite_surf, bx, head_y):
        hat = self.arch["hat_type"]
        hc = self.arch["hat_color"]
        if not hc:
            return

        if hat == "chef_hat":
            hc_s = _shade(hc, -15)
            _px(sprite_surf, hc, bx + 4, head_y - 4, 8, 5)
            _px(sprite_surf, hc, bx + 3, head_y, 10, 1)
            _px(sprite_surf, hc_s, bx + 10, head_y - 4, 2, 5)
            # Poof on top
            _px(sprite_surf, (248, 248, 255), bx + 6, head_y - 5, 4, 1)
            _px(sprite_surf, (248, 248, 255), bx + 7, head_y - 6, 2, 1)
            # Band
            _px(sprite_surf, (220, 220, 230), bx + 4, head_y, 8, 1)

        elif hat == "hardhat":
            hc_s = _shade(hc, -20)
            _px(sprite_surf, hc, bx + 3, head_y - 1, 10, 2)
            _px(sprite_surf, hc, bx + 4, head_y - 2, 8, 1)
            _px(sprite_surf, hc_s, bx + 10, head_y - 1, 3, 2)
            # Brim
            _px(sprite_surf, _shade(hc, -30), bx + 2, head_y + 1, 12, 1)
            # Ridge
            _px(sprite_surf, (255, 240, 60), bx + 7, head_y - 2, 2, 1)

        elif hat == "beanie":
            hc_s = _shade(hc, -15)
            _px(sprite_surf, hc, bx + 4, head_y - 2, 8, 3)
            _px(sprite_surf, hc, bx + 5, head_y - 3, 6, 1)
            _px(sprite_surf, hc_s, bx + 10, head_y - 2, 2, 3)
            # Fold line
            fc = _shade(hc, 25)
            _px(sprite_surf, fc, bx + 4, head_y, 8, 1)
            # Pompom
            _px(sprite_surf, fc, bx + 7, head_y - 4, 2, 1)

        elif hat == "cap":
            hc_s = _shade(hc, -25)
            _px(sprite_surf, hc, bx + 4, head_y - 1, 8, 2)
            _px(sprite_surf, hc, bx + 5, head_y - 2, 6, 1)
            _px(sprite_surf, hc_s, bx + 10, head_y - 1, 2, 2)
            # Brim
            brim_c = _shade(hc, -40)
            _px(sprite_surf, brim_c, bx + 2, head_y + 1, 6, 1)
            # Logo dot
            _px(sprite_surf, (255, 255, 255), bx + 7, head_y - 1, 1, 1)

    def _draw_accessory(self, sprite_surf, bx, torso_y, frame):
        acc = self.arch["accessory"]
        ax = bx + 13
        ay = torso_y + 3 + (1 if frame % 2 == 0 else 0)

        if acc == "spatula":
            _px(sprite_surf, (100, 80, 50), ax, ay + 2, 1, 3)  # handle
            _px(sprite_surf, (190, 190, 200), ax - 1, ay - 1, 3, 1)  # blade top
            _px(sprite_surf, (180, 180, 190), ax - 1, ay, 3, 2)  # blade
            _px(sprite_surf, (200, 200, 210), ax, ay - 1, 1, 1)  # highlight

        elif acc == "coffee_cup":
            _px(sprite_surf, (245, 235, 220), ax - 1, ay, 3, 4)  # cup
            _px(sprite_surf, (170, 110, 70), ax - 1, ay + 1, 3, 1)  # sleeve
            _px(sprite_surf, (230, 220, 200), ax - 1, ay, 3, 1)  # lid edge
            _px(sprite_surf, (220, 210, 190), ax, ay - 1, 1, 1)  # lid top
            # Handle
            _px(sprite_surf, (200, 190, 170), ax + 2, ay + 1, 1, 2)
            # Steam
            if frame % 4 < 2:
                _px(sprite_surf, (200, 200, 220), ax, ay - 2, 1, 1)
                _px(sprite_surf, (180, 180, 210), ax - 1, ay - 3, 1, 1)

        elif acc == "wrench":
            _px(sprite_surf, (120, 90, 50), ax, ay + 2, 1, 3)  # handle
            _px(sprite_surf, (180, 180, 195), ax - 1, ay, 3, 2)  # jaw
            _px(sprite_surf, (200, 200, 215), ax, ay, 1, 1)  # highlight
            _px(sprite_surf, (160, 160, 175), ax - 1, ay + 1, 1, 1)  # gap

        elif acc == "box":
            _px(sprite_surf, (200, 170, 120), ax - 2, ay, 4, 3)  # box
            _px(sprite_surf, (180, 150, 100), ax - 1, ay + 1, 2, 1)  # tape
            _px(sprite_surf, (170, 140, 90), ax - 2, ay + 2, 4, 1)  # shade
            _px(sprite_surf, (220, 190, 140), ax - 2, ay, 4, 1)  # top highlight

        elif acc == "mop":
            _px(sprite_surf, (170, 150, 110), ax, ay - 2, 1, 6)  # handle
            _px(sprite_surf, (210, 210, 220), ax - 1, ay + 3, 3, 2)  # mop head
            _px(sprite_surf, (190, 190, 200), ax - 1, ay + 4, 3, 1)  # shade
            _px(sprite_surf, (160, 160, 170), ax - 2, ay + 4, 1, 1)  # drip

    def _draw_star(self, surf, cx, cy, color, frame):
        """Animated star above legendary workers."""
        bob = int(math.sin(frame * 0.3) * 3)
        ps = PX
        # Larger cross-star
        color_s = _shade(color, -30)
        pygame.draw.rect(surf, color, (cx - ps, cy + bob, ps * 2, ps))
        pygame.draw.rect(surf, color, (cx - ps // 2, cy + bob - ps, ps, ps * 3))
        # Corner sparkle
        pygame.draw.rect(surf, color_s, (cx - ps, cy + bob - ps // 2, ps // 2, ps // 2))
        pygame.draw.rect(surf, color_s, (cx + ps, cy + bob - ps // 2, ps // 2, ps // 2))
        # Ray particles
        if frame % 8 < 4:
            pygame.draw.rect(surf, (*color[:3],), (cx - ps * 2, cy + bob, ps // 2, ps // 2))
            pygame.draw.rect(surf, (*color[:3],), (cx + ps * 2, cy + bob, ps // 2, ps // 2))

    def _draw_diamond(self, surf, cx, cy, color, frame):
        """Animated diamond above epic workers."""
        bob = int(math.sin(frame * 0.25) * 2)
        ps = PX
        color_s = _shade(color, 30)
        pygame.draw.rect(surf, color, (cx - ps // 2, cy + bob - ps, ps, ps))
        pygame.draw.rect(surf, color, (cx - ps, cy + bob, ps * 2, ps))
        pygame.draw.rect(surf, color, (cx - ps // 2, cy + bob + ps, ps, ps))
        # Inner highlight
        pygame.draw.rect(surf, color_s, (cx - ps // 4, cy + bob, ps // 2, ps // 2))


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

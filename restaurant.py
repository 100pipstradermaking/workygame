"""
restaurant.py — 2D top-down burger restaurant world.
Manages the restaurant floor, stations, worker pathfinding/movement,
customer NPCs, and ambient visual effects (steam, fire, burger pops).
Inspired by Kairosoft's Burger Bistro Story.
"""

import pygame
import math
import random
from sprites import WorkySpriteRenderer, draw_speech_bubble
import icons

# ── Station definitions ──────────────────────────────────────

STATION_DEFS = [
    {
        "id": "storage",
        "name": "Storage",
        "color": (120, 90, 60),
        "accent": (160, 120, 70),
        "icon_color": (200, 160, 80),
        "work_time": 1.5,
        "description": "Grab ingredients",
    },
    {
        "id": "grill",
        "name": "Grill",
        "color": (60, 60, 65),
        "accent": (255, 100, 40),
        "icon_color": (255, 140, 50),
        "work_time": 2.5,
        "description": "Cook the patty",
    },
    {
        "id": "assembly",
        "name": "Assembly",
        "color": (200, 200, 210),
        "accent": (100, 200, 100),
        "icon_color": (80, 180, 80),
        "work_time": 2.0,
        "description": "Assemble the burger",
    },
    {
        "id": "counter",
        "name": "Counter",
        "color": (140, 80, 50),
        "accent": (255, 210, 80),
        "icon_color": (255, 220, 100),
        "work_time": 1.0,
        "description": "Serve the customer",
    },
]

TILE_SIZE = 16

# ── Customer NPC colors / looks ──────────────────────────────
_CUSTOMER_SHIRTS = [
    (180, 60, 60), (60, 120, 180), (60, 160, 80), (200, 160, 50),
    (160, 80, 160), (80, 180, 180), (200, 120, 60), (100, 100, 180),
]
_CUSTOMER_SKINS = [
    (240, 200, 160), (220, 180, 140), (190, 140, 100),
    (160, 110, 70), (120, 80, 50),
]


class Station:
    """A workstation in the restaurant."""

    def __init__(self, station_def: dict, x: int, y: int, w: int = 3, h: int = 2):
        self.id = station_def["id"]
        self.name = station_def["name"]
        self.color = station_def["color"]
        self.accent = station_def["accent"]
        self.icon_color = station_def["icon_color"]
        self.work_time = station_def["work_time"]
        self.tx, self.ty = x, y
        self.tw, self.th = w, h
        self.px = (x + w / 2) * TILE_SIZE
        self.py = (y + h / 2) * TILE_SIZE
        self.work_x = self.px
        self.work_y = (y + h + 0.5) * TILE_SIZE
        self.active_timer = 0.0

    def draw(self, surf: pygame.Surface, ox: int, oy: int, anim_t: float = 0.0):
        """Draw the station with animated icons."""
        x = int(self.tx * TILE_SIZE + ox)
        y = int(self.ty * TILE_SIZE + oy)
        w = self.tw * TILE_SIZE
        h = self.th * TILE_SIZE

        # Main body
        pygame.draw.rect(surf, self.color, (x, y, w, h))
        pygame.draw.rect(surf, self.accent, (x, y, w, h), 2)

        # Glow when active
        if self.active_timer > 0:
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            alpha = int(60 * min(self.active_timer, 1.0))
            glow.fill((*self.accent, alpha))
            surf.blit(glow, (x, y))

        self._draw_icon(surf, x, y, w, h, anim_t)

        # Label
        font = pygame.font.SysFont("Consolas", 10)
        label = font.render(self.name, True, (220, 220, 220))
        surf.blit(label, (x + 2, y + h + 2))

    def _draw_icon(self, surf: pygame.Surface, x: int, y: int,
                   w: int, h: int, t: float = 0.0):
        cx, cy = x + w // 2, y + h // 2
        ps = 4

        if self.id == "storage":
            for dx in range(-2, 3):
                for dy in range(-1, 2):
                    pygame.draw.rect(surf, self.icon_color,
                                     (cx + dx * ps - ps, cy + dy * ps - ps, ps, ps))
            pygame.draw.rect(surf, (100, 70, 40), (cx - ps, cy - ps // 2, ps * 2, ps))
            pygame.draw.rect(surf, (100, 70, 40), (cx - ps // 2, cy - ps, ps, ps * 2))

        elif self.id == "grill":
            # Animated fire flames that flicker
            for i, base_c in enumerate([(255, 60, 20), (255, 140, 30), (255, 200, 60)]):
                fh = (3 - i) * ps
                fw = (3 - i) * ps
                flicker = int(2 * math.sin(t * 8 + i * 1.5))
                r = min(255, base_c[0] + flicker * 10)
                g = min(255, base_c[1] + flicker * 5)
                pygame.draw.rect(surf, (r, g, base_c[2]),
                                 (cx - fw // 2 + flicker, cy - fh + ps - abs(flicker),
                                  fw, fh + abs(flicker)))
            # Grill lines
            for dx in range(-2, 3):
                pygame.draw.rect(surf, (80, 80, 90),
                                 (cx + dx * ps - ps // 2, cy + ps, ps // 2, ps))

        elif self.id == "assembly":
            colors = [(210, 160, 60), (100, 50, 20), (60, 180, 60), (190, 140, 50)]
            for i, c in enumerate(colors):
                pygame.draw.rect(surf, c,
                                 (cx - 2 * ps, cy - 2 * ps + i * ps, 4 * ps, ps))

        elif self.id == "counter":
            pygame.draw.rect(surf, self.icon_color,
                             (cx - ps, cy - ps, ps * 3, ps * 2))
            pygame.draw.rect(surf, (200, 170, 60),
                             (cx - ps, cy - 2 * ps, ps * 3, ps))
            pygame.draw.rect(surf, (100, 70, 30), (cx, cy - ps, ps, ps))

    def update(self, dt: float):
        if self.active_timer > 0:
            self.active_timer -= dt


# ── Customer NPC ──────────────────────────────────────────────

class CustomerNPC:
    """A simple customer that walks to a table, sits, eats, and leaves."""

    SPEED = 35.0

    def __init__(self, table_x: float, table_y: float, door_x: float, door_y: float):
        self.x = door_x
        self.y = door_y
        self.table_x = table_x
        self.table_y = table_y
        self.door_x = door_x
        self.door_y = door_y
        self.shirt = random.choice(_CUSTOMER_SHIRTS)
        self.skin = random.choice(_CUSTOMER_SKINS)
        self.state = "entering"   # entering | sitting | eating | leaving | done
        self.timer = 0.0
        self.eat_duration = random.uniform(4.0, 8.0)
        self.satisfaction = random.choice(["!", "♥", "★", ":)"])
        self.sat_timer = 0.0
        self.direction = "up"

    def update(self, dt: float):
        if self.state == "entering":
            dx = self.table_x - self.x
            dy = self.table_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 3:
                self.state = "sitting"
                self.timer = 0.5  # brief pause before eating
                return
            step = self.SPEED * dt
            if step > dist:
                step = dist
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.direction = "up" if dy < 0 else "down"

        elif self.state == "sitting":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "eating"
                self.timer = self.eat_duration

        elif self.state == "eating":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "leaving"
                self.sat_timer = 1.5  # show satisfaction icon

        elif self.state == "leaving":
            self.sat_timer -= dt
            dx = self.door_x - self.x
            dy = self.door_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 3:
                self.state = "done"
                return
            step = self.SPEED * dt
            if step > dist:
                step = dist
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.direction = "down" if dy > 0 else "up"

    def draw(self, surf: pygame.Surface, ox: int, oy: int, anim_t: float):
        sx = int(self.x + ox)
        sy = int(self.y + oy)
        PX = 2

        # Shadow
        pygame.draw.ellipse(surf, (0, 0, 0, 50),
                            (sx - 5 * PX, sy + 7 * PX, 10 * PX, 3 * PX))
        # Body
        pygame.draw.rect(surf, self.shirt, (sx - 3 * PX, sy - 2 * PX, 6 * PX, 5 * PX))
        # Head
        pygame.draw.rect(surf, self.skin, (sx - 3 * PX, sy - 6 * PX, 6 * PX, 4 * PX))
        # Eyes
        if self.direction != "up":
            pygame.draw.rect(surf, (30, 30, 40), (sx - 2 * PX, sy - 4 * PX, PX, PX))
            pygame.draw.rect(surf, (30, 30, 40), (sx + 1 * PX, sy - 4 * PX, PX, PX))
        # Legs
        walk = 0
        if self.state in ("entering", "leaving"):
            walk = int(math.sin(anim_t * 8) * PX)
        pygame.draw.rect(surf, (50, 45, 55),
                         (sx - 2 * PX, sy + 3 * PX + walk, 2 * PX, 3 * PX))
        pygame.draw.rect(surf, (50, 45, 55),
                         (sx, sy + 3 * PX - walk, 2 * PX, 3 * PX))

        # Eating animation — burger in hand
        if self.state == "eating":
            bob = int(math.sin(anim_t * 4) * PX)
            pygame.draw.rect(surf, (200, 160, 60),
                             (sx + 3 * PX, sy - 2 * PX + bob, 3 * PX, 2 * PX))
            pygame.draw.rect(surf, (100, 50, 20),
                             (sx + 3 * PX, sy - 1 * PX + bob, 3 * PX, PX))

        # Satisfaction bubble
        if self.state == "leaving" and self.sat_timer > 0:
            alpha = min(255, int(255 * self.sat_timer / 1.5))
            font = pygame.font.SysFont("Consolas", 14)
            txt = font.render(self.satisfaction, True, (255, 220, 80))
            ts = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            ts.blit(txt, (0, 0))
            ts.set_alpha(alpha)
            surf.blit(ts, (sx - txt.get_width() // 2, sy - 12 * PX))


# ── Particle effects ─────────────────────────────────────────

class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "kind")

    def __init__(self, x, y, vx, vy, life, color, size=2, kind="generic"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.kind = kind


# ── Worker movement states ────────────────────────────────────

class WorkerSprite:
    """Visual representation of a worker moving in the restaurant."""

    MOVE_SPEED = 50.0

    def __init__(self, worker_ref, color: tuple, worker_index: int):
        self.worker_ref = worker_ref
        self.color = color
        self.index = worker_index
        self.sprite_renderer = WorkySpriteRenderer(
            archetype_id=worker_ref.archetype,
            rarity_color=color,
            skin=worker_ref.skin_tone,
        )
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.moving = False
        self.current_station_idx = 0
        self.state = "idle"
        self.work_timer = 0.0
        self.burgers_made = 0
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.direction = "down"
        self.bounce = 0.0
        self.anim_global = 0
        self._just_completed_station = None  # track station completion for effects

    def assign_to_station(self, station: Station, offset: int = 0):
        ofs = (offset % 3 - 1) * 12
        self.target_x = station.work_x + ofs
        self.target_y = station.work_y + (offset // 3) * 12
        self.moving = True
        self.state = "walking"

    def update(self, dt: float, stations: list["Station"]):
        self._just_completed_station = None
        if self.state == "walking":
            self._move(dt)
        elif self.state == "working":
            self._work(dt, stations)
        elif self.state == "idle":
            if stations:
                st = stations[self.current_station_idx]
                self.assign_to_station(st, self.index)

        self.anim_timer += dt
        if self.anim_timer > 0.12:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4
            self.anim_global += 1

        # Update blink animation
        self.sprite_renderer.update_blink(dt)

        if self.state == "working":
            self.bounce = math.sin(self.anim_timer * 15) * 1.5
        else:
            self.bounce *= 0.9  # smooth decay instead of instant zero

    def _move(self, dt: float):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < 2.0:
            self.x = self.target_x
            self.y = self.target_y
            self.moving = False
            self.state = "working"
            self.work_timer = 0.0
            return

        speed = self.MOVE_SPEED * (1 + self.worker_ref.speed * 0.1)
        step = speed * dt
        if step > dist:
            step = dist
        self.x += (dx / dist) * step
        self.y += (dy / dist) * step

        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        else:
            self.direction = "down" if dy > 0 else "up"

    def _work(self, dt: float, stations: list["Station"]):
        st = stations[self.current_station_idx]
        work_speed = 1.0 + self.worker_ref.speed * 0.05
        self.work_timer += dt * work_speed
        st.active_timer = 1.0

        if self.work_timer >= st.work_time:
            completed_id = st.id
            self.current_station_idx = (self.current_station_idx + 1) % len(stations)
            if self.current_station_idx == 0:
                self.burgers_made += 1
            self._just_completed_station = completed_id
            next_st = stations[self.current_station_idx]
            self.assign_to_station(next_st, self.index)

    def draw(self, surf: pygame.Surface, ox: int, oy: int):
        x = int(self.x + ox)
        y = int(self.y + oy + self.bounce)
        self.sprite_renderer.draw(
            surf, x, y,
            direction=self.direction,
            anim_frame=self.anim_global,
            state=self.state,
            rarity=self.worker_ref.rarity,
        )

    def draw_status(self, surf: pygame.Surface, ox: int, oy: int, font: pygame.font.Font):
        x = int(self.x + ox)
        y = int(self.y + oy) - 28

        if self.state == "working":
            station = STATION_DEFS[self.current_station_idx]
            icons = {"storage": "📦", "grill": "🔥", "assembly": "🍔", "counter": "$$$"}
            label = icons.get(station["id"], "...")
            color = (255, 200, 100)
        elif self.state == "walking":
            return
        else:
            label = "zzz"
            color = (150, 150, 150)

        draw_speech_bubble(surf, x, y, label, color, font)


# ── Restaurant world ─────────────────────────────────────────

class Restaurant:
    """The 2D restaurant floor with stations, workers, customers, and effects."""

    FLOOR_W = 34
    FLOOR_H = 26

    def __init__(self):
        self.stations: list[Station] = []
        self.worker_sprites: list[WorkerSprite] = []

        self._build_layout()

        self.floor_color_a = (55, 50, 45)
        self.floor_color_b = (48, 43, 38)
        self.wall_color = (80, 70, 65)
        self.wall_top = (100, 88, 78)

        self.decorations: list[dict] = []
        self._add_base_decorations()

        self._seat_lvl = -1
        self._neon_lvl = -1
        self._floor_lvl = -1
        self._paint_lvl = -1
        self._music_lvl = -1
        self._ac_lvl = -1
        self._attractiveness = 0
        self._community_rating = 0.0
        self._community_votes = 0

        # Animation / effects
        self._anim_t = 0.0
        self._music_particles: list[dict] = []
        self._particles: list[_Particle] = []     # generic particle system
        self._customers: list[CustomerNPC] = []    # active customer NPCs
        self._customer_timer = 0.0                 # spawn timer
        self._customer_spawn_interval = 6.0        # seconds between spawns
        self._table_positions_px: list[tuple] = [] # filled by apply_customization

    def _build_layout(self):
        """Place stations in the restaurant. Kairosoft-style layout:
        Top-left: Storage, Top-right: Grill,
        Center: Assembly, Bottom-center: Counter.
        """
        # Station placement (tile coords)
        placements = [
            (STATION_DEFS[0], 3, 3, 4, 3),      # Storage — top left
            (STATION_DEFS[1], 14, 2, 5, 3),      # Grill — top center-right
            (STATION_DEFS[2], 9, 10, 5, 3),      # Assembly — center
            (STATION_DEFS[3], 9, 19, 6, 3),      # Counter — bottom center
        ]
        for defn, tx, ty, tw, th in placements:
            self.stations.append(Station(defn, tx, ty, tw, th))

    def _add_base_decorations(self):
        """Add permanent decorations (plants, door). Tables are dynamic."""
        self.decorations.clear()
        # Plants
        for pos in [(1, 1), (30, 1), (1, 22), (30, 22)]:
            self.decorations.append({
                "type": "plant",
                "x": pos[0], "y": pos[1],
                "w": 2, "h": 2,
                "color": (60, 140, 60),
            })
        # Door
        self.decorations.append({
            "type": "door",
            "x": 14, "y": 23,
            "w": 4, "h": 2,
            "color": (100, 70, 40),
        })

    # ── Visual customization system ──────────────────────────

    def apply_customization(self, player):
        """Rebuild visual appearance from design upgrade levels.
        Call this when upgrades change or once per frame (cheap)."""
        from shop import (shop_item_level, get_seat_count,
                          get_attractiveness)

        seat_lvl = shop_item_level(player, "design_seats")
        neon_lvl = shop_item_level(player, "design_neon")
        floor_lvl = shop_item_level(player, "design_floor")
        paint_lvl = shop_item_level(player, "design_paint")
        music_lvl = shop_item_level(player, "design_music")
        ac_lvl = shop_item_level(player, "design_ac")

        # Only rebuild decorations if anything changed
        changed = (seat_lvl != self._seat_lvl or neon_lvl != self._neon_lvl or
                   floor_lvl != self._floor_lvl or paint_lvl != self._paint_lvl or
                   music_lvl != self._music_lvl or ac_lvl != self._ac_lvl)

        self._seat_lvl = seat_lvl
        self._neon_lvl = neon_lvl
        self._floor_lvl = floor_lvl
        self._paint_lvl = paint_lvl
        self._music_lvl = music_lvl
        self._ac_lvl = ac_lvl
        self._attractiveness = get_attractiveness(player)

        if not changed:
            return

        # ── Rebuild dynamic decorations ──────────────────────
        self._add_base_decorations()
        self._table_positions_px = []

        # ─ FLOOR upgrade ─────────────────────────────────────
        if floor_lvl == 0:
            self.floor_color_a = (55, 50, 45)
            self.floor_color_b = (48, 43, 38)
        elif floor_lvl == 1:
            self.floor_color_a = (65, 55, 45)
            self.floor_color_b = (55, 48, 38)
        elif floor_lvl == 2:
            self.floor_color_a = (70, 60, 50)
            self.floor_color_b = (58, 50, 42)
        elif floor_lvl == 3:
            self.floor_color_a = (80, 65, 50)
            self.floor_color_b = (65, 55, 42)
        elif floor_lvl == 4:
            self.floor_color_a = (90, 75, 55)
            self.floor_color_b = (75, 62, 48)
        else:
            # Max — polished marble look
            self.floor_color_a = (100, 90, 75)
            self.floor_color_b = (85, 78, 65)

        # ─ WALL PAINT upgrade ────────────────────────────────
        if paint_lvl == 0:
            self.wall_color = (80, 70, 65)
            self.wall_top = (100, 88, 78)
        elif paint_lvl <= 3:
            # Warm tones
            t = paint_lvl / 3
            self.wall_color = (int(80 + 40 * t), int(70 + 20 * t), int(65 + 10 * t))
            self.wall_top = (int(100 + 50 * t), int(88 + 30 * t), int(78 + 10 * t))
        elif paint_lvl <= 6:
            # Rich tones
            t = (paint_lvl - 3) / 3
            self.wall_color = (int(120 - 30 * t), int(90 + 20 * t), int(75 + 25 * t))
            self.wall_top = (int(150 - 20 * t), int(118 + 30 * t), int(88 + 40 * t))
        else:
            # Premium
            t = (paint_lvl - 6) / 4
            self.wall_color = (int(90 + 20 * t), int(110 + 15 * t), int(100 + 20 * t))
            self.wall_top = (int(130 + 15 * t), int(148 + 10 * t), int(128 + 15 * t))

        # Wall art frames (paintings on walls) — one per 2 paint levels
        art_count = min(5, paint_lvl // 2)
        art_colors = [(180, 60, 60), (60, 120, 180), (180, 160, 50),
                      (60, 160, 100), (160, 80, 180)]
        art_positions = [(5, 1), (10, 1), (20, 1), (28, 1), (15, 1)]
        for i in range(art_count):
            px, py = art_positions[i]
            self.decorations.append({
                "type": "wall_art",
                "x": px, "y": py,
                "w": 2, "h": 1,
                "color": art_colors[i],
            })

        # ─ TABLES (seats) ────────────────────────────────────
        seat_count = 3 + seat_lvl * 2  # total seats from get_seat_count
        table_count = max(1, seat_count // 2)  # ~2 seats per table

        # Table layout — right side + extra rows
        table_positions = [
            (24, 5), (24, 11), (24, 17),  # right column (base 3)
            (28, 5), (28, 11), (28, 17),  # far right column
            (21, 8), (21, 14),             # center-right
            (24, 20), (28, 20),            # bottom right
            (21, 5), (21, 17),             # more center
        ]

        for i in range(min(table_count, len(table_positions))):
            tx, ty = table_positions[i]

            if seat_lvl <= 3:
                t_color = (120, 80, 45)
                c_color = (100, 65, 35)
            elif seat_lvl <= 7:
                t_color = (140, 100, 55)
                c_color = (120, 85, 50)
            else:
                t_color = (160, 120, 70)
                c_color = (140, 105, 65)

            self.decorations.append({
                "type": "table", "x": tx, "y": ty,
                "w": 3, "h": 2, "color": t_color,
            })
            self.decorations.append({
                "type": "chair", "x": tx - 1, "y": ty,
                "w": 1, "h": 2, "color": c_color,
            })
            self.decorations.append({
                "type": "chair", "x": tx + 3, "y": ty,
                "w": 1, "h": 2, "color": c_color,
            })
            # Track table pixel positions for customer NPC seating
            self._table_positions_px.append((
                (tx + 1.5) * TILE_SIZE,
                (ty + 1) * TILE_SIZE,
            ))

        # Adjust customer spawn rate based on attractiveness
        self._customer_spawn_interval = max(2.0, 8.0 - self._attractiveness * 0.05)

        # ─ NEON SIGNS ────────────────────────────────────────
        neon_defs = [
            {"x": 2, "y": 0, "w": 4, "h": 1,
             "text": "OPEN", "color": (255, 80, 200)},
            {"x": 22, "y": 0, "w": 5, "h": 1,
             "text": "BURGERS", "color": (80, 255, 200)},
            {"x": 11, "y": 0, "w": 4, "h": 1,
             "text": "WORKY", "color": (255, 200, 50)},
            {"x": 28, "y": 0, "w": 3, "h": 1,
             "text": "HOT", "color": (255, 100, 60)},
            {"x": 7, "y": 0, "w": 3, "h": 1,
             "text": "EAT", "color": (100, 200, 255)},
            {"x": 17, "y": 0, "w": 3, "h": 1,
             "text": "YUM", "color": (200, 255, 80)},
            {"x": 31, "y": 0, "w": 2, "h": 1,
             "text": "24h", "color": (255, 150, 255)},
            {"x": 0, "y": 12, "w": 1, "h": 3,
             "text": "", "color": (100, 255, 200)},  # wall strip
        ]
        for i in range(min(neon_lvl, len(neon_defs))):
            nd = neon_defs[i]
            self.decorations.append({
                "type": "neon",
                "x": nd["x"], "y": nd["y"],
                "w": nd["w"], "h": nd["h"],
                "color": nd["color"],
                "text": nd["text"],
            })

        # ─ AC UNITS ──────────────────────────────────────────
        ac_positions = [(1, 3), (31, 3), (1, 15), (31, 15), (16, 0)]
        for i in range(min(ac_lvl, len(ac_positions))):
            ax, ay = ac_positions[i]
            self.decorations.append({
                "type": "ac_unit",
                "x": ax, "y": ay,
                "w": 2, "h": 1,
                "color": (200, 220, 240),
            })

        # ─ SPEAKERS (music) ──────────────────────────────────
        speaker_positions = [(0, 8), (32, 8), (0, 18), (32, 18), (16, 0), (8, 0)]
        for i in range(min(music_lvl, len(speaker_positions))):
            sx, sy = speaker_positions[i]
            self.decorations.append({
                "type": "speaker",
                "x": sx, "y": sy,
                "w": 1, "h": 1,
                "color": (60, 55, 70),
            })

    def sync_workers(self, workers: list):
        """Sync worker sprites with actual worker list."""
        while len(self.worker_sprites) < len(workers):
            idx = len(self.worker_sprites)
            w = workers[idx]
            sprite = WorkerSprite(w, w.color, idx)
            if self.stations:
                st = self.stations[0]
                sprite.x = st.work_x + (idx % 3 - 1) * 14
                sprite.y = st.work_y + (idx // 3) * 14
            self.worker_sprites.append(sprite)

        if len(self.worker_sprites) > len(workers):
            self.worker_sprites = self.worker_sprites[:len(workers)]

        for i, ws in enumerate(self.worker_sprites):
            if i < len(workers):
                w = workers[i]
                ws.worker_ref = w
                ws.color = w.color
                if ws.sprite_renderer.archetype_id != w.archetype:
                    ws.sprite_renderer = WorkySpriteRenderer(
                        archetype_id=w.archetype,
                        rarity_color=w.color,
                        skin=w.skin_tone,
                    )

    def update(self, dt: float):
        self._anim_t += dt
        for st in self.stations:
            st.update(dt)
        for ws in self.worker_sprites:
            ws.update(dt, self.stations)
            # Spawn effect particles when worker finishes a station
            if ws._just_completed_station:
                self._spawn_station_effect(ws)

        if self._music_lvl > 0:
            self._update_music_particles(dt)

        # Update generic particles
        alive = []
        for p in self._particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 30 * dt  # gravity for some
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self._particles = alive[:80]

        # Spawn steam from grill when active
        grill_st = self.stations[1] if len(self.stations) > 1 else None
        if grill_st and grill_st.active_timer > 0:
            if random.random() < 2.0 * dt:
                self._particles.append(_Particle(
                    grill_st.px + random.uniform(-12, 12),
                    grill_st.py - 8,
                    random.uniform(-3, 3),
                    random.uniform(-25, -15),
                    random.uniform(0.6, 1.2),
                    (200, 200, 220),
                    size=random.choice([2, 3]),
                    kind="steam",
                ))

        # Update customer NPCs
        self._update_customers(dt)

    def _spawn_station_effect(self, ws: WorkerSprite):
        """Spawn visual particles when a worker finishes at a station."""
        sid = ws._just_completed_station
        cx, cy = ws.x, ws.y

        if sid == "grill":
            # Fire sparks
            for _ in range(4):
                self._particles.append(_Particle(
                    cx + random.uniform(-6, 6), cy - 10,
                    random.uniform(-20, 20), random.uniform(-40, -15),
                    random.uniform(0.3, 0.6),
                    random.choice([(255, 140, 40), (255, 200, 60), (255, 80, 30)]),
                    size=2, kind="spark",
                ))
        elif sid == "counter":
            # Burger served — green coin burst
            for _ in range(6):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(20, 50)
                self._particles.append(_Particle(
                    cx, cy - 5,
                    math.cos(angle) * speed, math.sin(angle) * speed - 20,
                    random.uniform(0.5, 1.0),
                    random.choice([(255, 220, 50), (80, 230, 120), (255, 200, 80)]),
                    size=3, kind="coin",
                ))
        elif sid == "assembly":
            # Small green sparkles
            for _ in range(3):
                self._particles.append(_Particle(
                    cx + random.uniform(-8, 8), cy - 5,
                    random.uniform(-15, 15), random.uniform(-30, -10),
                    random.uniform(0.3, 0.5),
                    (100, 230, 100),
                    size=2, kind="sparkle",
                ))

    def _update_customers(self, dt: float):
        """Spawn and manage customer NPCs."""
        # Only spawn if we have tables
        if not self._table_positions_px:
            return

        self._customer_timer += dt
        max_customers = max(1, len(self._table_positions_px) // 2)

        # Active customers (not done)
        active = [c for c in self._customers if c.state != "done"]

        if self._customer_timer >= self._customer_spawn_interval and len(active) < max_customers:
            self._customer_timer = 0.0
            # Pick a free table
            occupied = {(int(c.table_x), int(c.table_y))
                        for c in active if c.state in ("entering", "sitting", "eating")}
            free = [(tx, ty) for (tx, ty) in self._table_positions_px
                    if (int(tx), int(ty)) not in occupied]
            if free:
                tx, ty = random.choice(free)
                door_x = 16 * TILE_SIZE  # center of door
                door_y = (self.FLOOR_H - 1) * TILE_SIZE
                self._customers.append(CustomerNPC(tx, ty, door_x, door_y))

        # Update all customers
        for c in self._customers:
            c.update(dt)

        # Remove done customers
        self._customers = [c for c in self._customers if c.state != "done"]

    def _update_music_particles(self, dt: float):
        """Spawn and animate floating music note particles."""
        # Spawn rate increases with level
        spawn_chance = self._music_lvl * 0.3 * dt
        if random.random() < spawn_chance:
            # Spawn near a speaker decoration
            speakers = [d for d in self.decorations if d["type"] == "speaker"]
            if speakers:
                sp = random.choice(speakers)
                self._music_particles.append({
                    "x": (sp["x"] + 0.5) * TILE_SIZE,
                    "y": (sp["y"] + 0.5) * TILE_SIZE,
                    "vx": random.uniform(-8, 8),
                    "vy": -random.uniform(15, 30),
                    "life": random.uniform(1.5, 3.0),
                    "max_life": 3.0,
                    "note": random.choice(["♪", "♫", "♩", "~"]),
                    "color": random.choice([
                        (200, 130, 255), (130, 200, 255),
                        (255, 200, 130), (200, 255, 130),
                    ]),
                })

        # Update existing
        alive = []
        for p in self._music_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] -= 5 * dt  # slow deceleration
            p["life"] -= dt
            if p["life"] > 0:
                alive.append(p)
        self._music_particles = alive[:30]  # cap max particles

    def draw(self, surf: pygame.Surface, area_rect: pygame.Rect):
        """Draw the restaurant world within the given screen area."""
        world_w = self.FLOOR_W * TILE_SIZE
        world_h = self.FLOOR_H * TILE_SIZE
        ox = area_rect.x + (area_rect.width - world_w) // 2
        oy = area_rect.y + (area_rect.height - world_h) // 2

        clip_prev = surf.get_clip()
        surf.set_clip(area_rect)

        # Floor
        self._draw_floor(surf, ox, oy)

        # Walls
        self._draw_walls(surf, ox, oy, world_w, world_h)

        # Decorations
        self._draw_decorations(surf, ox, oy)

        # Stations (with animated icons)
        for st in self.stations:
            st.draw(surf, ox, oy, self._anim_t)

        # Customers (behind workers, sorted by Y)
        for c in sorted(self._customers, key=lambda c: c.y):
            c.draw(surf, ox, oy, self._anim_t)

        # Workers (sorted by y for depth)
        sorted_workers = sorted(self.worker_sprites, key=lambda w: w.y)
        font_tiny = pygame.font.SysFont("Consolas", 9)
        for ws in sorted_workers:
            ws.draw(surf, ox, oy)
            ws.draw_status(surf, ox, oy, font_tiny)

        # Particles (steam, sparks, coins — on top)
        self._draw_particles(surf, ox, oy)

        # Music particles
        self._draw_music_particles(surf, ox, oy)

        # Badges
        if self._attractiveness > 0:
            self._draw_attractiveness_badge(surf, area_rect)
        if self._community_votes > 0:
            self._draw_rating_badge(surf, area_rect)

        surf.set_clip(clip_prev)

    def _draw_particles(self, surf: pygame.Surface, ox: int, oy: int):
        """Draw all generic particles (steam, sparks, coins, sparkles)."""
        for p in self._particles:
            alpha = max(0, min(255, int(255 * (p.life / p.max_life))))
            px = int(p.x + ox)
            py = int(p.y + oy)
            if p.kind == "steam":
                # Expanding translucent circles
                sz = int(p.size + (1 - p.life / p.max_life) * 3)
                s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, alpha // 2), (sz, sz), sz)
                surf.blit(s, (px - sz, py - sz))
            elif p.kind == "spark":
                s = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                s.fill((*p.color, alpha))
                surf.blit(s, (px, py))
            elif p.kind == "coin":
                s = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, alpha),
                                   (p.size // 2, p.size // 2), p.size // 2)
                surf.blit(s, (px, py))
            else:
                s = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
                s.fill((*p.color, alpha))
                surf.blit(s, (px, py))

    def _draw_floor(self, surf: pygame.Surface, ox: int, oy: int):
        for ty in range(self.FLOOR_H):
            for tx in range(self.FLOOR_W):
                c = self.floor_color_a if (tx + ty) % 2 == 0 else self.floor_color_b
                pygame.draw.rect(surf, c,
                                 (ox + tx * TILE_SIZE, oy + ty * TILE_SIZE,
                                  TILE_SIZE, TILE_SIZE))
        # Floor shine effect if upgraded
        if self._floor_lvl >= 3:
            shine_alpha = int(8 + 4 * math.sin(self._anim_t * 1.5))
            for ty in range(0, self.FLOOR_H, 4):
                for tx in range(0, self.FLOOR_W, 4):
                    if (tx + ty) % 8 == 0:
                        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        s.fill((255, 255, 255, max(0, shine_alpha)))
                        surf.blit(s, (ox + tx * TILE_SIZE, oy + ty * TILE_SIZE))

    def _draw_walls(self, surf: pygame.Surface, ox: int, oy: int, w: int, h: int):
        thickness = TILE_SIZE

        # Top wall
        pygame.draw.rect(surf, self.wall_color, (ox, oy, w, thickness))
        pygame.draw.rect(surf, self.wall_top, (ox, oy, w, 3))

        # Left wall
        pygame.draw.rect(surf, self.wall_color, (ox, oy, thickness, h))

        # Right wall
        pygame.draw.rect(surf, self.wall_color, (ox + w - thickness, oy, thickness, h))

        # Bottom wall (with door gap)
        door_x = 14 * TILE_SIZE
        door_w = 4 * TILE_SIZE
        pygame.draw.rect(surf, self.wall_color, (ox, oy + h - thickness, door_x, thickness))
        pygame.draw.rect(surf, self.wall_color,
                         (ox + door_x + door_w, oy + h - thickness,
                          w - door_x - door_w, thickness))

    def _draw_decorations(self, surf: pygame.Surface, ox: int, oy: int):
        for dec in self.decorations:
            x = ox + dec["x"] * TILE_SIZE
            y = oy + dec["y"] * TILE_SIZE
            w = dec["w"] * TILE_SIZE
            h = dec["h"] * TILE_SIZE

            if dec["type"] == "table":
                pygame.draw.rect(surf, dec["color"], (x, y, w, h))
                pygame.draw.rect(surf, (90, 60, 30), (x, y, w, h), 1)
                # Plate
                pygame.draw.circle(surf, (220, 220, 220),
                                   (x + w // 2, y + h // 2), 5, 1)

            elif dec["type"] == "chair":
                pygame.draw.rect(surf, dec["color"], (x + 2, y + 2, w - 4, h - 4))

            elif dec["type"] == "plant":
                # Pot
                pygame.draw.rect(surf, (140, 90, 50),
                                 (x + 4, y + h - 8, w - 8, 8))
                # Leaves
                for _ in range(5):
                    lx = x + w // 2 + random.randint(-6, 6)
                    ly = y + random.randint(2, h - 10)
                    pygame.draw.circle(surf, dec["color"], (lx, ly), 4)

            elif dec["type"] == "door":
                pygame.draw.rect(surf, dec["color"], (x, y, w, h))
                pygame.draw.rect(surf, (70, 50, 30), (x, y, w, h), 2)
                # Welcome mat
                pygame.draw.rect(surf, (120, 100, 80),
                                 (x + 4, y + h, w - 8, 6))

            elif dec["type"] == "neon":
                self._draw_neon(surf, x, y, w, h, dec)

            elif dec["type"] == "ac_unit":
                self._draw_ac_unit(surf, x, y, w, h)

            elif dec["type"] == "wall_art":
                self._draw_wall_art(surf, x, y, w, h, dec["color"])

            elif dec["type"] == "speaker":
                self._draw_speaker(surf, x, y, w, h)

    def _draw_neon(self, surf, x, y, w, h, dec):
        """Draw a glowing neon sign on the wall."""
        r, g, b = dec["color"]
        # Pulsing glow
        pulse = 0.6 + 0.4 * math.sin(self._anim_t * 2.5 + x * 0.3)
        glow_r = min(255, int(r * pulse))
        glow_g = min(255, int(g * pulse))
        glow_b = min(255, int(b * pulse))

        # Outer glow (larger, faint)
        glow_surf = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
        glow_alpha = int(40 * pulse)
        glow_surf.fill((glow_r, glow_g, glow_b, max(0, glow_alpha)))
        surf.blit(glow_surf, (x - 4, y - 4))

        # Sign background
        pygame.draw.rect(surf, (20, 18, 28), (x, y, w, h))
        pygame.draw.rect(surf, (glow_r, glow_g, glow_b), (x, y, w, h), 2)

        # Text
        text = dec.get("text", "")
        if text:
            font = pygame.font.SysFont("Consolas", max(8, min(12, w // len(text))))
            txt_surf = font.render(text, True, (glow_r, glow_g, glow_b))
            surf.blit(txt_surf, txt_surf.get_rect(center=(x + w // 2, y + h // 2)))

    def _draw_ac_unit(self, surf, x, y, w, h):
        """Draw an AC unit on the wall with blowing particles."""
        # Unit body
        pygame.draw.rect(surf, (200, 220, 240), (x, y, w, h))
        pygame.draw.rect(surf, (160, 180, 200), (x, y, w, h), 1)
        # Grille lines
        for i in range(3):
            lx = x + 4 + i * (w // 4)
            pygame.draw.line(surf, (140, 160, 180),
                             (lx, y + 3), (lx, y + h - 3), 1)
        # Tiny LED
        led_pulse = int(200 + 55 * math.sin(self._anim_t * 3))
        pygame.draw.rect(surf, (0, min(255, led_pulse), 0),
                         (x + w - 5, y + 2, 3, 3))
        # Cold air particles
        for i in range(2):
            px = x + w // 2 + int(8 * math.sin(self._anim_t * 4 + i * 2))
            py_off = int((self._anim_t * 20 + i * 15) % 20)
            alpha = max(0, 60 - py_off * 3)
            if alpha > 0:
                ps = pygame.Surface((4, 2), pygame.SRCALPHA)
                ps.fill((180, 220, 255, alpha))
                surf.blit(ps, (px, y + h + py_off))

    def _draw_wall_art(self, surf, x, y, w, h, color):
        """Draw a framed painting on the wall."""
        # Frame
        pygame.draw.rect(surf, (160, 130, 80), (x - 1, y - 1, w + 2, h + 2))
        # Canvas
        pygame.draw.rect(surf, color, (x + 2, y + 2, w - 4, h - 4))
        # Random "art" — small colored rects
        r, g, b = color
        for i in range(3):
            ax = x + 4 + i * ((w - 8) // 3)
            ah = h - 8
            ac = (min(255, r + 40), min(255, g + 30), min(255, b + 20))
            pygame.draw.rect(surf, ac, (ax, y + 4, (w - 8) // 4, ah // 2))

    def _draw_speaker(self, surf, x, y, w, h):
        """Draw a small wall speaker."""
        pygame.draw.rect(surf, (60, 55, 70), (x, y, w, h))
        pygame.draw.rect(surf, (45, 40, 55), (x, y, w, h), 1)
        # Speaker cone
        cx = x + w // 2
        cy = y + h // 2
        pygame.draw.circle(surf, (80, 75, 90), (cx, cy), 4)
        pygame.draw.circle(surf, (50, 45, 60), (cx, cy), 2)
        # Sound wave arcs
        if self._music_lvl > 0:
            wave = int(2 * math.sin(self._anim_t * 6))
            pygame.draw.arc(surf, (150, 130, 200),
                            (cx + 3, cy - 4 + wave, 6, 8), -0.5, 0.5, 1)

    def _draw_music_particles(self, surf, ox, oy):
        """Draw floating music note particles."""
        font = pygame.font.SysFont("Consolas", 11)
        for p in self._music_particles:
            alpha = int(200 * (p["life"] / p["max_life"]))
            if alpha <= 0:
                continue
            note_surf = font.render(p["note"], True, p["color"])
            # Create alpha surface
            alpha_surf = pygame.Surface(note_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.blit(note_surf, (0, 0))
            alpha_surf.set_alpha(max(0, min(255, alpha)))
            surf.blit(alpha_surf, (ox + p["x"], oy + p["y"]))

    def _draw_attractiveness_badge(self, surf, area_rect):
        """Draw a small attractiveness star badge in the restaurant area."""
        score = self._attractiveness
        bx = area_rect.right - 80
        by = area_rect.y + 8
        bw, bh = 72, 24

        # Badge background
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        if score >= 80:
            bg.fill((255, 200, 50, 160))
        elif score >= 50:
            bg.fill((80, 200, 120, 140))
        else:
            bg.fill((60, 60, 80, 130))
        surf.blit(bg, (bx, by))
        pygame.draw.rect(surf, (255, 210, 80), (bx, by, bw, bh), 1, border_radius=3)

        star_ico = icons.get_scaled("star", 12)
        if score < 50:
            star_ico = star_ico.copy()
            star_ico.set_alpha(100)
        surf.blit(star_ico, (bx + 4, by + 6))
        font = pygame.font.SysFont("Consolas", 12, bold=True)
        txt = font.render(f"{score}%", True, (255, 255, 240))
        surf.blit(txt, (bx + 20, by + 6))
    def _draw_rating_badge(self, surf, area_rect):
        """Draw community rating badge below attractiveness badge."""
        bx = area_rect.right - 80
        by = area_rect.y + 38
        bw, bh = 72, 24

        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        if self._community_rating >= 4.0:
            bg.fill((50, 180, 255, 150))
        elif self._community_rating >= 2.5:
            bg.fill((100, 160, 100, 130))
        else:
            bg.fill((60, 60, 80, 120))
        surf.blit(bg, (bx, by))
        pygame.draw.rect(surf, (100, 180, 255), (bx, by, bw, bh), 1, border_radius=3)

        font = pygame.font.SysFont("Consolas", 11, bold=True)
        stars_full = int(round(self._community_rating))
        sx = bx + 3
        for si in range(5):
            s_ico = icons.get_scaled("star", 10)
            if si >= stars_full:
                s_ico = s_ico.copy()
                s_ico.set_alpha(60)
            surf.blit(s_ico, (sx + si * 12, by + 3))

        cnt_txt = font.render(f"({self._community_votes})", True, (200, 200, 220))
        surf.blit(cnt_txt, (bx + bw - cnt_txt.get_width() - 3, by + 12))

    def set_community_rating(self, rating: float, votes: int):
        """Update the displayed community rating."""
        self._community_rating = rating
        self._community_votes = votes
    # ── Serialization ─────────────────────────────────────────
    def to_dict(self) -> dict:
        sprites_data = []
        for ws in self.worker_sprites:
            sprites_data.append({
                "x": ws.x, "y": ws.y,
                "station_idx": ws.current_station_idx,
                "state": ws.state,
                "work_timer": ws.work_timer,
                "burgers_made": ws.burgers_made,
            })
        return {"worker_sprites": sprites_data}

    def from_dict(self, data: dict):
        sprites_data = data.get("worker_sprites", [])
        for i, sd in enumerate(sprites_data):
            if i < len(self.worker_sprites):
                ws = self.worker_sprites[i]
                ws.x = sd.get("x", ws.x)
                ws.y = sd.get("y", ws.y)
                ws.current_station_idx = sd.get("station_idx", 0)
                ws.state = sd.get("state", "idle")
                ws.work_timer = sd.get("work_timer", 0.0)
                ws.burgers_made = sd.get("burgers_made", 0)

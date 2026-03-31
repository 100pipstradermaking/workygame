"""
leaderboard.py — Leaderboard & voting system with online sync.
Stores top player scores and restaurant ratings in JSON files (local)
and syncs with online backend via GitHub repo.
Tracks: total_income, prestige_level, workers_count, burgers_made, votes.
"""

import json
import os
import time
import pygame
import math
from theme import (TEXT_GOLD as LB_HEADER, TEXT_WHITE as LB_TEXT,
                   TEXT_DIM as LB_DIM, ACCENT as LB_ACCENT,
                   GOLD as LB_GOLD, SILVER as LB_SILVER, BRONZE as LB_BRONZE,
                   BORDER as LB_BORDER, BG_CARD as LB_ROW_A,
                   STAR_ON as LB_STAR_ON, STAR_OFF as LB_STAR_OFF,
                   STAR_HOVER as LB_STAR_HOVER)
import icons
from online import (
    fetch_online_leaderboard, push_score_online,
    push_vote_online, fetch_online_votes, is_web,
    web_save, web_load,
)

LEADERBOARD_FILE = "worky_leaderboard.json"
VOTES_FILE = "worky_votes.json"
MAX_ENTRIES = 50


def _load_entries() -> list[dict]:
    if is_web():
        data = web_load("leaderboard")
        if data:
            return data.get("entries", [])
        return []
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entries", [])


def _save_entries(entries: list[dict]):
    if is_web():
        web_save("leaderboard", {"entries": entries})
        return
    tmp = LEADERBOARD_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f, indent=2)
    if os.path.exists(LEADERBOARD_FILE):
        os.replace(tmp, LEADERBOARD_FILE)
    else:
        os.rename(tmp, LEADERBOARD_FILE)


def submit_score(player, restaurant=None):
    """Add or update a player's score on the leaderboard."""
    burgers = 0
    if restaurant:
        for ws in restaurant.worker_sprites:
            burgers += ws.burgers_made

    entry = {
        "name": player.player_name or "Anonymous",
        "restaurant": player.restaurant_name or "Unnamed",
        "total_income": player.total_income,
        "coins": player.coins,
        "prestige": player.prestige_level,
        "workers": len(player.workers),
        "burgers": burgers,
        "score": _calc_score(player, burgers),
        "timestamp": time.time(),
    }

    entries = _load_entries()

    # Update existing entry for this player or add new
    found = False
    for i, e in enumerate(entries):
        if e["name"] == entry["name"] and e["restaurant"] == entry["restaurant"]:
            if entry["score"] > e["score"]:
                entries[i] = entry
            found = True
            break
    if not found:
        entries.append(entry)

    # Sort by score descending, keep top N
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_ENTRIES]

    _save_entries(entries)

    # Also push to online leaderboard (async-friendly, non-blocking)
    try:
        push_score_online(entry)
    except Exception:
        pass

    return entries


def get_leaderboard() -> list[dict]:
    # Merge local + online entries
    local_entries = _load_entries()
    online_entries = []
    try:
        online_entries = fetch_online_leaderboard()
    except Exception:
        pass

    # Merge: combine by (name, restaurant) key, prefer higher score
    merged = {}
    for e in local_entries + online_entries:
        key = (e.get("name", ""), e.get("restaurant", ""))
        if key not in merged or e.get("score", 0) > merged[key].get("score", 0):
            merged[key] = e
    entries = sorted(merged.values(), key=lambda e: e.get("score", 0), reverse=True)

    # Attach vote data
    votes = _load_votes()
    online_votes = {}
    try:
        online_votes = fetch_online_votes()
    except Exception:
        pass
    # Merge votes
    for k, v in online_votes.items():
        if k not in votes:
            votes[k] = v

    for e in entries:
        key = _vote_key(e["name"], e["restaurant"])
        vdata = votes.get(key, {})
        vote_list = vdata.get("votes", [])
        e["vote_count"] = len(vote_list)
        e["rating"] = sum(v["stars"] for v in vote_list) / len(vote_list) if vote_list else 0.0
    return entries


# ── Voting / Rating system ───────────────────────────────────

def _vote_key(name: str, restaurant: str) -> str:
    """Unique key for a restaurant in the votes file."""
    return f"{name}::{restaurant}"


def _load_votes() -> dict:
    if is_web():
        data = web_load("votes")
        return data if data else {}
    if not os.path.exists(VOTES_FILE):
        return {}
    with open(VOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_votes(votes: dict):
    if is_web():
        web_save("votes", votes)
        return
    tmp = VOTES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(votes, f, indent=2)
    if os.path.exists(VOTES_FILE):
        os.replace(tmp, VOTES_FILE)
    else:
        os.rename(tmp, VOTES_FILE)


def cast_vote(voter_name: str, target_name: str, target_restaurant: str,
              stars: int) -> bool:
    """Cast a 1-5 star vote for a restaurant. One vote per voter per restaurant.
    Returns True if vote was recorded/updated."""
    stars = max(1, min(5, stars))
    if voter_name == target_name:
        return False  # can't vote for yourself

    votes = _load_votes()
    key = _vote_key(target_name, target_restaurant)

    if key not in votes:
        votes[key] = {"name": target_name, "restaurant": target_restaurant, "votes": []}

    vote_list = votes[key]["votes"]
    # Update existing vote or add new
    for v in vote_list:
        if v["voter"] == voter_name:
            v["stars"] = stars
            v["time"] = time.time()
            _save_votes(votes)
            # Try online
            try:
                push_vote_online(voter_name, target_name, target_restaurant, stars)
            except Exception:
                pass
            return True

    vote_list.append({"voter": voter_name, "stars": stars, "time": time.time()})
    _save_votes(votes)
    try:
        push_vote_online(voter_name, target_name, target_restaurant, stars)
    except Exception:
        pass
    return True


def get_restaurant_rating(name: str, restaurant: str) -> tuple[float, int]:
    """Returns (average_rating, vote_count) for a restaurant."""
    votes = _load_votes()
    key = _vote_key(name, restaurant)
    vdata = votes.get(key, {})
    vote_list = vdata.get("votes", [])
    if not vote_list:
        return (0.0, 0)
    avg = sum(v["stars"] for v in vote_list) / len(vote_list)
    return (avg, len(vote_list))


def get_my_vote(voter_name: str, target_name: str, target_restaurant: str) -> int:
    """Returns the star count the voter gave (0 = no vote yet)."""
    votes = _load_votes()
    key = _vote_key(target_name, target_restaurant)
    vdata = votes.get(key, {})
    for v in vdata.get("votes", []):
        if v["voter"] == voter_name:
            return v["stars"]
    return 0


def _calc_score(player, burgers: int) -> float:
    """Score = total_income + prestige_bonus + burger_bonus."""
    return (player.total_income
            + player.prestige_level * 50_000
            + burgers * 100
            + len(player.workers) * 1000)


# ── Leaderboard Overlay UI ───────────────────────────────────

LB_BG = (0, 0, 0, 160)
LB_ROW_B = (248, 245, 240)
LB_HIGHLIGHT = (255, 250, 230)


class LeaderboardOverlay:
    """Full-screen overlay showing the leaderboard."""

    def __init__(self, screen_w: int, screen_h: int):
        self.sw = screen_w
        self.sh = screen_h
        self.visible = False
        self.scroll_y = 0
        self.max_scroll = 0
        self.anim_t = 0.0
        self._open_time = 0.0          # time since opened (for row slide-in)
        self._hover_row = -1           # row index mouse is hovering

        self.font_title = pygame.font.SysFont("Consolas", 28, bold=True)
        self.font_md = pygame.font.SysFont("Consolas", 16)
        self.font_sm = pygame.font.SysFont("Consolas", 13)
        self.font_rank = pygame.font.SysFont("Consolas", 20, bold=True)

        self.entries: list[dict] = []
        self.player_name = ""
        self.hover_star: tuple[int, int] | None = None  # (entry_idx, star 1-5)
        self.vote_flash: dict[int, float] = {}  # {entry_idx: timer}
        self._star_rects: list[list[pygame.Rect]] = []  # per entry, 5 star rects

    def toggle(self, player_name: str = ""):
        self.visible = not self.visible
        if self.visible:
            self.entries = get_leaderboard()
            self.player_name = player_name
            self.scroll_y = 0
            self._open_time = 0.0
            self._hover_row = -1

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if event was consumed."""
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_l):
            self.visible = False
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Close button
            close_rect = pygame.Rect(self.sw // 2 + 240, 52, 30, 30)
            if close_rect.collidepoint(event.pos):
                self.visible = False
                return True

            # Star voting clicks
            mx, my = event.pos
            for entry_idx, star_rects in enumerate(self._star_rects):
                for star_idx, sr in enumerate(star_rects):
                    if sr.collidepoint(mx, my):
                        entry = self.entries[entry_idx]
                        stars = star_idx + 1
                        if cast_vote(self.player_name, entry["name"],
                                     entry["restaurant"], stars):
                            self.vote_flash[entry_idx] = 1.0
                            # Refresh data
                            self.entries = get_leaderboard()
                        return True

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, min(self.max_scroll,
                                       self.scroll_y - event.y * 30))
            return True

        # Track star hover and row hover
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hover_star = None
            self._hover_row = -1
            # Row hover — check content area
            pw, ph = 540, 500
            px = (self.sw - pw) // 2
            py = 44
            content_y = py + 58 + 24
            row_h = 44
            if px < mx < px + pw and content_y < my < py + ph - 10:
                rel = my - content_y + self.scroll_y
                if rel >= 0:
                    self._hover_row = int(rel // row_h)
            for entry_idx, star_rects in enumerate(self._star_rects):
                for star_idx, sr in enumerate(star_rects):
                    if sr.collidepoint(mx, my):
                        self.hover_star = (entry_idx, star_idx + 1)
                        break

        return True  # consume all events while visible

    def update(self, dt: float):
        if self.visible:
            self.anim_t += dt
            self._open_time += dt
            # Decay vote flash timers
            for k in list(self.vote_flash):
                self.vote_flash[k] -= dt * 2
                if self.vote_flash[k] <= 0:
                    del self.vote_flash[k]

    def draw(self, surf: pygame.Surface):
        if not self.visible:
            return

        # Darkened background
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill(LB_BG)
        surf.blit(overlay, (0, 0))

        # Main panel
        pw, ph = 540, 500
        px = (self.sw - pw) // 2
        py = 44
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(surf, (255, 255, 255), panel, border_radius=10)
        pygame.draw.rect(surf, LB_ACCENT, panel, 2, border_radius=10)

        # Title with trophy icons
        title_txt = self.font_title.render("LEADERBOARD", True, LB_HEADER)
        tr = title_txt.get_rect(center=(self.sw // 2, py + 30))
        surf.blit(title_txt, tr)
        trophy_ico = icons.get_scaled("trophy", 20)
        surf.blit(trophy_ico, (tr.x - 26, tr.y))
        surf.blit(trophy_ico, (tr.right + 6, tr.y))

        # Close button
        close_rect = pygame.Rect(px + pw - 38, py + 8, 30, 30)
        mx, my = pygame.mouse.get_pos()
        cc = (180, 60, 60) if close_rect.collidepoint(mx, my) else (100, 60, 60)
        pygame.draw.rect(surf, cc, close_rect, border_radius=4)
        xt = self.font_md.render("X", True, (240, 240, 240))
        surf.blit(xt, xt.get_rect(center=close_rect.center))

        # Column headers
        header_y = py + 58
        headers = [("", px + 10, 30), ("Player", px + 45, 100),
                    ("Restaurant", px + 148, 90), ("Score", px + 260, 70),
                    ("Rating", px + 350, 75), ("Prstg", px + 445, 45),
                    ("Brg", px + 495, 40)]
        for label, hx, hw in headers:
            htxt = self.font_sm.render(label, True, LB_DIM)
            surf.blit(htxt, (hx + 4, header_y))
        pygame.draw.line(surf, LB_BORDER, (px + 8, header_y + 18),
                         (px + pw - 8, header_y + 18), 1)

        # Scrollable content area
        content_y = header_y + 24
        content_h = ph - (content_y - py) - 10
        content_rect = pygame.Rect(px, content_y, pw, content_h)
        prev_clip = surf.get_clip()
        surf.set_clip(content_rect)

        row_h = 44
        y = content_y - self.scroll_y
        self._star_rects.clear()

        for i, entry in enumerate(self.entries):
            rank = i + 1

            # Slide-in animation: each row delays by 0.05s
            row_age = self._open_time - i * 0.05
            if row_age < 0:
                y += row_h
                self._star_rects.append([])
                continue
            slide_offset = max(0, int(40 * (1.0 - min(1.0, row_age * 4))))
            row_alpha = min(255, int(255 * min(1.0, row_age * 4)))

            row_rect = pygame.Rect(px + 4 + slide_offset, y, pw - 8 - slide_offset, row_h - 2)

            # Highlight current player or hover
            is_me = entry["name"] == self.player_name
            if is_me:
                bg = LB_HIGHLIGHT
            elif i == self._hover_row:
                bg = (240, 238, 245)
            else:
                bg = LB_ROW_A if i % 2 == 0 else LB_ROW_B

            # Vote flash effect
            if i in self.vote_flash:
                flash_a = int(40 * self.vote_flash[i])
                bg = (min(255, bg[0] + flash_a),
                      min(255, bg[1] + flash_a + 10),
                      min(255, bg[2]))

            pygame.draw.rect(surf, bg, row_rect, border_radius=4)

            # Rank with medal colors
            if rank == 1:
                rank_col = LB_GOLD
            elif rank == 2:
                rank_col = LB_SILVER
            elif rank == 3:
                rank_col = LB_BRONZE
            else:
                rank_col = LB_DIM

            if rank <= 3:
                medal_name = ["medal_gold", "medal_silver", "medal_bronze"][rank - 1]
                medal_ico = icons.get(medal_name)
                surf.blit(medal_ico, (px + 12, y + 6))
            rank_txt = self.font_rank.render(f"#{rank}", True, rank_col)
            surf.blit(rank_txt, (px + 10 if rank > 3 else px + 30, y + 4))

            # Player name
            name_col = LB_ACCENT if is_me else LB_TEXT
            ntxt = self.font_md.render(entry["name"][:10], True, name_col)
            surf.blit(ntxt, (px + 48, y + 4))

            # Restaurant
            rtxt = self.font_sm.render(entry["restaurant"][:10], True, LB_DIM)
            surf.blit(rtxt, (px + 150, y + 6))

            # Score
            score_str = self._format_number(entry["score"])
            stxt = self.font_md.render(score_str, True, LB_HEADER)
            surf.blit(stxt, (px + 264, y + 4))

            # ── Rating stars ─────────────────────────────────
            rating = entry.get("rating", 0.0)
            vote_count = entry.get("vote_count", 0)
            my_vote = get_my_vote(self.player_name, entry["name"],
                                  entry["restaurant"]) if not is_me else 0
            star_x = px + 350
            star_y_pos = y + 4
            entry_stars = []

            for s in range(5):
                sx = star_x + s * 14
                sr = pygame.Rect(sx, star_y_pos, 13, 14)
                entry_stars.append(sr)

                # Determine star color
                if is_me:
                    # Can't vote for self — show others' rating
                    if s < int(round(rating)):
                        sc = LB_STAR_ON
                    else:
                        sc = LB_STAR_OFF
                else:
                    # Interactive: show hover preview or current vote
                    hover_preview = 0
                    if self.hover_star and self.hover_star[0] == i:
                        hover_preview = self.hover_star[1]

                    if hover_preview > 0:
                        if s < hover_preview:
                            sc = LB_STAR_HOVER
                        else:
                            sc = LB_STAR_OFF
                    elif my_vote > 0:
                        if s < my_vote:
                            sc = LB_STAR_ON
                        else:
                            sc = LB_STAR_OFF
                    elif s < int(round(rating)):
                        sc = (180, 160, 60)
                    else:
                        sc = LB_STAR_OFF

                star_chr = "★" if sc != LB_STAR_OFF else "☆"
                # Glow effect on vote flash
                if i in self.vote_flash and sc == LB_STAR_ON:
                    glow_r = int(10 * self.vote_flash[i])
                    glow_s = pygame.Surface((13 + glow_r*2, 14 + glow_r*2), pygame.SRCALPHA)
                    glow_a = int(80 * self.vote_flash[i])
                    pygame.draw.ellipse(glow_s, (255, 220, 60, glow_a),
                                        (0, 0, 13 + glow_r*2, 14 + glow_r*2))
                    surf.blit(glow_s, (sx - glow_r, star_y_pos - glow_r))
                st = self.font_sm.render(star_chr, True, sc)
                surf.blit(st, (sx, star_y_pos))

            self._star_rects.append(entry_stars)

            # Vote count and average below stars
            if vote_count > 0:
                info_txt = self.font_sm.render(
                    f"{rating:.1f} ({vote_count})", True, LB_DIM)
                surf.blit(info_txt, (star_x, star_y_pos + 16))
            elif not is_me:
                info_txt = self.font_sm.render("vote!", True, (80, 75, 100))
                surf.blit(info_txt, (star_x + 10, star_y_pos + 16))

            # Prestige with icon
            prs_ico = icons.get_scaled("prestige", 12)
            surf.blit(prs_ico, (px + 445, y + 8))
            ptxt = self.font_sm.render(f"Lv{entry['prestige']}", True, (180, 120, 255))
            surf.blit(ptxt, (px + 458, y + 6))

            # Burgers with icon
            brg_ico = icons.get_scaled("burger", 12)
            surf.blit(brg_ico, (px + 493, y + 8))
            btxt = self.font_sm.render(str(entry.get("burgers", 0)), True, (255, 160, 80))
            surf.blit(btxt, (px + 507, y + 6))

            y += row_h

        self.max_scroll = max(0, int(y + self.scroll_y - content_y - content_h))
        surf.set_clip(prev_clip)

        # Scrollbar
        if self.max_scroll > 0:
            sb_x = px + pw - 8
            sb_h = content_h
            thumb_h = max(20, int(sb_h * content_h / (content_h + self.max_scroll)))
            thumb_y = content_y + int((sb_h - thumb_h) * self.scroll_y / self.max_scroll)
            # Track
            track_s = pygame.Surface((4, sb_h), pygame.SRCALPHA)
            track_s.fill((255, 255, 255, 15))
            surf.blit(track_s, (sb_x, content_y))
            # Thumb
            thumb_s = pygame.Surface((4, thumb_h), pygame.SRCALPHA)
            thumb_s.fill((255, 210, 80, 100))
            surf.blit(thumb_s, (sb_x, thumb_y))

        # Footer
        footer_y = py + ph - 28
        count = len(self.entries)
        ft = self.font_sm.render(
            f"{count} player{'s' if count != 1 else ''}  |  Press L or ESC to close",
            True, LB_DIM)
        surf.blit(ft, ft.get_rect(center=(self.sw // 2, footer_y + 8)))

    @staticmethod
    def _format_number(n: float) -> str:
        if n >= 1_000_000_000:
            return f"{n / 1_000_000_000:.1f}B"
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return f"{n:,.0f}"

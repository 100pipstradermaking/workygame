"""
main.py — Entry point for WORKY: Burger Economy Simulator.
Initializes Pygame, runs the game loop, and ties all systems together.

Flow: Start Menu → Registration (new game) or Load (continue) → Game Loop.
      Game Loop → Exit to Menu saves and returns to main menu.

Run:
    python main.py
"""

import sys
import asyncio
import pygame

from player import Player
from worker import Worker
from economy import Economy
from upgrades import (
    get_speed_multiplier, get_efficiency_multiplier,
    get_income_multiplier, get_event_interval_reduction,
)
from ui import UI, SCREEN_W, SCREEN_H, PANEL_W, REST_W, REST_H, BAR_H
from restaurant import Restaurant
from save_system import SaveSystem
from menu import StartMenu, MenuState
from shop import ShopUI, get_total_shop_multiplier, get_seat_count
from leaderboard import LeaderboardOverlay, submit_score, get_restaurant_rating

FPS = 60


def init_new_player(player: Player, reg_data: dict):
    """Set up a brand-new player from registration data."""
    player.player_name = reg_data["player_name"]
    player.restaurant_name = reg_data["restaurant_name"]
    player.coins = 50.0
    # Give one free common worker
    starter = Worker(rarity="common")
    player.workers.append(starter)


async def run_menu(screen, clock, save_sys):
    """Run the start menu. Returns ('new', reg_data) or ('continue', None) or exits."""
    menu = StartMenu(screen)

    while True:
        dt = clock.tick(FPS) / 1000.0
        menu.update(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            result = menu.handle_event(event)
            if result == "start_game":
                return ("new", menu.reg_data)
            elif result == "continue_game":
                return ("continue", None)
            elif result == "quit":
                pygame.quit()
                sys.exit()

        menu.draw()
        pygame.display.flip()
        await asyncio.sleep(0)


async def run_game(screen, clock, mode, reg_data, save_sys):
    """Run the main game loop. Returns 'menu' to go back to main menu."""
    player = Player()
    economy = Economy()
    restaurant = Restaurant()
    ui = UI(screen)
    shop_ui = ShopUI(SCREEN_W - PANEL_W, PANEL_W, SCREEN_H)
    leaderboard = LeaderboardOverlay(SCREEN_W, SCREEN_H)

    if mode == "new" and reg_data:
        init_new_player(player, reg_data)
    else:
        save_sys.load(player, economy, Worker.from_dict, restaurant)

    restaurant.sync_workers(player.workers)

    show_shop = True  # start with shop visible on right panel
    rating_timer = 0.0  # throttle rating file reads

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── Events ───────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_sys.save(player, economy, restaurant)
                submit_score(player, restaurant)
                pygame.quit()
                sys.exit()

            # Leaderboard overlay consumes events when visible
            if leaderboard.handle_event(event):
                continue

            # Bottom bar buttons
            bar_action = ui.handle_bar_event(event)
            if bar_action == "exit_to_menu":
                save_sys.save(player, economy, restaurant)
                submit_score(player, restaurant)
                return "menu"
            elif bar_action == "toggle_leaderboard":
                submit_score(player, restaurant)
                leaderboard.toggle(player.player_name)
                continue
            elif bar_action == "toggle_shop":
                show_shop = not show_shop
                continue

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    show_shop = not show_shop
                    continue
                elif event.key == pygame.K_l:
                    submit_score(player, restaurant)
                    leaderboard.toggle(player.player_name)
                    continue
                elif event.key == pygame.K_ESCAPE:
                    save_sys.save(player, economy, restaurant)
                    submit_score(player, restaurant)
                    return "menu"

            # Shop panel events
            if show_shop:
                action = shop_ui.handle_event(event, player)
                if action == "hired":
                    restaurant.sync_workers(player.workers)
                # Prestige via shop
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, atype, aid in shop_ui._buttons:
                        if rect.collidepoint(event.pos) and aid == "__prestige__":
                            if player.prestige():
                                restaurant.sync_workers(player.workers)
                            break

        # ── Apply upgrade effects to economy settings ────────
        economy.event_check_interval = max(1.0, 5.0 - get_event_interval_reduction(player))

        spd = get_speed_multiplier(player)
        eff = get_efficiency_multiplier(player)
        inc = get_income_multiplier(player)
        shop_mult = get_total_shop_multiplier(player)
        seats = get_seat_count(player)

        # Temporarily boost worker output
        original_multiplier = player.prestige_multiplier
        player.prestige_multiplier = original_multiplier * spd * eff * inc * shop_mult

        # ── Economy tick ─────────────────────────────────────
        economy.update(player, dt, seats=seats)

        # Restore original multiplier
        player.prestige_multiplier = original_multiplier

        # ── Restaurant tick ──────────────────────────────────
        restaurant.sync_workers(player.workers)
        restaurant.apply_customization(player)
        # Update community rating (throttled to every 5s)
        rating_timer -= dt
        if rating_timer <= 0:
            r_avg, r_cnt = get_restaurant_rating(player.player_name,
                                                  player.restaurant_name)
            restaurant.set_community_rating(r_avg, r_cnt)
            rating_timer = 5.0
        restaurant.update(dt)

        # ── UI update ────────────────────────────────────────
        ui.update(dt)
        shop_ui.update(dt)
        leaderboard.update(dt)

        effective_ips = player.get_income_per_second() * spd * eff * inc * shop_mult

        # ── Render ───────────────────────────────────────────
        screen.fill((22, 20, 32))

        # Restaurant area (top-left, 640 × 480)
        world_area = pygame.Rect(0, 0, REST_W, REST_H)
        restaurant.draw(screen, world_area)

        # Event popup inside restaurant area
        ui.draw_event(economy)

        # Bottom info bar (below restaurant, 640 × 240)
        ui.draw_bottom_bar(player, economy, effective_ips, show_shop)

        # Right panel: shop (full height 720)
        if show_shop:
            shop_ui.draw(screen, player)
        else:
            # Draw empty panel background
            panel_rect = pygame.Rect(SCREEN_W - PANEL_W, 0, PANEL_W, SCREEN_H)
            pygame.draw.rect(screen, (28, 26, 40), panel_rect)
            pygame.draw.line(screen, (75, 70, 100),
                             (SCREEN_W - PANEL_W, 0),
                             (SCREEN_W - PANEL_W, SCREEN_H), 2)
            # Show a hint
            fnt = pygame.font.SysFont("Consolas", 16)
            hint = fnt.render("Press S for Shop", True, (100, 100, 120))
            screen.blit(hint, hint.get_rect(
                center=(SCREEN_W - PANEL_W // 2, SCREEN_H // 2)))

        # Leaderboard overlay (on top of everything)
        leaderboard.draw(screen)

        pygame.display.flip()
        await asyncio.sleep(0)

        # ── Auto-save ────────────────────────────────────────
        if save_sys.should_auto_save():
            save_sys.save(player, economy, restaurant)
            submit_score(player, restaurant)

    return "menu"


async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("WORKY — Burger Economy Simulator")
    clock = pygame.time.Clock()
    save_sys = SaveSystem()

    # Main loop: menu ↔ game
    while True:
        mode, reg_data = await run_menu(screen, clock, save_sys)
        result = await run_game(screen, clock, mode, reg_data, save_sys)
        if result != "menu":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())

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
from restaurant import Restaurant
from save_system import SaveSystem
from menu import StartMenu, MenuState
from shop import get_total_shop_multiplier, get_seat_count
from leaderboard import LeaderboardOverlay, submit_score, get_restaurant_rating
from economy import get_guild_income_bonus
from loading import LoadingScreen
from game_screen import GameScreen, SCREEN_W, SCREEN_H

FPS = 60


async def run_loading(screen, clock):
    """Run the animated loading/splash screen. Returns when user clicks."""
    loader = LoadingScreen(screen)
    while not loader.finished:
        dt = clock.tick(FPS) / 1000.0
        loader.update(dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            loader.handle_event(event)
        loader.draw()
        pygame.display.flip()
        await asyncio.sleep(0)


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
    game_ui = GameScreen(screen)
    leaderboard = LeaderboardOverlay(SCREEN_W, SCREEN_H)

    if mode == "new" and reg_data:
        init_new_player(player, reg_data)
    else:
        save_sys.load(player, economy, Worker.from_dict, restaurant)

    restaurant.sync_workers(player.workers)

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

            # Game screen events (top bar, bottom nav, content)
            action = game_ui.handle_event(event, player)
            if action == "exit_to_menu":
                save_sys.save(player, economy, restaurant)
                submit_score(player, restaurant)
                return "menu"
            elif action == "toggle_leaderboard":
                submit_score(player, restaurant)
                leaderboard.toggle(player.player_name)
                continue
            elif action in ("hired", "prestige", "season_claimed"):
                restaurant.sync_workers(player.workers)

        # ── Apply upgrade effects to economy settings ────────
        economy.event_check_interval = max(1.0, 5.0 - get_event_interval_reduction(player))

        spd = get_speed_multiplier(player)
        eff = get_efficiency_multiplier(player)
        inc = get_income_multiplier(player)
        shop_mult = get_total_shop_multiplier(player)
        guild_mult = get_guild_income_bonus(player)
        seats = get_seat_count(player)

        # Temporarily boost worker output
        original_multiplier = player.prestige_multiplier
        player.prestige_multiplier = original_multiplier * spd * eff * inc * shop_mult * guild_mult

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
        game_ui.update(dt)
        leaderboard.update(dt)

        effective_ips = player.get_income_per_second() * spd * eff * inc * shop_mult * guild_mult

        # ── Render ───────────────────────────────────────────
        game_ui.draw(player, economy, effective_ips, restaurant)

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
    pygame.display.set_caption("WORKY — Burgers Farm")
    clock = pygame.time.Clock()
    save_sys = SaveSystem()

    # Loading / splash screen
    await run_loading(screen, clock)

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

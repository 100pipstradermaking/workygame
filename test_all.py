"""Quick end-to-end test for all recent changes."""
import traceback, sys, os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

try:
    import pygame; pygame.init()
    s = pygame.display.set_mode((960, 720))

    # Test 1: Prestige keeps one worker
    from player import Player
    from worker import Worker
    p = Player()
    p.total_income = 2_000_000
    p.coins = 5000
    for _ in range(5):
        p.workers.append(Worker(rarity='common'))
    assert len(p.workers) == 5
    result = p.prestige()
    assert result is True
    assert len(p.workers) == 1, f'Expected 1 worker, got {len(p.workers)}'
    assert p.workers[0].rarity == 'common'
    assert p.coins == 0.0
    assert p.prestige_level == 1
    print('PRESTIGE TEST OK: 1 worker kept')

    # Test 2: Menu with icons
    from menu import StartMenu
    m = StartMenu(s)
    for i in range(5):
        m.update(1/60)
    m.draw()
    print('MENU DRAW OK')

    # Test 3: Shop names clean (no emoji)
    from shop import ShopUI, KITCHEN_ITEMS, DESIGN_ITEMS, BUSINESS_ITEMS
    for item in KITCHEN_ITEMS + DESIGN_ITEMS + BUSINESS_ITEMS:
        for c in item['name']:
            assert ord(c) < 128, f"Emoji found in: {item['name']}"
    print('SHOP NAMES CLEAN')

    p2 = Player()
    p2.player_name = 'T'
    p2.restaurant_name = 'TR'
    sh = ShopUI(640, 320, 720)
    sh.update(1/60)
    sh.draw(s, p2)
    print('SHOP DRAW OK')

    # Test 4: UI bottom bar with pixel star icons
    from economy import Economy
    from ui import UI
    e = Economy()
    ui = UI(s)
    ui.update(1/60)
    ui.draw_bottom_bar(p2, e, 5.0, True)
    print('UI BOTTOM BAR OK')

    # Test 5: Event popup with star icons
    e.last_event_name = 'RUSH HOUR'
    e.last_event_color = (255, 200, 60)
    e.event_display_timer = 3.0
    ui.draw_event(e)
    print('EVENT POPUP OK')

    # Test 6: Restaurant badges with star icons
    from restaurant import Restaurant
    r = Restaurant()
    r.sync_workers(p2.workers)
    r.apply_customization(p2)
    r._attractiveness = 75
    r._community_rating = 4.2
    r._community_votes = 5
    r.update(1/60)
    r.draw(s, pygame.Rect(0, 0, 640, 480))
    print('RESTAURANT BADGES OK')

    # Test 7: Leaderboard overlay
    from leaderboard import LeaderboardOverlay
    lb = LeaderboardOverlay(960, 720)
    lb.toggle('T')
    lb.update(1/60)
    lb.draw(s)
    print('LEADERBOARD OK')

    print('ALL TESTS PASSED')
    pygame.quit()
except Exception as ex:
    traceback.print_exc()
    sys.exit(1)

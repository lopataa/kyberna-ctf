import time
from playwright.sync_api import sync_playwright

from . import network


def run_game(player_id: str) -> None:
    """Run an interactive game session."""
    maps = network.get_maps(player_id)
    print("\nAvailable Maps:")
    for idx, name in enumerate(maps, start=1):
        print(f"{idx}. {name}")

    choice = int(input("Choose a map by number: "))
    if choice < 1 or choice > len(maps):
        raise ValueError("Invalid map selection.")
    selected_map = maps[choice - 1]
    print(f"Selected map: {selected_map}")

    session_id, team_color = network.create_session(player_id, selected_map)
    print(f"Session ID: {session_id}, Team Color: {team_color}")

    session_url = f"https://ctf.kyberna.cz/Session/{session_id}"
    print("Launching browser to display game board...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, channel="chrome")
        page = browser.new_page()
        page.goto(session_url)
        print("Waiting for the game to start...")
        last_state = None
        while True:
            player_state = network.get_state(player_id, session_id)

            if player_state != last_state:
                if player_state != "Waiting":
                    print(f"State changed to: {player_state}")
                page.reload()
                last_state = player_state

            if player_state == "GameOver":
                print("Game over! The session has ended.")
                break

            if player_state == "Ready":
                direction = None
                while direction not in {"1", "2", "3", "4", "5", "6"}:
                    direction = input("Your turn! Enter move direction (1-6): ").strip()
                network.send_move(player_id, session_id, int(direction))
                print("Move sent. Waiting for opponent...")
            else:
                time.sleep(0.25)

        browser.close()


import time
from playwright.sync_api import sync_playwright

from . import network
import requests
from .ai import AIBase
from .models import ALL_MODELS

# Polling interval while waiting for the opponent or game to start.
POLL_INTERVAL = 0.1


def _select_map(player_id: str) -> str:
    maps = network.get_maps(player_id)
    print("\nAvailable Maps:")
    for idx, name in enumerate(maps, start=1):
        print(f"{idx}. {name}")

    choice = int(input("Choose a map by number: "))
    if choice < 1 or choice > len(maps):
        raise ValueError("Invalid map selection.")
    selected_map = maps[choice - 1]
    print(f"Selected map: {selected_map}")
    return selected_map


def _select_ai() -> type[AIBase]:
    names = list(ALL_MODELS.keys())
    print("\nAvailable AI models:")
    for idx, name in enumerate(names, start=1):
        print(f"{idx}. {name}")
    choice = int(input("Choose an AI model by number: "))
    if choice < 1 or choice > len(names):
        raise ValueError("Invalid AI selection.")
    print(f"Selected AI: {names[choice - 1]}")
    return ALL_MODELS[names[choice - 1]]


def _play_session(player_id: str, session_id: str, team_color: str, ai: AIBase | None = None) -> None:
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
                score = network.get_score(player_id, session_id)
                if isinstance(score, dict) and "Red" in score and "Blue" in score:
                    red = score.get("Red", 0)
                    blue = score.get("Blue", 0)
                    print(f"Final score - Red: {red}, Blue: {blue}")
                    my = red if team_color == "Red" else blue
                    opp = blue if team_color == "Red" else red
                    ratio = my / opp if opp != 0 else float("inf")
                    print(f"Score ratio ({team_color}/opponent): {ratio}")
                else:
                    print(f"Final score: {score}")
                break

            if player_state == "Ready":
                if ai is None:
                    direction = None
                    while direction not in {"1", "2", "3", "4", "5", "6"}:
                        direction = input("Your turn! Enter move direction (1-6): ").strip()
                else:
                    game_map = network.get_map(player_id, session_id)
                    entities = network.get_entities(player_id, session_id)
                    start = time.perf_counter()
                    direction = str(ai.choose_move(game_map, entities))
                    duration = time.perf_counter() - start
                    print(f"AI chose direction {direction} in {duration:.2f}s")
                try:
                    network.send_move(player_id, session_id, int(direction))
                except requests.RequestException as exc:
                    print(f"Failed to send move: {exc}")
                else:
                    print("Move sent. Waiting for opponent...")
            else:
                # Sleep only briefly while waiting for the opponent so the UI
                # remains responsive.
                time.sleep(POLL_INTERVAL)

        browser.close()


def run_game(player_id: str) -> None:
    """Run a game session, either manually or with AI."""
    mode = ""
    while mode not in {"m", "a"}:
        mode = input("Play manually or use AI? [m/a]: ").strip().lower()

    map_name = _select_map(player_id)
    if mode == "a":
        ai_cls = _select_ai()
        session_id, team_color = network.create_session(player_id, map_name, session_type="Ai")
        ai = ai_cls(team_color=team_color)
    else:
        ai = None
        session_id, team_color = network.create_session(player_id, map_name, session_type="Manual")
    print(f"Session ID: {session_id}, Team Color: {team_color}")
    _play_session(player_id, session_id, team_color, ai)

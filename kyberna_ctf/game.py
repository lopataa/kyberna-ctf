import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

from . import network
import requests
from .ai import AIBase
from .models import ALL_MODELS

# Polling interval while waiting for the opponent or game to start.
POLL_INTERVAL = 0.1

# File used to persist game results
SCORE_LOG_FILE = Path("scores.log")


def _log_score(map_name: str, team_color: str, score) -> None:
    """Append the map and scores to the score log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SCORE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SCORE_LOG_FILE.open("a", encoding="utf-8") as f:
        if isinstance(score, dict) and "Red" in score and "Blue" in score:
            red = score.get("Red", 0)
            blue = score.get("Blue", 0)
            f.write(
                f"{timestamp} | Map: {map_name} | Team: {team_color} | "
                f"Red: {red}, Blue: {blue}\n"
            )
        else:
            f.write(
                f"{timestamp} | Map: {map_name} | Team: {team_color} | "
                f"Score: {score}\n"
            )


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


def _play_session(
    player_id: str,
    session_id: str,
    team_color: str,
    map_name: str,
    ai: AIBase | None = None,
) -> None:
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

                _log_score(map_name, team_color, score)
                break

            if player_state == "Ready":
                if ai is None:
                    direction = None
                    while direction not in {"1", "2", "3", "4", "5", "6"}:
                        direction = input("Your turn! Enter move direction (1-6): ").strip()
                else:
                    game_map = network.get_map(player_id, session_id)
                    entities = network.get_entities(player_id, session_id)
                    score = network.get_score(player_id, session_id)
                    start = time.perf_counter()
                    direction = str(ai.choose_move(game_map, entities, score))
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


def run_game(player_id: str, ai_name: str | None = None, map_name: str | None = None) -> None:
    """Run a game session, either manually or with a specific AI."""

    if ai_name is None:
        mode = ""
        while mode not in {"m", "a"}:
            mode = input("Play manually or use AI? [m/a]: ").strip().lower()
    else:
        mode = "a"

    if map_name is None:
        map_name = _select_map(player_id)

    if mode == "a":
        if ai_name is None:
            ai_cls = _select_ai()
        else:
            try:
                ai_cls = ALL_MODELS[ai_name]
            except KeyError as exc:
                raise ValueError(f"Unknown AI model: {ai_name}") from exc
        session_id, team_color = network.create_session(player_id, map_name, session_type="Ai")
        ai = ai_cls(team_color=team_color)
    else:
        ai = None
        session_id, team_color = network.create_session(player_id, map_name, session_type="Manual")

    print(f"Session ID: {session_id}, Team Color: {team_color}")
    _play_session(player_id, session_id, team_color, map_name, ai)


def run_games(player_id: str, ai_names: list[str], map_name: str | None = None) -> None:
    """Run multiple AI sessions concurrently."""
    if map_name is None:
        map_name = _select_map(player_id)

    threads: list[Thread] = []
    for name in ai_names:
        t = Thread(target=run_game, args=(player_id, name, map_name))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

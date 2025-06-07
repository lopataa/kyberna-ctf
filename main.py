import requests
import time
from playwright.sync_api import sync_playwright

# Player ID (could be prompted or configured)
#PLAYER_ID = input("Enter your player ID: ").strip()
PLAYER_ID = "GVURzsZvyRParQx"

# 1. Fetch all available maps from the server
maps_response = requests.post(
    "https://ctf.kyberna.cz/Game/AllMaps",
    json={"playerId": PLAYER_ID}
)
print(maps_response.status_code)
maps = maps_response.json()  # Expecting a list of map names:contentReference[oaicite:29]{index=29}
print("\nAvailable Maps:")
for idx, map_name in enumerate(maps, start=1):
    print(f"{idx}. {map_name}")

# Let user choose a map by number
choice = int(input("Choose a map by number: "))
if choice < 1 or choice > len(maps):
    raise ValueError("Invalid map selection.")
selected_map = maps[choice - 1]
print(f"Selected map: {selected_map}")


# 2. Create a manual game session on the chosen map
session_response = requests.post(
    "https://ctf.kyberna.cz/Game/CreateSession",
    json={
        "playerId": PLAYER_ID,
        "mapName": selected_map,
        "type": "Manual"   # Manual game session (human player):contentReference[oaicite:32]{index=32}
    }
)
session_data = session_response.json()
session_id = session_data["sessionId"]
team_color = session_data["teamsColor"]
print(f"Session ID: {session_id}, Team Color: {team_color}")

# Open the session board in a Chrome browser using Playwright
session_url = f"https://ctf.kyberna.cz/Session/{session_id}"
print("Launching browser to display game board...")
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, channel="chrome")  # use Chrome
    page = browser.new_page()
    page.goto(session_url)
    # (We will refresh this page on each state change in the loop below)

    # 3. Poll game state and play until GameOver
    print("Waiting for the game to start...")
    last_state = None  # track last seen state for refresh logic

    while True:
        # Poll the current game state from the server
        state_response = requests.post(
            "https://ctf.kyberna.cz/Game/State",
            json={"playerId": PLAYER_ID, "sessionId": session_id}
        )
        # The state is a simple string: "Waiting", "Ready", or "GameOver":contentReference[oaicite:38]{index=38}
        try:
            player_state = state_response.json()
        except ValueError:
            player_state = state_response.text.strip()
        # (Use .text as fallback in case response is not a JSON structure but raw text)

        # Refresh the board view if the state changed
        if player_state != last_state:
            if player_state != "Waiting":
                print(f"State changed to: {player_state}")
            page.reload()  # update the browser view on each state change
            last_state = player_state

        # Check for game-over condition
        if player_state == "GameOver":
            print("Game over! The session has ended.")
            break

        # If it's the user's turn, prompt for a move
        if player_state == "Ready":
            # It's our turn to move:contentReference[oaicite:39]{index=39}
            direction = None
            while direction not in {"1", "2", "3", "4", "5", "6"}:
                direction = input("Your turn! Enter move direction (1-6): ").strip()
            # 4. Send the move to the server
            move_resp = requests.post(
                "https://ctf.kyberna.cz/Game/Move",
                json={
                    "playerId": PLAYER_ID,
                    "sessionId": session_id,
                    "direction": int(direction)
                }
            )
            # Optionally, check move_resp.status_code or .json() for success (True/False)
            # Immediately continue loop to await the opponent's move
            print("Move sent. Waiting for opponent...")
            # After our move, the state will likely switch to "Waiting" until opponent moves
            # We'll pick it up in the next iteration of the loop.

        # If not Ready and not GameOver, state must be "Waiting" – not our turn yet
        else:
            # Wait a short interval before polling again to avoid spamming the server
            time.sleep(0.25)
    # end while loop

    # 5. Clean up: close browser after game ends
    browser.close()

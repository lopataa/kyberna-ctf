import requests

BASE_URL = "https://ctf.kyberna.cz"


def get_maps(player_id: str):
    """Return a list of available map names."""
    resp = requests.post(f"{BASE_URL}/Game/AllMaps", json={"playerId": player_id})
    resp.raise_for_status()
    return resp.json()


def create_session(player_id: str, map_name: str, session_type: str = "Manual"):
    """Create a game session and return its id and team color."""
    resp = requests.post(
        f"{BASE_URL}/Game/CreateSession",
        json={"playerId": player_id, "mapName": map_name, "type": session_type},
    )
    resp.raise_for_status()
    data = resp.json()
    return data["sessionId"], data["teamsColor"]


def get_state(player_id: str, session_id: str):
    """Fetch the current state of the game."""
    resp = requests.post(
        f"{BASE_URL}/Game/State",
        json={"playerId": player_id, "sessionId": session_id},
    )
    try:
        return resp.json()
    except ValueError:
        return resp.text.strip()


def send_move(player_id: str, session_id: str, direction: int):
    """Send a move to the server."""
    resp = requests.post(
        f"{BASE_URL}/Game/Move",
        json={"playerId": player_id, "sessionId": session_id, "direction": direction},
    )
    resp.raise_for_status()
    return resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else resp.text


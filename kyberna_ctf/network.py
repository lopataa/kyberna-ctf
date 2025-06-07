"""HTTP helpers for interacting with the CTF server."""

import requests

BASE_URL = "https://ctf.kyberna.cz"

# Reuse a single session so that HTTP connections are kept alive.  This
# eliminates the overhead of creating a new TCP/TLS connection for every
# request which noticeably improves responsiveness when the AI is polling the
# server in a tight loop.
_SESSION = requests.Session()


def _post(endpoint: str, payload: dict):
    """Send a POST request using the shared session."""
    resp = _SESSION.post(f"{BASE_URL}{endpoint}", json=payload, timeout=10)
    resp.raise_for_status()
    return resp


def get_maps(player_id: str):
    """Return a list of available map names."""
    resp = _post("/Game/AllMaps", {"playerId": player_id})
    return resp.json()


def create_session(player_id: str, map_name: str, session_type: str = "Manual"):
    """Create a game session and return its id and team color."""
    resp = _post(
        "/Game/CreateSession",
        {"playerId": player_id, "mapName": map_name, "type": session_type},
    )
    data = resp.json()
    return data["sessionId"], data["teamsColor"]


def get_state(player_id: str, session_id: str):
    """Fetch the current state of the game."""
    resp = _post("/Game/State", {"playerId": player_id, "sessionId": session_id})
    try:
        return resp.json()
    except ValueError:
        return resp.text.strip()


def send_move(player_id: str, session_id: str, direction: int):
    """Send a move to the server."""
    resp = _post(
        "/Game/Move",
        {"playerId": player_id, "sessionId": session_id, "direction": direction},
    )
    return resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else resp.text


def get_map(player_id: str, session_id: str):
    """Retrieve the current game map."""
    resp = _post("/Game/Map", {"playerId": player_id, "sessionId": session_id})
    return resp.json()


def get_entities(player_id: str, session_id: str):
    """Retrieve all entities in the current session."""
    resp = _post("/Game/Entities", {"playerId": player_id, "sessionId": session_id})
    return resp.json()

import argparse
from kyberna_ctf.game import run_game, run_games
from kyberna_ctf.models import ALL_MODELS

# Player ID (could be prompted or configured)
PLAYER_ID = "GVURzsZvyRParQx"
# PLAYER_ID = input("Enter your player ID: ").strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Kyberna CTF AI")
    parser.add_argument(
        "--ais",
        help="Comma separated list of AI models to run concurrently",
    )
    parser.add_argument("--map", dest="map_name", help="Map name to play")
    args = parser.parse_args()

    if args.ais:
        ai_names = [n.strip() for n in args.ais.split(",") if n.strip()]
        for name in ai_names:
            if name not in ALL_MODELS:
                raise SystemExit(f"Unknown AI model: {name}")
        run_games(PLAYER_ID, ai_names, args.map_name)
    else:
        run_game(PLAYER_ID)


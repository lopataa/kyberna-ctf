class AIBase:
    """Interface for AI algorithms deciding on the next move."""

    def __init__(self, team_color: str | None = None):
        self.team_color = team_color

    def choose_move(self, game_map: dict, entities: list, score: dict | None = None) -> int:
        """Return the move direction (1-6) based on map, entities and score."""
        raise NotImplementedError

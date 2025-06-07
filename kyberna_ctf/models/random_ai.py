from ..ai import AIBase
import random


class RandomAI(AIBase):
    """A trivial AI that chooses a random valid direction."""

    def __init__(self, team_color: str | None = None):
        super().__init__(team_color)

    def choose_move(self, game_map: dict, entities: list) -> int:
        return random.randint(1, 6)

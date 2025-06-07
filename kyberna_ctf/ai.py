import random


class AIBase:
    """Interface for AI algorithms deciding on the next move."""

    def choose_move(self, game_map: dict, entities: list) -> int:
        """Return the move direction (1-6) based on map and entities."""
        raise NotImplementedError


class RandomAI(AIBase):
    """A trivial AI that chooses a random valid direction."""

    def choose_move(self, game_map: dict, entities: list) -> int:
        return random.randint(1, 6)

from collections import deque
from ..ai import AIBase

# Direction mapping for a hexagonal grid using axial coordinates
# 1: up, 2: top-right, 3: bottom-right, 4: down, 5: bottom-left, 6: top-left
DIRS = {
    1: (0, -1),
    2: (1, -1),
    3: (1, 0),
    4: (0, 1),
    5: (-1, 1),
    6: (-1, 0),
}


class ShortestPathAI(AIBase):
    """Move to the nearest flag, return it to base, repeat."""

    def __init__(self, team_color: str | None = None):
        self.team_color = team_color
        self._path: list[int] = []

    def _is_wall(self, game_map: dict, x: int, y: int) -> bool:
        w = game_map["width"]
        cells = game_map["cells"]
        return cells[y * w + x]["type"] == "Wall"

    def _shortest_path(self, game_map: dict, start: tuple[int, int], goal: tuple[int, int]) -> list[int] | None:
        w, h = game_map["width"], game_map["height"]
        queue = deque([(start, [])])
        visited = {start}
        while queue:
            (x, y), path = queue.popleft()
            if (x, y) == goal:
                return path
            for direction, (dx, dy) in DIRS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and not self._is_wall(game_map, nx, ny):
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [direction]))
        return None

    def _select_targets(self, entities: list[dict]):
        player = None
        base = None
        flags = []
        for e in entities:
            if e["type"] == "Player" and e["teamColor"] == self.team_color:
                player = (e["location"]["x"], e["location"]["y"])
            elif e["type"] == "Base" and e["teamColor"] == self.team_color:
                base = (e["location"]["x"], e["location"]["y"])
            elif e["type"] == "Flag" and e["teamColor"] != self.team_color:
                flags.append((e["location"]["x"], e["location"]["y"]))
        return player, base, flags

    def choose_move(self, game_map: dict, entities: list, score: dict | None = None) -> int:
        if not self._path:
            player, base, flags = self._select_targets(entities)
            if player is None or base is None or not flags:
                return 1

            best_path = None
            for flag in flags:
                path1 = self._shortest_path(game_map, player, flag)
                path2 = self._shortest_path(game_map, flag, base)
                if path1 and path2:
                    path = path1 + path2
                    if best_path is None or len(path) < len(best_path):
                        best_path = path
            if best_path:
                self._path = best_path
            else:
                return 1
        return self._path.pop(0)

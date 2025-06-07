from heapq import heappush, heappop
from typing import Dict, List, Tuple, Optional

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


def _offset_to_axial(x: int, y: int) -> Tuple[int, int]:
    """Convert odd-q offset coordinates to axial coordinates."""
    q = x
    r = y - (x - (x & 1)) // 2
    return q, r


def _axial_to_offset(q: int, r: int) -> Tuple[int, int]:
    """Convert axial coordinates back to odd-q offset."""
    x = q
    y = r + (q - (q & 1)) // 2
    return x, y


class DijkstraAI(AIBase):
    """Pathfinding AI using Dijkstra/A* on a hexagonal grid."""

    def __init__(self, team_color: str | None = None) -> None:
        super().__init__(team_color)

    def _is_wall(self, game_map: Dict, x: int, y: int) -> bool:
        w = game_map["width"]
        cells = game_map["cells"]
        return cells[y * w + x]["type"] == "Wall"

    def _neighbors(self, game_map: Dict, x: int, y: int):
        w, h = game_map["width"], game_map["height"]
        q, r = _offset_to_axial(x, y)
        for direction, (dq, dr) in DIRS.items():
            aq, ar = q + dq, r + dr
            nx, ny = _axial_to_offset(aq, ar)
            if 0 <= nx < w and 0 <= ny < h and not self._is_wall(game_map, nx, ny):
                yield direction, nx, ny

    def _step(self, x: int, y: int, direction: int) -> Tuple[int, int]:
        """Return neighbouring coordinates for a given direction."""
        dq, dr = DIRS[direction]
        q, r = _offset_to_axial(x, y)
        return _axial_to_offset(q + dq, r + dr)

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        aq, ar = _offset_to_axial(*a)
        bq, br = _offset_to_axial(*b)
        return (
            abs(aq - bq)
            + abs(ar - br)
            + abs((aq + ar) - (bq + br))
        ) // 2

    def _dijkstra(
        self, game_map: Dict, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> List[int] | None:
        queue = []
        heappush(queue, (0 + self._heuristic(start, goal), 0, start, []))
        costs = {start: 0}

        while queue:
            _, cost, current, path = heappop(queue)
            if current == goal:
                return path
            if cost > costs[current]:
                continue
            x, y = current
            for direction, nx, ny in self._neighbors(game_map, x, y):
                new_cost = cost + 1
                if (nx, ny) not in costs or new_cost < costs[(nx, ny)]:
                    costs[(nx, ny)] = new_cost
                    priority = new_cost + self._heuristic((nx, ny), goal)
                    heappush(queue, (priority, new_cost, (nx, ny), path + [direction]))
        return None

    def _distance(
        self, game_map: Dict, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Optional[int]:
        """Return shortest path length between two points."""
        path = self._dijkstra(game_map, start, goal)
        return len(path) if path is not None else None

    def _select_targets(self, entities: List[Dict]):
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

    def choose_move(self, game_map: Dict, entities: List[Dict], score: Dict | None = None) -> int:
        player, base, flags = self._select_targets(entities)
        if player is None or base is None:
            return 1

        best_path = None
        for flag in flags:
            path1 = self._dijkstra(game_map, player, flag)
            if path1 is None:
                continue
            path2 = self._dijkstra(game_map, flag, base)
            if path2 is None:
                continue
            path = path1 + path2
            if best_path is None or len(path) < len(best_path):
                best_path = path

        if best_path:
            return best_path[0]

        path_to_base = self._dijkstra(game_map, player, base)
        if path_to_base:
            return path_to_base[0]

        return 1

from __future__ import annotations

from typing import Dict, List

from .dijkstra_ai import DijkstraAI


class DijkstraAICached(DijkstraAI):
    """Dijkstra AI that caches the computed path between turns."""

    def __init__(self, team_color: str | None = None) -> None:
        super().__init__(team_color)
        self._path: list[int] = []

    def choose_move(self, game_map: Dict, entities: List[Dict]) -> int:
        if not self._path:
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
                self._path = best_path
            else:
                path_to_base = self._dijkstra(game_map, player, base)
                if path_to_base:
                    self._path = path_to_base
                else:
                    return 1

        return self._path.pop(0)

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .dijkstra_ai import DijkstraAI


class InterceptAI2(DijkstraAI):
    """Improved interception AI.

    This version evaluates whether attempting an interception is beneficial
    and looks for the earliest interception point on the opponent's path to
    any of their bases.
    """

    def __init__(self, team_color: str | None = None, mode: str = "dynamic") -> None:
        """Create the AI.

        ``mode`` can be ``"dynamic"`` or ``"always"``. In ``"always`` mode the
        bot switches to defensive interception after scoring its first flag. In
        ``"dynamic"`` mode it intercepts only when its own flag is threatened.
        """
        super().__init__(team_color)
        self.mode = mode
        self._last_pos: Optional[Tuple[int, int]] = None
        self._enemy_flag_pos: Optional[Tuple[int, int]] = None
        self._carrying_flag = False
        self._captures = 0

    # ------------------------------------------------------------------
    # Parsing and state tracking
    # ------------------------------------------------------------------
    def _parse_entities(self, entities: List[Dict]):
        player = None
        base = None
        enemy_player = None
        enemy_bases = []
        enemy_flag = None
        my_flag = None
        for e in entities:
            pos = (e["location"]["x"], e["location"]["y"])
            if e["type"] == "Player":
                if e["teamColor"] == self.team_color:
                    player = pos
                else:
                    enemy_player = pos
            elif e["type"] == "Base":
                if e["teamColor"] == self.team_color:
                    base = pos
                else:
                    enemy_bases.append(pos)
            elif e["type"] == "Flag":
                if e["teamColor"] == self.team_color:
                    my_flag = pos
                else:
                    enemy_flag = pos
        return player, base, enemy_player, enemy_bases, enemy_flag, my_flag

    def _update_flag_state(
        self,
        player: Tuple[int, int] | None,
        base: Tuple[int, int] | None,
        enemy_flag: Tuple[int, int] | None,
    ) -> None:
        if player is None:
            return

        if self._carrying_flag:
            if enemy_flag is not None:
                if base is not None and player == base:
                    self._captures += 1
                self._carrying_flag = False
            elif base is not None and player == base:
                self._captures += 1
                self._carrying_flag = False
        else:
            if (
                enemy_flag is None
                and self._enemy_flag_pos is not None
                and self._last_pos == self._enemy_flag_pos
            ):
                self._carrying_flag = True

        self._enemy_flag_pos = enemy_flag
        self._last_pos = player

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def _dijkstra_full(
        self,
        game_map: Dict,
        start: Tuple[int, int],
        goal: Tuple[int, int],
    ) -> Optional[Tuple[List[int], List[Tuple[int, int]]]]:
        from heapq import heappush, heappop

        queue = []
        heappush(queue, (self._heuristic(start, goal), 0, start))
        came_from: dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}
        move_from: dict[Tuple[int, int], int] = {}
        costs = {start: 0}

        while queue:
            _, cost, current = heappop(queue)
            if current == goal:
                break
            if cost > costs[current]:
                continue
            x, y = current
            for direction, nx, ny in self._neighbors(game_map, x, y):
                new_cost = cost + 1
                if (nx, ny) not in costs or new_cost < costs[(nx, ny)]:
                    costs[(nx, ny)] = new_cost
                    came_from[(nx, ny)] = current
                    move_from[(nx, ny)] = direction
                    priority = new_cost + self._heuristic((nx, ny), goal)
                    heappush(queue, (priority, new_cost, (nx, ny)))

        if goal not in came_from:
            return None

        path_dirs: List[int] = []
        path_pos: List[Tuple[int, int]] = [goal]
        current = goal
        while current != start:
            prev = came_from[current]
            if prev is None:
                break
            path_dirs.append(move_from[current])
            current = prev
            path_pos.append(current)
        path_dirs.reverse()
        path_pos.reverse()
        return path_dirs, path_pos

    def _distance(self, game_map: Dict, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[int]:
        path = self._dijkstra(game_map, start, goal)
        return len(path) if path is not None else None

    def _compute_intercept(
        self,
        game_map: Dict,
        player: Tuple[int, int],
        enemy_player: Tuple[int, int] | None,
        enemy_bases: List[Tuple[int, int]],
    ) -> Optional[Tuple[int, int]]:
        """Find the earliest point where we can intercept the enemy."""
        if enemy_player is None or not enemy_bases:
            return None

        best_point = None
        best_enemy_eta = None

        for base in enemy_bases:
            res = self._dijkstra_full(game_map, enemy_player, base)
            if res is None:
                continue
            _, pos_seq = res
            for eta_enemy, pos in enumerate(pos_seq):
                if self._is_wall(game_map, pos[0], pos[1]):
                    continue
                dist_self = self._distance(game_map, player, pos)
                if dist_self is not None and dist_self <= eta_enemy:
                    if best_enemy_eta is None or eta_enemy < best_enemy_eta:
                        best_enemy_eta = eta_enemy
                        best_point = pos
                    break  # earliest intercept on this path

        return best_point

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------
    def choose_move(self, game_map: Dict, entities: List[Dict]) -> int:
        player, base, enemy_player, enemy_bases, enemy_flag, my_flag = self._parse_entities(entities)
        self._update_flag_state(player, base, enemy_flag)

        if player is None or base is None:
            return 1

        if self._carrying_flag:
            path = self._dijkstra(game_map, player, base)
            return path[0] if path else 1

        intercept_point = self._compute_intercept(
            game_map, player, enemy_player, enemy_bases
        )

        intercept_needed = False
        if intercept_point is not None:
            if my_flag is None:
                intercept_needed = True
            elif enemy_player is not None and my_flag is not None:
                dist = self._distance(game_map, enemy_player, my_flag)
                if dist is not None and dist <= 3:
                    intercept_needed = True
            if self.mode == "always" and self._captures >= 1:
                intercept_needed = True

        if intercept_point is not None and intercept_needed:
            path = self._dijkstra(game_map, player, intercept_point)
            if path:
                intercept_len = len(path)
                capture_len = None
                if enemy_flag is not None:
                    d1 = self._distance(game_map, player, enemy_flag)
                    d2 = self._distance(game_map, enemy_flag, base)
                    if d1 is not None and d2 is not None:
                        capture_len = d1 + d2
                if capture_len is None or intercept_len <= capture_len:
                    return path[0]

        return super().choose_move(game_map, entities)

"""Adaptive A* AI using score ratio to balance offence and defence."""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from .dijkstra_ai import DijkstraAI, DIRS


class RatioAI(DijkstraAI):
    """AI that adjusts aggressiveness based on the current score ratio."""

    def __init__(self, team_color: str | None = None) -> None:
        super().__init__(team_color)
        self._last_pos: Optional[Tuple[int, int]] = None
        self._enemy_flag_pos: Optional[Tuple[int, int]] = None
        self._carrying_flag = False

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _parse_entities(self, entities: List[Dict]):
        player = None
        base = None
        enemy_player = None
        enemy_base = None
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
                    enemy_base = pos
            elif e["type"] == "Flag":
                if e["teamColor"] == self.team_color:
                    my_flag = pos
                else:
                    enemy_flag = pos
        return player, base, enemy_player, enemy_base, enemy_flag, my_flag

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
                # Flag respawned -> we scored
                self._carrying_flag = False
            elif base is not None and player == base:
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

    def _distance_field(self, game_map: Dict, start: Tuple[int, int] | None):
        w, h = game_map["width"], game_map["height"]
        dist = [[None for _ in range(w)] for _ in range(h)]
        if start is None:
            return dist
        q = deque([start])
        dist[start[1]][start[0]] = 0
        while q:
            x, y = q.popleft()
            d = dist[y][x]
            for _, nx, ny in self._neighbors(game_map, x, y):
                if dist[ny][nx] is None:
                    dist[ny][nx] = d + 1
                    q.append((nx, ny))
        return dist

    def _weighted_a_star(
        self,
        game_map: Dict,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        danger: List[List[Optional[int]]],
        opp: List[List[Optional[int]]],
        alpha: float,
        beta: float,
    ) -> List[int] | None:
        from heapq import heappush, heappop

        queue = []
        heappush(queue, (0 + self._heuristic(start, goal), 0, start, []))
        costs = {start: 0.0}

        while queue:
            _, cost, current, path = heappop(queue)
            if current == goal:
                return path
            if cost > costs[current]:
                continue
            x, y = current
            for direction, nx, ny in self._neighbors(game_map, x, y):
                dval = danger[ny][nx]
                oval = opp[ny][nx]
                cell_cost = 1.0
                if dval is not None:
                    cell_cost += alpha * (1.0 / (dval + 1))
                if oval is not None:
                    cell_cost -= beta * (1.0 / (oval + 1))
                new_cost = cost + cell_cost
                if (nx, ny) not in costs or new_cost < costs[(nx, ny)]:
                    costs[(nx, ny)] = new_cost
                    priority = new_cost + self._heuristic((nx, ny), goal)
                    heappush(queue, (priority, new_cost, (nx, ny), path + [direction]))
        return None

    def _coeffs_for_ratio(self, ratio: float) -> Tuple[float, float]:
        if ratio < 1.0:
            return 0.2, 1.5
        if ratio > 2.0:
            return 1.2, 0.3
        return 0.6, 1.0

    def _evaluate_move(
        self,
        game_map: Dict,
        next_pos: Tuple[int, int],
        enemy_pos: Tuple[int, int] | None,
        base: Tuple[int, int],
        enemy_base: Tuple[int, int] | None,
        enemy_flag: Tuple[int, int] | None,
        my_flag: Tuple[int, int] | None,
        carrying: bool,
        score: Dict,
    ) -> float:
        my_score = score.get(self.team_color, 0)
        opp_color = "Red" if self.team_color == "Blue" else "Blue"
        opp_score = score.get(opp_color, 0)

        # Estimate time to our score
        if carrying:
            d_me = self._distance(game_map, next_pos, base)
        else:
            if enemy_flag is None:
                d_me = None
            else:
                d1 = self._distance(game_map, next_pos, enemy_flag)
                d2 = self._distance(game_map, enemy_flag, base)
                d_me = d1 + d2 if d1 is not None and d2 is not None else None

        if enemy_pos is None or enemy_base is None:
            d_enemy = None
        else:
            if my_flag is None:
                # assume enemy carries our flag
                d_enemy = self._distance(game_map, enemy_pos, enemy_base)
            else:
                d1 = self._distance(game_map, enemy_pos, my_flag)
                d2 = self._distance(game_map, my_flag, enemy_base)
                d_enemy = d1 + d2 if d1 is not None and d2 is not None else None

        if d_me is None and d_enemy is None:
            return (my_score + 1) / (opp_score + 1)

        if d_enemy is None or (d_me is not None and d_me <= d_enemy):
            my_score += 1
        else:
            opp_score += 1

        return (my_score + 1) / (opp_score + 1)

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------
    def choose_move(
        self, game_map: Dict, entities: List[Dict], score: Dict | None = None
    ) -> int:
        if score is None:
            score = {}

        (
            player,
            base,
            enemy_player,
            enemy_base,
            enemy_flag,
            my_flag,
        ) = self._parse_entities(entities)

        self._update_flag_state(player, base, enemy_flag)

        if player is None or base is None:
            return 1

        ratio = (score.get(self.team_color, 0) + 1) / (
            score.get("Red" if self.team_color == "Blue" else "Blue", 0) + 1
        )
        alpha, beta = self._coeffs_for_ratio(ratio)

        target = base if self._carrying_flag else (enemy_flag or base)

        danger_field = self._distance_field(game_map, enemy_player)
        opp_field = self._distance_field(game_map, target)

        path = self._weighted_a_star(
            game_map, player, target, danger_field, opp_field, alpha, beta
        )
        if not path:
            return 1

        best_move = path[0]
        nx, ny = player[0] + DIRS[best_move][0], player[1] + DIRS[best_move][1]
        best_ratio = self._evaluate_move(
            game_map,
            (nx, ny),
            enemy_player,
            base,
            enemy_base,
            enemy_flag,
            my_flag,
            self._carrying_flag,
            score,
        )

        # Try one sidestep alternative if available
        for direction, (dx, dy) in DIRS.items():
            if direction == best_move:
                continue
            sx, sy = player[0] + dx, player[1] + dy
            if sx < 0 or sy < 0 or sx >= game_map["width"] or sy >= game_map["height"]:
                continue
            if self._is_wall(game_map, sx, sy):
                continue
            ratio_alt = self._evaluate_move(
                game_map,
                (sx, sy),
                enemy_player,
                base,
                enemy_base,
                enemy_flag,
                my_flag,
                self._carrying_flag,
                score,
            )
            if ratio_alt > best_ratio:
                best_ratio = ratio_alt
                best_move = direction

        return best_move


"""Potential-based reward shaping. Training only: scoring and the arena never use it.

phi(square) = -(steps from the square to the exit) / (the most steps any square needs), so phi is
0 at the exit and -1 at the farthest square. Each training step adds gamma * phi(s') - phi(s) to
the game's reward: a step towards the exit earns a little, a step away costs a little. Shaping of
this form does not change which way of playing is best (Ng, Harada and Russell, 1999).
"""

from __future__ import annotations

from collections import deque

from minotaurus.engine.levels import MOVES, Level


def potential(level: Level) -> dict[tuple[int, int], float]:
    """phi for every floor square of the level, from a BFS that starts at the exit.

    Example: a corridor S . . E gives phi(S) = -1, then -2/3, -1/3, and phi(E) = 0.
    """
    distance = {level.exit: 0}
    queue = deque([level.exit])
    while queue:
        x, y = queue.popleft()
        for dx, dy in MOVES:
            nxt = (x + dx, y + dy)
            if nxt not in distance and not level.is_wall(*nxt):
                distance[nxt] = distance[(x, y)] + 1
                queue.append(nxt)
    longest = max(distance.values())
    phi = {}
    for square, steps in distance.items():
        phi[square] = -steps / longest
    return phi


def shaped_reward(
    reward: float,
    phi: dict[tuple[int, int], float],
    before: tuple[int, int],
    after: tuple[int, int],
    gamma: float,
    on_bump: bool,
) -> float:
    """The game's reward plus gamma * phi(after) - phi(before).

    A bump into a wall leaves the dot in place (after == before). With on_bump=False such a step
    keeps the plain game reward (the experimental "Enb" variant).
    """
    if after == before and not on_bump:
        return reward
    return reward + gamma * phi[after] - phi[before]


def visits_before(env) -> int:
    """How often the dot was on its square before the step it just made (MazeEnv counts the
    square it ends on, a bump too: a bump re-enters the dot's own square)."""
    return env.visits[env.pos] - 1


def visit_reward(count_before: int, novelty_bonus: float, revisit_penalty: float) -> float:
    """Training-only reward from the visit count of the square just entered, counted before the
    step: novelty_bonus for a square never visited, minus revisit_penalty for each earlier visit.

    Example: novelty_bonus 0.02, revisit_penalty 0.01 -> a new square +0.02, a square visited
    once before -0.01, three times before -0.03.
    """
    if count_before == 0:
        return novelty_bonus
    return -revisit_penalty * count_before

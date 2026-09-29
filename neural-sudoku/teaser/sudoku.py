"""
Solve the puzzle used in the teaser and export web/puzzle.json.

Puzzle: Arto Inkala (2012), widely publicised as "the world's hardest sudoku" (21 clues).
The export holds the givens, the verified unique solution, and an order in which the empty
cells become certain (MRV depth-first search on the successful path). The animation uses
that order so cells crystallise in a plausible, constraint-driven sequence.
"""

import json
import os

PUZZLE = (
    "8........"
    "..36....."
    ".7..9.2.."
    ".5...7..."
    "....457.."
    "...1...3."
    "..1....68"
    "..85...1."
    ".9....4.."
)

PEERS = []
for i in range(81):
    r, c = divmod(i, 9)
    br, bc = 3 * (r // 3), 3 * (c // 3)
    p = {r * 9 + k for k in range(9)} | {k * 9 + c for k in range(9)} | \
        {(br + a) * 9 + bc + b for a in range(3) for b in range(3)}
    p.discard(i)
    PEERS.append(p)


def candidates(g, i):
    return set(range(1, 10)) - {g[j] for j in PEERS[i]}


def solve(g, order, count=None):
    empty = [i for i in range(81) if g[i] == 0]
    if not empty:
        if count is not None:
            count[0] += 1
            return count[0] > 1  # keep searching only to prove uniqueness
        return True
    i = min(empty, key=lambda k: len(candidates(g, k)))
    for d in sorted(candidates(g, i)):
        g[i] = d
        order.append(i)
        if solve(g, order, count):
            return True
        order.pop()
        g[i] = 0
    return False


def main():
    grid = [0 if ch == "." else int(ch) for ch in PUZZLE]
    sol, order = grid[:], []
    assert solve(sol, order)
    count = [0]
    solve(grid[:], [], count)
    assert count[0] == 1, "puzzle must have a unique solution"
    for i in range(81):  # verify
        assert sol[i] not in {sol[j] for j in PEERS[i]}
    out = {"givens": grid, "solution": sol, "order": order}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "puzzle.json")
    with open(path, "w") as f:
        json.dump(out, f)
    print("clues:", sum(1 for v in grid if v), "empty:", len(order))
    for r in range(9):
        print(" ".join(str(v) for v in sol[r * 9:(r + 1) * 9]))


if __name__ == "__main__":
    main()

import numpy as np
import itertools

DIRECTIONS = [
    'N',
    'NE',
    'SE',
    'S',
    'SW',
    'NW',
]

COLORS = {
    'white': -1,
    'black': -2,
}

COLOR_NAMES = {
    -1: 'white',
    -2: 'black',
}

BOARD = [
    [1, 2, 3, 4, 5, 6],             # 0 adj (util)
    [8, 9, 2, 4, 6, 7],             # 1 adj
    [9, 10, 11, 3, 5, 1],           # 2 adj
    [2, 11, 12, 13, 4, 6],          # 3 adj
    [1, 3, 13, 14, 15, 5],          # 4 adj
    [6, 2, 4, 15, 16, 17],          # 5 adj
    [7, 1, 3, 5, 17, 18],           # 6 adj
    [-1, 8, 1, 6, 18, -2],          # 7 adj
    [-2, -1, 9, 1, 7, -1],          # 8 adj
    [-1, -2, 10, 2, 1, 8],          # 9 adj 
    [-1, -1, -2, 11, 2, 9],         # 10 adj
    [10, -1, -2, 12, 3, 2],         # 11 adj
    [11, -1, -2, -2, 13, 3],        # 12 adj
    [3, 12, -1, -2, 14, 4],         # 13 adj
    [4, 13, -2, -1, -2, 15],        # 14 adj
    [5, 4, 14, -2, -1, 16],         # 15 adj
    [17, 5, 15, -2, -2, -1],        # 16 adj
    [18, 6, 5, 16, -2, -1],         # 17 adj
    [-1, 7, 6, 17, -2, -1],         # 18 adj
]

NUM_MOVES = len(BOARD) - 1
ALL_ONE_SWAPS = [[tuple(sorted([t1, t2])) for t2 in BOARD[t1] if t2 > 0] for t1 in range(1, 19)]
ALL_ONE_SWAPS = set([item for sublist in ALL_ONE_SWAPS for item in sublist])
ALL_TWO_SWAPS = list(itertools.product(ALL_ONE_SWAPS, ALL_ONE_SWAPS))
STATE_SHAPE = (len(BOARD), 6, 2)
WHITEC = 4
BLACKC = 5


class Board:
    def __init__(self):
        self._state = np.zeros((len(BOARD), 6, 2), dtype=bool)
        self._visited = np.zeros(len(BOARD), dtype=bool)
        self.match_swaps = {swap: 0 for swap in ALL_ONE_SWAPS}
        self.mismatch_swaps = {swap: 0 for swap in ALL_ONE_SWAPS}

        # zero points North
        self._state[0][0][0] = True

    def get_tile_color(self, tile, state):
        return -(2 - int(np.where(state[tile].any(axis=0))[0]))

    def get_tile_direction(self, tile, state):
        return int(np.where(state[tile].any(axis=1))[0])

    @property
    def state(self):
        return self._state

    def move(self, tile, color, direction):
        if direction in DIRECTIONS and color in COLORS and 1 <= tile <= 18:
            if not self.state[tile].any():
                self._state[tile][DIRECTIONS.index(direction)][COLORS[color]] = True
                return True
        return False

    def swap(self, t1, t2):
        if 0 <= t1 <= 18 and 0 <= t2 <= 18:
            self._state[t1], self._state[t2] = np.array(self._state[t2]), np.array(self._state[t1])

    @property
    def complete(self):
        return self._state.any(axis=1).any(axis=1).all()

    def eval(self):
        if self.complete:
            return self.go()

    def greedy_swap(self):
        if self.complete:
            for mismatch_swap, match_swap in ALL_TWO_SWAPS:
                self.swap(*mismatch_swap)
                self.swap(*match_swap)
                _, _, match_win = self.eval()
                self._visited = np.zeros(len(BOARD), dtype=bool)
                if match_win:
                    self.match_swaps[match_swap] += 1.0/len(ALL_ONE_SWAPS)
                else:
                    self.mismatch_swaps[mismatch_swap] += 1.0/len(ALL_ONE_SWAPS)
                self.swap(*match_swap)
                self.swap(*mismatch_swap)
        return max(self.mismatch_swaps, key=self.mismatch_swaps.get), max(self.match_swaps, key=self.match_swaps.get)

    def make_greedy_swaps(self):
        mismatch_swap, match_swap = self.greedy_swap()
        self.swap(*mismatch_swap)
        self.swap(*match_swap)

    def go(self, prev_tile = 0, current_tile = 0, current_dir = 0, color = 'black', path = None):
        if path is None:
            path = []
        while current_tile >= 0:
            path.append(current_tile)
            # tile already played
            if self._visited[current_tile]:
                prev_tile_color = -(2 - int(np.where(self.state[prev_tile].any(axis=0))[0]))
                return self.go(current_tile, BOARD[current_tile][current_dir], current_dir, prev_tile_color, path)

            # tile visit first time
            self._visited[current_tile] = True
            new_dir = int(np.where(self.state[current_tile].any(axis=1))[0])
            next_tile_color = -(2 - int(np.where(self.state[current_tile].any(axis=0))[0]))
            return self.go(current_tile, BOARD[current_tile][new_dir], new_dir, next_tile_color, path)

        # hit border (base case)
        vic = "went out on " + str(COLOR_NAMES[color]) + " from " + str(prev_tile) + DIRECTIONS[current_dir]
        vic += " " + ("match" if color == current_tile else "mismatch") + " wins"
        return path, vic, True if color == current_tile else False


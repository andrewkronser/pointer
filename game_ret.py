import board
import numpy as np
from repoze.lru import lru_cache


def best_legal_move(b, output, white_count, black_count):
    output = np.array(output)
    output = np.reshape(output, board.STATE_SHAPE)

    if white_count == 0:
        output[:,:,1] = -float("inf")

    if black_count == 0:
        output[:,:,0] = -float("inf")

    max_ndx = np.argmax(output)
    max_tile, max_dir, max_c = np.unravel_index(max_ndx, board.STATE_SHAPE)

    while not b.move(max_tile, board.COLOR_NAMES[-2 + max_c], board.DIRECTIONS[max_dir]):
        output[max_tile][max_dir][max_c] = -float("inf")
        max_ndx = np.argmax(output)
        max_tile, max_dir, max_c = np.unravel_index(max_ndx, board.STATE_SHAPE)

    return max_c


def play_game(mismatch_net, match_net):
    b = board.Board()
    white_count = [board.WHITEC, board.WHITEC]
    black_count = [board.BLACKC, board.BLACKC]
    
    for i in range(board.NUM_MOVES):
        # mismatch
        if not i % 2:
            output = mismatch_net.activate(b.state.flatten())
            color = 'white' if best_legal_move(b, output, white_count[0], black_count[0]) else 'black'
            if color == 'white':
                white_count[0] -= 1
            else:
                black_count[0] -= 1

        # match
        else:
            output = match_net.activate(b.state.flatten())
            color = 'white' if best_legal_move(b, output, white_count[1], black_count[1]) else 'black'
            if color == 'white':
                white_count[1] -= 1
            else:
                black_count[1] -= 1

    b.make_greedy_swaps()
    return b.eval()[-1], b.greedy_swap()

@lru_cache(maxsize=500)
def play_mismatch_game(net_one, net_two):
    scores = [0,0]
    wins = [0,0]
    # Round 1: net_one mismatch, net_two match
    if play_game(net_one, net_two)[0]:
        scores[1] += 1
        wins[0] += 1
    else:
        scores[0] += 1
        wins[1] += 1

    return scores, wins, play_game(net_one, net_two)[1]

@lru_cache(maxsize=500)
def play_match_game(net_one, net_two):
    scores = [0,0]
    wins = [0,0]

    # Round 2: net_one match, net_two mismatch
    if play_game(net_two, net_one)[0]:
        scores[0] += 1
        wins[0] += 1
    else:
        scores[1] += 1
        wins[1] += 1

    return scores, wins

@lru_cache(maxsize=500)
def play_set(net_one, net_two):
    scores = [0,0]
    wins = [0,0]
    # Round 1: net_one mismatch, net_two match
    if play_game(net_one, net_two)[0]:
        scores[1] += 1
        wins[0] += 1
    else:
        scores[0] += 1
        wins[1] += 1

    # Round 2: net_one match, net_two mismatch
    if play_game(net_two, net_one)[0]:
        scores[0] += 1
        wins[0] += 1
    else:
        scores[1] += 1
        wins[1] += 1

    return scores, wins


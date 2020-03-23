import neat
import itertools
from neat.six_util import itervalues
import game_ret
from collections import Counter

CONFIG = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     'config-feedforward')
NUM_CHAMPIONS = 5
match_files = ["match190", "match193", "match196", "match199"]
mismatch_files = ["mismatch190", "mismatch193", "mismatch196", "mismatch199"]

matches = [[g for g in itervalues(neat.checkpoint.Checkpointer.restore_checkpoint(match_file).population)] for match_file in match_files]
mismatches = [[g for g in itervalues(neat.checkpoint.Checkpointer.restore_checkpoint(mismatch_file).population)] for mismatch_file in mismatch_files]

def get_champions(gs):
    champions = []
    for i in range(NUM_CHAMPIONS):
        champion = max(gs, key=lambda g: g.fitness)
        gs.remove(max(gs, key=lambda g: g.fitness))
        champions.append(neat.nn.FeedForwardNetwork.create(champion, CONFIG))

    return champions


match_champs = list(itertools.chain.from_iterable([get_champions(match_players) for match_players in matches]))
mismatch_champs = list(itertools.chain.from_iterable([get_champions(mismatch_players) for mismatch_players in mismatches]))



match_score, mismatch_score = 0.0, 0.0
swaps = []

matchups = list(itertools.product(match_champs, mismatch_champs))
for match, mismatch in matchups:
    scores, wins, swap = game_ret.play_mismatch_game(mismatch, match)
    swaps.append(swap)
    match_score += scores[1]
    mismatch_score += scores[0]

print match_score/len(matchups), mismatch_score/len(matchups)
swaps = list(itertools.chain.from_iterable(swaps))
swaps = list(itertools.chain.from_iterable(swaps))
print Counter(swaps)

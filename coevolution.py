import neat
from itertools import product, repeat
from random import shuffle
import game
import multiprocessing

BOOTSTRAP = 12
NUM_HALL_OF_FAMERS = 8
NUM_CHAMPIONS = 4

def eval_pair_unpack(args):
    return eval_pair(*args)

def eval_pair(gnet_and_role, opp):
    genome, net, role = gnet_and_role

    if role == 'match':
        scores, wins = game.play_match_game(net, opp)
    else:
        scores, wins = game.play_mismatch_game(net, opp)

    genome.fitness += 1.0/(NUM_HALL_OF_FAMERS + NUM_CHAMPIONS) * scores[0]
    return genome.fitness

def evolve(put_q, get_q, role, config):
    # First, put an empty list
    put_q.put([])
    pop = neat.Population(config)
    if role == 'match':
        pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.checkpoint.Checkpointer(generation_interval=5, filename_prefix=role))

    hof = set()
    pool = multiprocessing.Pool(2)

    def get_nets_and_gs_and_gids(genomes, config):
        nets = []
        gs = []
        gids = []
        for genome_id, genome in genomes:
            genome.fitness = 0.0
            gs.append(genome)
            gids.append(genome_id)
            nets.append(neat.nn.FeedForwardNetwork.create(genome, config))
        return nets, gs, gids

    def get_champions(nets, gs, gids):
        gnets = list(zip(nets, gs, gids))

        champions = []
        species = set()

        while gnets and len(champions) < NUM_CHAMPIONS + (NUM_HALL_OF_FAMERS - len(hof)):
            challenger = max(gnets, key=lambda x: x[1].fitness)
            gnets.remove(max(gnets, key=lambda x: x[1].fitness))
            spec = pop.species.get_species(challenger[2])
            if spec not in species:
                species.add(spec)
                # Add the network as an opponent
                champions.append(challenger[0])

        return champions

    def run_matchups(nets, gs, gids, opponents):
        if not opponents:
            # If no opponents are present yet, play a bootstrap round
            matchups = list(product(zip(gs, nets, repeat(role, len(gs))), nets[:BOOTSTRAP])) 
        else:
            # Otherwise, play all opponents
            matchups = list(product(zip(gs, nets, repeat(role, len(gs))), opponents))

        for g, new_fit in zip(gs, pool.map(eval_pair_unpack, matchups)):
            g.fitness += new_fit

        # Add the round's champion network to the Hall of Fame
        hof.add(max(zip(nets, gs), lambda x: x[1].fitness)[0])

        # Return species champions for additional opponents
        return get_champions(nets, gs, gids)


    def eval_genomes(genomes, config):
        nets, gs, gids = get_nets_and_gs_and_gids(genomes, config)
        opponents = get_q.get()
        champions = run_matchups(nets, gs, gids, opponents)

        hoffers = list(hof)
        shuffle(hoffers)
        put_q.put(champions.extend(hoffers[:min(NUM_HALL_OF_FAMERS, len(hof))]))

    pop.run(eval_genomes, n=200)


config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     'config-feedforward')

p1_hof = multiprocessing.Queue()
p2_hof = multiprocessing.Queue()

mismatch_proc = multiprocessing.Process(target=evolve, args=(p1_hof, p2_hof, 'mismatch', config))
match_proc = multiprocessing.Process(target=evolve, args=(p2_hof, p1_hof, 'match', config))

mismatch_proc.start()
match_proc.start()

mismatch_proc.join()
match_proc.join()


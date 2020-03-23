import neat
from neat.six_util import itervalues


def get_net(filename):
    pop = neat.checkpoint.Checkpointer.restore_checkpoint(filename)
    g = None
    genomes = list(itervalues(pop.population))
    g = max(genomes, key=lambda x: x.fitness)
    return neat.nn.FeedForwardNetwork.create(g, pop.config)


from .random_ai import RandomAI
from .shortest_path_ai import ShortestPathAI
from .dijkstra_ai import DijkstraAI

ALL_MODELS = {
    "RandomAI": RandomAI,
    "ShortestPathAI": ShortestPathAI,
    "DijkstraAI": DijkstraAI,
}

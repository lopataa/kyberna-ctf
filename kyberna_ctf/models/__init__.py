from .random_ai import RandomAI
from .shortest_path_ai import ShortestPathAI
from .dijkstra_ai import DijkstraAI
from .intercept_ai import InterceptAI

ALL_MODELS = {
    "RandomAI": RandomAI,
    "ShortestPathAI": ShortestPathAI,
    "DijkstraAI": DijkstraAI,
    "InterceptAI": InterceptAI,
}

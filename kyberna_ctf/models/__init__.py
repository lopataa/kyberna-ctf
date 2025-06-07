from .random_ai import RandomAI
from .shortest_path_ai import ShortestPathAI
from .dijkstra_ai import DijkstraAI
from .intercept_ai import InterceptAI
from .intercept_ai2 import InterceptAI2

ALL_MODELS = {
    "RandomAI": RandomAI,
    "ShortestPathAI": ShortestPathAI,
    "DijkstraAI": DijkstraAI,
    "InterceptAI": InterceptAI,
    "InterceptAI2": InterceptAI2,
}

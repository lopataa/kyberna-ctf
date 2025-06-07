from .random_ai import RandomAI
from .shortest_path_ai import ShortestPathAI
from .dijkstra_ai import DijkstraAI
from .dijkstra_cached_ai import DijkstraAICached

ALL_MODELS = {
    "RandomAI": RandomAI,
    "ShortestPathAI": ShortestPathAI,
    "DijkstraAI": DijkstraAI,
    "DijkstraAICached": DijkstraAICached,
}

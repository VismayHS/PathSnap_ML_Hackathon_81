"""Directed physical graph routing with bounded searches and original arc IDs."""
from collections import OrderedDict
import heapq
import math
import numpy as np


class RoadGraph:
    def __init__(self, arcs, lengths, cache_size=4096):
        self.arcs, self.lengths = arcs, lengths
        self.adjacency = {}
        for arc_id, ((u, v), distance) in enumerate(zip(arcs, lengths)):
            if np.isfinite(distance) and distance >= 0:
                self.adjacency.setdefault(int(u), []).append((int(v), float(distance), arc_id))
        self.cache, self.cache_size = OrderedDict(), cache_size

    def shortest(self, source, target, limit):
        """Return (metres, arc sequence) or (inf, ()); exact within explicit bound."""
        if source == target:
            return 0., ()
        key = (int(source), int(target), float(limit))
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        heap, distance, previous = [(0., int(source))], {int(source): 0.}, {}
        result = (math.inf, ())
        while heap:
            cost, node = heapq.heappop(heap)
            if cost != distance[node]:
                continue
            if node == target:
                route, current = [], node
                while current != source:
                    current, arc_id = previous[current]
                    route.append(arc_id)
                result = (cost, tuple(reversed(route)))
                break
            for neighbor, length, arc_id in self.adjacency.get(node, ()):
                proposed = cost + length
                if proposed <= limit and proposed < distance.get(neighbor, math.inf):
                    distance[neighbor] = proposed
                    previous[neighbor] = (node, arc_id)
                    heapq.heappush(heap, (proposed, neighbor))
        self.cache[key] = result
        if len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)
        return result

    def between(self, arc_a, fraction_a, arc_b, fraction_b, limit, noise_m=15.):
        """Partial source/target segment distances; reversed travel needs a real cycle.

        Up to noise_m backward displacement on the same arc is treated as stationary
        projection noise (zero travel), never as permission to add a reverse edge.
        """
        if arc_a == arc_b:
            progress = (fraction_b-fraction_a)*self.lengths[arc_a]
            if progress >= -noise_m:
                return max(0., float(progress)), ()
        remainder = (1-fraction_a)*self.lengths[arc_a] + fraction_b*self.lengths[arc_b]
        if remainder > limit:
            return math.inf, ()
        distance, route = self.shortest(self.arcs[arc_a, 1], self.arcs[arc_b, 0], limit-remainder)
        return distance+float(remainder), route

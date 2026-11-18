"""Directed physical graph routing with bounded searches and original arc IDs.

The road network of one trip as a one-way (directed) graph. The HMM uses it to ask:
"how far would a car have to DRIVE to get from this road to that road?"
"""
from collections import OrderedDict
import heapq
import math
import numpy as np


class RoadGraph:
    """A trip's road network, built from its arcs (one-way roads between nodes)."""

    def __init__(self, arcs, lengths, cache_size=4096):
        """Build the graph from the trip's arcs and their lengths in metres.

        adjacency[node] lists every road leaving that node as (next node, length, arc ID).
        Roads with an invalid length are left out. Recent shortest-path answers are
        cached (up to cache_size) because the HMM asks the same questions many times.
        """
        self.arcs, self.lengths = arcs, lengths
        self.adjacency = {}
        for arc_id, ((u, v), distance) in enumerate(zip(arcs, lengths)):
            if np.isfinite(distance) and distance >= 0:
                self.adjacency.setdefault(int(u), []).append((int(v), float(distance), arc_id))
        self.cache, self.cache_size = OrderedDict(), cache_size

    def shortest(self, source, target, limit):
        """Return (metres, arc sequence) or (inf, ()); exact within explicit bound.

        Dijkstra's shortest-path search from node `source` to node `target`, following
        roads only in their allowed direction. It gives up on paths longer than `limit`
        metres (farther than a car could drive in the time), returning (inf, ()).
        On success it returns the driving distance and the list of arcs driven.
        """
        if source == target:
            return 0., ()
        key = (int(source), int(target), float(limit))
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        # heap: nodes to visit, closest first; distance: best known distance to each node;
        # previous: how we reached each node (for rebuilding the path).
        heap, distance, previous = [(0., int(source))], {int(source): 0.}, {}
        result = (math.inf, ())
        while heap:
            cost, node = heapq.heappop(heap)
            if cost != distance[node]:
                continue  # an outdated entry; a shorter way to this node was already found
            if node == target:
                # Reached the target: walk back through `previous` to list the arcs driven.
                route, current = [], node
                while current != source:
                    current, arc_id = previous[current]
                    route.append(arc_id)
                result = (cost, tuple(reversed(route)))
                break
            for neighbor, length, arc_id in self.adjacency.get(node, ()):
                proposed = cost + length
                # Keep only paths within the driving limit that improve on what we know.
                if proposed <= limit and proposed < distance.get(neighbor, math.inf):
                    distance[neighbor] = proposed
                    previous[neighbor] = (node, arc_id)
                    heapq.heappush(heap, (proposed, neighbor))
        self.cache[key] = result
        if len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)  # forget the oldest cached answer
        return result

    def between(self, arc_a, fraction_a, arc_b, fraction_b, limit, noise_m=15.):
        """Partial source/target segment distances; reversed travel needs a real cycle.

        Up to noise_m backward displacement on the same arc is treated as stationary
        projection noise (zero travel), never as permission to add a reverse edge.

        Driving distance from a point on road A to a point on road B. The `fraction`
        values say how far along each road the point is (0 = start, 1 = end).
          - Same road, moving forward (or jittering back by up to noise_m): the gap along it.
          - Different roads: the rest of road A + shortest path between them + the start
            of road B up to the point.
        Returns (inf, ()) if this is farther than `limit` or not drivable at all.
        """
        if arc_a == arc_b:
            progress = (fraction_b-fraction_a)*self.lengths[arc_a]
            if progress >= -noise_m:
                travel = max(0., float(progress))
                return (travel, ()) if travel <= limit else (math.inf, ())
        # Distance left on road A plus distance already covered on road B.
        remainder = (1-fraction_a)*self.lengths[arc_a] + fraction_b*self.lengths[arc_b]
        if remainder > limit:
            return math.inf, ()
        # Shortest path from the END node of road A to the START node of road B.
        distance, route = self.shortest(self.arcs[arc_a, 1], self.arcs[arc_b, 0], limit-remainder)
        return distance+float(remainder), route

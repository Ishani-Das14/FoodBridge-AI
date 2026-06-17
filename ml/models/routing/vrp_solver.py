import logging
from typing import List, Tuple, Dict
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from ml.models.routing.distance_matrix import DistanceMatrixBuilder

logger = logging.getLogger(__name__)

class VRPSolver:
    def __init__(self):
        self.matrix_builder = DistanceMatrixBuilder()

    def nearest_neighbor_heuristic(self, stops: List[Dict]) -> List[Dict]:
        """Simple greedy fallback if OR-Tools times out or fails."""
        logger.warning("OR-Tools timeout/failure, using nearest-neighbour fallback")
        if not stops:
            return []
            
        unvisited = stops[1:]
        current = stops[0]
        
        route = []
        current["arrival_time_seconds"] = 0
        route.append(current)
        
        current_time = 0
        
        while unvisited:
            # Find closest
            closest = None
            closest_dist = float('inf')
            
            for stop in unvisited:
                # Use Haversine distance mapped to seconds roughly
                # DistanceMatrixBuilder haversine computes km, we multiply by 120s
                dist = self.matrix_builder._haversine_distance(
                    current["lat"], current["lng"], stop["lat"], stop["lng"]
                )
                time_sec = int(dist * 120.0)
                if time_sec < closest_dist:
                    closest_dist = time_sec
                    closest = stop
                    
            unvisited.remove(closest)
            current_time += closest_dist
            closest["arrival_time_seconds"] = current_time
            route.append(closest)
            current = closest
            
        return route

    def solve(self, stops: List[Dict], time_windows: List[Tuple[int, int]]) -> List[Dict]:
        """
        Solves the Vehicle Routing Problem with Time Windows.
        Returns the ordered route of stops.
        """
        if len(stops) < 2:
            return stops

        # Step 1: Build distance matrix
        time_matrix = self.matrix_builder.build_matrix(stops)
        
        # Step 2: Create OR-Tools RoutingIndexManager and RoutingModel
        manager = pywrapcp.RoutingIndexManager(len(stops), 1, 0) # num_locations, num_vehicles, depot_index
        routing = pywrapcp.RoutingModel(manager)

        # Step 3: Register transit callback using time matrix
        def time_callback(from_index, to_index):
            # Convert from routing variable Index to time matrix NodeIndex
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Step 4: Add time window constraints
        dimension_name = 'Time'
        # Arbitrary max time (e.g. 24 hours in seconds)
        max_time = 24 * 3600
        
        routing.AddDimension(
            transit_callback_index,
            0,         # allow waiting time
            max_time,  # maximum time per vehicle
            False,     # Don't force start cumul to zero
            dimension_name
        )
        time_dimension = routing.GetDimensionOrDie(dimension_name)

        for location_idx, (start_window, end_window) in enumerate(time_windows):
            if location_idx == 0:
                continue # Depot start time is naturally 0
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(start_window, end_window)

        # Step 5: Set first solution strategy
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        
        # Step 6: Set local search metaheuristic and time limit
        search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search_parameters.time_limit.seconds = 10

        # Step 7: Solve and extract route
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            return self.nearest_neighbor_heuristic(stops)

        # Step 8: Return ordered list of stops with ETAs
        ordered_route = []
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            arrival_time = solution.Min(time_var)
            
            stop_info = stops[node_index].copy()
            stop_info["arrival_time_seconds"] = arrival_time
            ordered_route.append(stop_info)
            
            index = solution.Value(routing.NextVar(index))
            
        # Add the final node (if it's a loop returning to depot, but usually we just end at the last dropoff)
        # In this simple VRP, OR-tools forces a return to depot, but we only care about the dropoff
        # Let's see if the end node is different. For an open path, we could drop the return to depot.
        # But we only track up to the last dropoff.
        
        return ordered_route

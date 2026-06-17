import os
import math
import hashlib
import json
import logging
import requests
from typing import List, Dict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
import sys
sys.path.append(project_root)

from backend.app.core.redis import redis_client

logger = logging.getLogger(__name__)

class DistanceMatrixBuilder:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance between two points in km."""
        R = 6371.0 # Earth radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def build_fallback_matrix(self, locations: List[Dict]) -> List[List[int]]:
        """
        Computes a fallback distance matrix using Haversine distance,
        assuming a constant urban average speed of 30 km/h.
        Returns time in seconds.
        """
        logger.warning("Using fallback Haversine matrix instead of Google Maps API.")
        n = len(locations)
        matrix = [[0] * n for _ in range(n)]
        
        # 30 km/h = 30 / 3600 km/s -> 1 km takes 120 seconds
        speed_factor_sec_per_km = 120.0
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_km = self._haversine_distance(
                        locations[i]["lat"], locations[i]["lng"],
                        locations[j]["lat"], locations[j]["lng"]
                    )
                    time_sec = int(dist_km * speed_factor_sec_per_km)
                    matrix[i][j] = time_sec
        return matrix

    def build_matrix(self, locations: List[Dict]) -> List[List[int]]:
        """
        Builds the time matrix (in seconds) between all locations.
        Attempts Google Maps API first, falls back to Haversine.
        """
        if not locations:
            return []

        # Create a deterministic hash for the specific set of locations
        loc_str = "|".join([f"{loc['lat']},{loc['lng']}" for loc in locations])
        loc_hash = hashlib.md5(loc_str.encode()).hexdigest()
        cache_key = f"distance_matrix:{loc_hash}"

        # 1. Try Cache
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        # 2. Try Google Maps API
        if self.api_key:
            try:
                origins = "|".join([f"{loc['lat']},{loc['lng']}" for loc in locations])
                destinations = origins
                url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
                params = {
                    "origins": origins,
                    "destinations": destinations,
                    "departure_time": "now", # triggers duration_in_traffic
                    "key": self.api_key
                }
                
                resp = requests.get(url, params=params, timeout=5)
                data = resp.json()
                
                if data.get("status") == "OK":
                    n = len(locations)
                    matrix = [[0] * n for _ in range(n)]
                    rows = data.get("rows", [])
                    for i, row in enumerate(rows):
                        elements = row.get("elements", [])
                        for j, element in enumerate(elements):
                            if element.get("status") == "OK":
                                # Prefer duration_in_traffic, fallback to normal duration
                                duration = element.get("duration_in_traffic", element.get("duration", {}))
                                matrix[i][j] = duration.get("value", 0)
                            else:
                                raise ValueError(f"Google API element error: {element.get('status')}")
                    
                    # Cache result
                    if redis_client:
                        try:
                            redis_client.setex(cache_key, 600, json.dumps(matrix))
                        except Exception:
                            pass
                            
                    return matrix
                else:
                    logger.error(f"Google API returned status: {data.get('status')}")
            except Exception as e:
                logger.error(f"Google Maps API failed: {e}")

        # 3. Fallback
        matrix = self.build_fallback_matrix(locations)
        return matrix

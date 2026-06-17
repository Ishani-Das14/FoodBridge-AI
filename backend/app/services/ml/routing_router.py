import os
import sys
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from ml.models.routing.vrp_solver import VRPSolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning Routing"])

class LocationInput(BaseModel):
    lat: float
    lng: float
    name: str = ""
    address: str = ""

class RouteOptimizationRequest(BaseModel):
    delivery_id: str
    volunteer_location: LocationInput
    restaurant: LocationInput
    ngo: LocationInput
    expiry_time_iso: str

class RouteStopResponse(BaseModel):
    stop_id: str
    label: str
    lat: float
    lng: float
    arrival_time_seconds: int
    type: str

class RouteOptimizationResponse(BaseModel):
    route: List[RouteStopResponse]
    total_time_minutes: int
    distance_km: float
    solver_used: str

@router.post("/optimize-route", response_model=RouteOptimizationResponse)
def optimize_route(request: RouteOptimizationRequest):
    """
    Optimizes the delivery route for a volunteer to pick up food from a restaurant
    and drop it off at an NGO before the expiry time.
    """
    try:
        now = datetime.now(timezone.utc)
        expiry_time = datetime.fromisoformat(request.expiry_time_iso.replace('Z', '+00:00'))
        
        # Calculate time windows in seconds from now
        seconds_to_expiry = int((expiry_time - now).total_seconds())
        if seconds_to_expiry < 0:
            seconds_to_expiry = 0
            
        # Buffer for pickup: 20 minutes (1200 seconds)
        pickup_buffer_seconds = 1200
        
        # Stops configuration
        stops = [
            {
                "id": "depot",
                "label": "Volunteer Start",
                "lat": request.volunteer_location.lat,
                "lng": request.volunteer_location.lng,
                "type": "depot"
            },
            {
                "id": "restaurant",
                "label": request.restaurant.name or "Restaurant",
                "lat": request.restaurant.lat,
                "lng": request.restaurant.lng,
                "type": "pickup"
            },
            {
                "id": "ngo",
                "label": request.ngo.name or "NGO",
                "lat": request.ngo.lat,
                "lng": request.ngo.lng,
                "type": "dropoff"
            }
        ]
        
        # Time windows (earliest, latest)
        # Volunteer: can start immediately
        # Restaurant: pickup before (expiry - 20 mins)
        # NGO: dropoff before expiry
        time_windows = [
            (0, 24 * 3600), 
            (0, max(0, seconds_to_expiry - pickup_buffer_seconds)),
            (0, seconds_to_expiry)
        ]

        solver = VRPSolver()
        route = solver.solve(stops, time_windows)
        
        solver_used = "ortools"
        if not route or len(route) < len(stops):
            # In case OR-Tools drops stops due to impossible time windows
            solver_used = "fallback"
            route = solver.nearest_neighbor_heuristic(stops)

        # Calculate total time in minutes
        total_time_seconds = route[-1].get("arrival_time_seconds", 0) if route else 0
        total_time_minutes = total_time_seconds // 60
        
        # Calculate straight-line distance roughly for the response metadata
        total_distance_km = 0.0
        for i in range(1, len(route)):
            dist = solver.matrix_builder._haversine_distance(
                route[i-1]["lat"], route[i-1]["lng"],
                route[i]["lat"], route[i]["lng"]
            )
            total_distance_km += dist
            
        route_response = [
            RouteStopResponse(
                stop_id=r["id"],
                label=r["label"],
                lat=r["lat"],
                lng=r["lng"],
                arrival_time_seconds=r.get("arrival_time_seconds", 0),
                type=r["type"]
            ) for r in route
        ]
        
        return RouteOptimizationResponse(
            route=route_response,
            total_time_minutes=total_time_minutes,
            distance_km=round(total_distance_km, 2),
            solver_used=solver_used
        )
        
    except Exception as e:
        logger.error(f"Routing optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from typing import List, Dict, Any, Tuple

class NGOScorer:
    """
    Scores and ranks candidate NGOs for a given donation using a weighted, explainable formula.
    """

    def __init__(self, max_radius: float = 15.0):
        self.max_radius = max_radius

        # Weights
        self.w_distance = 0.35
        self.w_capacity = 0.25
        self.w_acceptance = 0.20
        self.w_speed = 0.20

    def score_ngo(self, donation: Any, ngo: Any, past_stats: Dict[str, Any]) -> float:
        """
        Calculates a score between 0.0 and 1.0 for a given NGO and donation.
        """
        breakdown = self.explain_score(donation, ngo, past_stats)
        return breakdown["final_score"]

    def explain_score(self, donation: Any, ngo: Any, past_stats: Dict[str, Any]) -> Dict[str, float]:
        """
        Returns the individual component scores and final score for transparency.
        Assumes 'ngo' has attributes: capacity, distance_km
        Assumes 'donation' has attributes: quantity
        """
        # 1. Distance Score
        distance_km = getattr(ngo, "distance_km", self.max_radius)
        # Prevent negative distance score if distance_km > max_radius
        clamped_distance = min(max(distance_km, 0.0), self.max_radius)
        distance_score = 1.0 - (clamped_distance / self.max_radius)

        # 2. Capacity Score
        ngo_capacity = float(getattr(ngo, "capacity", 0))
        donation_quantity = float(getattr(donation, "quantity", 1))
        # Prevent division by zero
        if donation_quantity <= 0:
            capacity_score = 1.0
        else:
            capacity_score = min(ngo_capacity / donation_quantity, 1.0)

        # 3. Acceptance Rate Score
        acceptance_rate = float(past_stats.get("acceptance_rate", 0.7))

        # 4. Delivery Speed Score
        avg_minutes = float(past_stats.get("avg_minutes", 45.0))
        # Clamp to avoid negative scores if > 90 mins
        clamped_minutes = min(max(avg_minutes, 0.0), 90.0)
        speed_score = 1.0 - (clamped_minutes / 90.0)

        # Final Score
        final_score = (
            (distance_score * self.w_distance) +
            (capacity_score * self.w_capacity) +
            (acceptance_rate * self.w_acceptance) +
            (speed_score * self.w_speed)
        )

        return {
            "distance_score": round(distance_score, 4),
            "capacity_score": round(capacity_score, 4),
            "acceptance_rate": round(acceptance_rate, 4),
            "delivery_speed": round(speed_score, 4),
            "final_score": round(final_score, 4)
        }

    def rank_ngos(self, donation: Any, ngo_list: List[Any], past_stats_dict: Dict[str, Dict[str, Any]]) -> List[Tuple[Any, float]]:
        """
        Scores all NGOs in the list and returns them sorted by score in descending order.
        past_stats_dict maps str(ngo.id) -> stats dict.
        """
        ranked = []
        for ngo in ngo_list:
            stats = past_stats_dict.get(str(ngo.id), {})
            score = self.score_ngo(donation, ngo, stats)
            ranked.append((ngo, score))
        
        # Sort descending by score
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

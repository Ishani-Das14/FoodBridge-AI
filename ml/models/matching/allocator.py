from typing import List, Dict, Tuple, Any

class GreedyAllocator:
    """
    Allocates a donation's quantity across a ranked list of candidate NGOs
    using a greedy knapsack approach.
    """
    
    @staticmethod
    def allocate(donation_quantity: float, ranked_ngos: List[Tuple[Any, float]]) -> List[Dict[str, Any]]:
        """
        Iterates over the ranked NGOs and assigns quantity until the donation is exhausted.
        
        Parameters
        ----------
        donation_quantity : float
            Total quantity to allocate
        ranked_ngos : list of (ngo_object, score)
            Candidate NGOs sorted by score descending
            
        Returns
        -------
        List of dicts:
            [
              {"ngo_id": 1, "allocated_quantity": 20, "score": 0.85},
              {"ngo_id": None, "unallocated": 5} # if remaining > 0 at end
            ]
        """
        result = []
        remaining = float(donation_quantity)
        
        for ngo, score in ranked_ngos:
            if remaining <= 0:
                break
                
            ngo_capacity = float(getattr(ngo, "capacity", 0))
            if ngo_capacity <= 0:
                continue
                
            allocated = min(ngo_capacity, remaining)
            
            result.append({
                "ngo_id": ngo.id,
                "allocated_quantity": allocated,
                "score": score
            })
            
            remaining -= allocated
            
        if remaining > 0:
            result.append({
                "ngo_id": None,
                "unallocated": remaining
            })
            
        return result

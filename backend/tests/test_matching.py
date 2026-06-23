import pytest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from backend.app.models import Donation, NGOProfile
from ml.models.matching.allocator import GreedyAllocator
from ml.models.matching.scorer import NGOScorer
from backend.app.services.emergency.service import EmergencyModeService

def test_rule_based_matching_single_ngo():
    ranked_ngos = [(NGOProfile(id=1, capacity=100), 0.9)]
    allocations = GreedyAllocator.allocate(donation_quantity=50, ranked_ngos=ranked_ngos)
    assert len(allocations) == 1
    assert allocations[0]["ngo_id"] == 1
    assert allocations[0]["allocated_quantity"] == 50
    assert allocations[0]["unallocated"] == 0

def test_rule_based_matching_split_across_ngos():
    ranked_ngos = [
        (NGOProfile(id=1, capacity=30), 0.9),
        (NGOProfile(id=2, capacity=20), 0.8),
        (NGOProfile(id=3, capacity=10), 0.7)
    ]
    allocations = GreedyAllocator.allocate(donation_quantity=50, ranked_ngos=ranked_ngos)
    assert len(allocations) == 2
    assert allocations[0]["ngo_id"] == 1
    assert allocations[0]["allocated_quantity"] == 30
    assert allocations[1]["ngo_id"] == 2
    assert allocations[1]["allocated_quantity"] == 20

def test_matching_no_ngos_in_radius():
    ranked_ngos = []
    allocations = GreedyAllocator.allocate(donation_quantity=50, ranked_ngos=ranked_ngos)
    assert len(allocations) == 1
    assert allocations[0]["ngo_id"] is None
    assert allocations[0]["allocated_quantity"] == 0
    assert allocations[0]["unallocated"] == 50

def test_ml_scorer_weights_sum_correctly():
    scorer = NGOScorer(max_radius=15.0)
    donation = type("Donation", (), {"quantity": 50})()
    ngo = type("NGOProfile", (), {"capacity": 100, "distance_km": 5.0})()
    past_stats = {"acceptance_rate": 0.8, "avg_minutes": 30}
    
    score = scorer.score_ngo(donation, ngo, past_stats)
    assert 0.0 <= score <= 1.0

def test_emergency_mode_expands_radius(test_client, db_session):
    # Deactivate first
    EmergencyModeService.deactivate(deactivated_by="test", db=db_session)
    assert EmergencyModeService.get_emergency_matching_radius() == 15.0
    
    # Activate
    EmergencyModeService.activate(reason="Test", affected_districts=["A"], activated_by="test", db=db_session)
    assert EmergencyModeService.get_emergency_matching_radius() == 50.0

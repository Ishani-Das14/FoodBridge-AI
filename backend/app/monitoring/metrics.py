from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# Custom Metrics
donations_created_total = Counter('donations_created_total', 'Total donations created', ['food_type'])
matches_made_total = Counter('matches_made_total', 'Total NGO matches made')
deliveries_completed_total = Counter('deliveries_completed_total', 'Total deliveries completed')
donations_expired_total = Counter('donations_expired_total', 'Total donations that expired unmatched')
ml_inference_latency_seconds = Histogram('ml_inference_latency_seconds', 'ML model inference time', ['model_name'])
active_volunteers_gauge = Gauge('active_volunteers_count', 'Currently available volunteers')
donation_to_match_seconds = Histogram('donation_to_match_seconds', 'Time from donation creation to match')

def setup_metrics(app):
    """
    Instruments the FastAPI app and exposes /metrics endpoint.
    """
    Instrumentator().instrument(app).expose(app)

# Helper Functions
def increment_donation_created(food_type: str):
    """
    INTEGRATION POINT:
    Call this in `create_donation` (backend/app/services/donation/service.py) 
    right after db.commit() for the new donation.
    Usage: increment_donation_created(donation.food_type)
    """
    donations_created_total.labels(food_type=food_type).inc()

def increment_match_made():
    """
    INTEGRATION POINT:
    Call this in `match_donation` (backend/app/services/matching/ml_service.py)
    inside the loop where new Matches are added to the db.
    Usage: increment_match_made()
    """
    matches_made_total.inc()
    
def record_ml_latency(model_name: str, seconds: float):
    """
    INTEGRATION POINT:
    Call this anywhere ML models are executed (e.g. `ml_service.py` scorer, `freshness_router.py`).
    Usage: record_ml_latency('freshness_xgboost', execution_time)
    """
    ml_inference_latency_seconds.labels(model_name=model_name).observe(seconds)

def set_active_volunteers(count: int):
    """
    INTEGRATION POINT:
    Call this periodically or on volunteer status change to update the live gauge.
    Usage: set_active_volunteers(active_count)
    """
    active_volunteers_gauge.set(count)
    
def increment_delivery_completed():
    """
    INTEGRATION POINT:
    Call this in `update_donation_status` (backend/app/services/donation/service.py)
    when new_status == 'delivered'.
    """
    deliveries_completed_total.inc()
    
def increment_donation_expired():
    """
    INTEGRATION POINT:
    Call this in `update_donation_status` (backend/app/services/donation/service.py)
    when new_status == 'expired'.
    """
    donations_expired_total.inc()
    
def observe_donation_to_match_time(seconds: float):
    """
    INTEGRATION POINT:
    Call this in `match_donation` (backend/app/services/matching/ml_service.py)
    after successfully creating a match, calculating time since donation creation.
    """
    donation_to_match_seconds.observe(seconds)

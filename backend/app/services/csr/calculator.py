import os
import sys
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from app.models import Donation, RestaurantProfile

class CSRCalculator:
    def calculate_score(self, restaurant_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculates the CSR score and badge tier for a given restaurant.
        """
        # Fetch all delivered donations for this restaurant
        delivered_donations = db.query(Donation).filter(
            Donation.restaurant_id == restaurant_id,
            Donation.status == 'delivered'
        ).all()

        if not delivered_donations:
            return {
                "score": 0,
                "badge": "Bronze",
                "total_meals": 0,
                "on_time_rate": 0.0,
                "consistency_streak": 0,
                "kg_saved": 0.0,
                "co2_saved_kg": 0.0
            }

        total_meals = sum(int(d.quantity) if str(d.quantity).isdigit() else 1 for d in delivered_donations)
        
        # Calculate on time rate
        on_time_count = sum(1 for d in delivered_donations if d.expiry_time and d.updated_at and d.updated_at <= d.expiry_time)
        on_time_rate = on_time_count / len(delivered_donations) if delivered_donations else 0.0

        # Calculate consistency streak
        # Get distinct dates of donations (any status, or just delivered)
        # Assuming consistency based on any donation created
        dates = db.query(func.date(Donation.created_at)).filter(
            Donation.restaurant_id == restaurant_id
        ).distinct().order_by(func.date(Donation.created_at).desc()).all()
        
        streak = 0
        if dates:
            dates = [d[0] for d in dates]
            import datetime
            today = datetime.date.today()
            current_date = dates[0]
            
            # If the last donation wasn't today or yesterday, streak is broken
            if (today - current_date).days > 1:
                streak = 0
            else:
                streak = 1
                for i in range(1, len(dates)):
                    if (dates[i-1] - dates[i]).days == 1:
                        streak += 1
                    else:
                        break

        # Calculate score
        score = (total_meals * 2) + (on_time_rate * 20) + (streak * 0.5)

        # Determine badge
        if score >= 1000:
            badge = "Platinum"
        elif score >= 500:
            badge = "Gold"
        elif score >= 200:
            badge = "Silver"
        else:
            badge = "Bronze"

        # Conversion metrics
        kg_saved = total_meals * 0.4
        co2_saved_kg = kg_saved * 2.5

        return {
            "score": round(score, 2),
            "badge": badge,
            "total_meals": total_meals,
            "on_time_rate": round(on_time_rate, 2),
            "consistency_streak": streak,
            "kg_saved": round(kg_saved, 2),
            "co2_saved_kg": round(co2_saved_kg, 2)
        }

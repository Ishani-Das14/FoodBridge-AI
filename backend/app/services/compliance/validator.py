from datetime import datetime, timezone

class FSSAIValidator:
    def validate_license_format(self, license_number: str) -> bool:
        """
        FSSAI license must be exactly 14 digits, numeric only.
        """
        if not license_number:
            return False
        return len(license_number) == 14 and license_number.isdigit()

    def validate_donation_safety(self, food_type: str, prep_time: datetime, expiry_minutes: int) -> dict:
        """
        FOOD SAFETY RULES (FSSAI guidelines for cooked food):
        - Rice/Biryani: max safe window = 4 hours (240 min) from prep_time
        - Dal/Curry: max safe window = 6 hours (360 min)
        - Roti/Bread: max safe window = 8 hours (480 min)
        - Mixed: max safe window = 3 hours (180 min)
        """
        food_type_lower = food_type.lower()
        if "rice" in food_type_lower or "biryani" in food_type_lower:
            max_safe_window_hours = 4
        elif "dal" in food_type_lower or "curry" in food_type_lower:
            max_safe_window_hours = 6
        elif "roti" in food_type_lower or "bread" in food_type_lower:
            max_safe_window_hours = 8
        elif "mixed" in food_type_lower:
            max_safe_window_hours = 3
        else:
            # Default conservative
            max_safe_window_hours = 3
            
        now = datetime.utcnow()
        # prep_time might be naive or aware, making sure we handle correctly. 
        # For this we assume prep_time is naive UTC as per typical datetime.utcnow() usage.
        hours_since_prep = (now - prep_time).total_seconds() / 3600.0

        if hours_since_prep > max_safe_window_hours:
            return {
                "is_compliant": False, 
                "reason": f"{food_type} exceeds FSSAI safe consumption window of {max_safe_window_hours} hours"
            }
        
        return {
            "is_compliant": True, 
            "reason": "Within FSSAI safety guidelines"
        }

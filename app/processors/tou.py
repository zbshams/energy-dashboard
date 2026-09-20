from datetime import datetime

def is_weekend(date_str):
    """Check if date is weekend (M/D/Y format)"""
    date_obj = datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.weekday() >= 5  # 5=Saturday, 6=Sunday

def tou_class(hour, is_wknd):
    """Determine TOU class for an hour"""
    if hour >= 0 and hour < 6:
        return "sop"  # Super Off-Peak: 12am-6am
    elif hour >= 14 and hour < 18 and not is_wknd:  # 2pm-6pm weekdays
        return "pk"  # Peak
    else:
        return "op"  # Off-Peak

def get_active_rate(date_str, rates_schedule):
    """Get active rate period for a date"""
    date_obj = datetime.strptime(date_str, "%m/%d/%Y")
    active_rate = None
    for rate_date_str in sorted(rates_schedule.keys()):
        rate_date = datetime.strptime(rate_date_str, "%Y-%m-%d")
        if rate_date <= date_obj:
            active_rate = rates_schedule[rate_date_str]
    return active_rate or rates_schedule[sorted(rates_schedule.keys())[0]]

def calculate_tou_costs(hourly_data, dates, rates_schedule):
    """Calculate TOU costs for hourly data"""
    costs = {}
    
    for i, date_str in enumerate(dates):
        day_cost = 0
        is_wknd = is_weekend(date_str)
        active_rate = get_active_rate(date_str, rates_schedule)
        
        for hour in range(24):
            tou = tou_class(hour, is_wknd)
            if "all" in active_rate:
                rate = active_rate["all"]
            else:
                rate = active_rate.get(tou, 0.10)
            
            # Sum usage across all devices for this hour
            hour_usage = 0
            for device_values in hourly_data.values():
                if isinstance(device_values, list) and i * 24 + hour < len(device_values):
                    hour_usage += device_values[i * 24 + hour]
            
            day_cost += hour_usage * rate
        
        costs[date_str] = day_cost
    
    return costs

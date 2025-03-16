from datetime import datetime, timezone

def get_interval_in_minutes(interval):
    """Converts time interval (like 1m, 5m, 1H, 1D) to minutes."""
    interval_mapping = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1H": 60,
        "2H": 120,
        "4H": 240,
        "6H": 360,
        "8H": 480,
        "12H": 720,
        "1D": 1440,
        "3D": 4320,
        "1W": 10080,
        "1M": 43200  # Assuming 30 days in a month
    }
    
    return interval_mapping.get(interval, None)  # Returns None if the interval is invalid

def get_time_features(unix_time):
    """Extracts minute of the day and day of the week from a Unix timestamp in UTC."""
    utc_dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    minute_of_day = utc_dt.hour * 60 + utc_dt.minute
    day_of_week = utc_dt.weekday()
    return {"minute_of_day": minute_of_day, "day_of_week": day_of_week}

def calculate_token_age(price_data):
    """Calculates token age in minutes from earliest to latest entry."""
    if not price_data or len(price_data) < 1:
        return 0.0
    earliest_time = price_data[0]["unixTime"]
    current_time = price_data[-1]["unixTime"]
    age_seconds = current_time - earliest_time
    return max(0.0, age_seconds / 60.0)


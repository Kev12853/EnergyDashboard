def format_data_age(minutes):

    if minutes < 1:
        return f"{minutes * 60:.0f} seconds"

    if minutes < 60:
        return f"{minutes:.0f} minutes"

    if minutes < 1440:
        return f"{minutes / 60:.1f} hours"

    return f"{minutes / 1440:.1f} days"
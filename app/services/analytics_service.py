from app.repositories import analytics_repository



def get_summary():
    """Return a summary of transaction statistics."""
    return analytics_repository.get_summary()

def get_hourly_summary():
    """Return transaction counts grouped by hour."""
    return analytics_repository.get_hourly_summary()

from datetime import datetime

def fmt(dt):
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime("%d.%m.%Y %H:%M:%S")

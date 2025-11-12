# app/controllers/_datetime_helpers.py
from datetime import datetime, UTC
from zoneinfo import ZoneInfo

REYKJAVIK = ZoneInfo("Atlantic/Reykjavik")
DT_LOCAL_FMT = "%Y-%m-%dT%H:%M"  # from <input type="datetime-local">

def parse_local_to_utc(value: str):
    if not value:
        return None
    local_dt = datetime.strptime(value, DT_LOCAL_FMT)
    local_dt = local_dt.replace(tzinfo=REYKJAVIK)
    # strip seconds for minute precision
    local_dt = local_dt.replace(second=0, microsecond=0)
    return local_dt.astimezone(UTC)

def utc_to_local_minutes(dt_utc):
    if not dt_utc:
        return ""
    dt_local = dt_utc.astimezone(REYKJAVIK).replace(second=0, microsecond=0)
    return dt_local.strftime(DT_LOCAL_FMT)

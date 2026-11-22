import sys
from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

def to_sec(t):
    h, m, s = t.str.split(":", expand=True).astype(int).T.values
    return h * 3600 + m * 60 + s

for feed in ["A", "M", "T"]:
    d = RAW / feed
    stops = pd.read_csv(d / "stops.txt", dtype=str)
    routes = pd.read_csv(d / "routes.txt", dtype=str)
    trips = pd.read_csv(d / "trips.txt", dtype=str)
    st = pd.read_csv(d / "stop_times.txt", dtype=str, usecols=["trip_id", "stop_id", "departure_time"])
    cal = pd.read_csv(d / "calendar.txt", dtype=str)
    st["sec"] = to_sec(st["departure_time"])
    night = st[(st.sec % 86400 >= 0) & (st.sec % 86400 < 4 * 3600)]
    print(f"\n=== {feed} ===")
    print(f"stops: {len(stops)} (unique names: {stops.stop_name.nunique()})")
    print(f"routes: {len(routes)}  trips: {len(trips)}  stop_times: {len(st)}")
    print(f"route_types: {routes.route_type.value_counts().to_dict()}")
    print(f"calendar: {cal.start_date.min()} -> {cal.end_date.max()}, services: {len(cal)}")
    print(f"bbox lat {stops.stop_lat.astype(float).min():.3f}-{stops.stop_lat.astype(float).max():.3f}, "
          f"lon {stops.stop_lon.astype(float).min():.3f}-{stops.stop_lon.astype(float).max():.3f}")
    print(f"night departures 00-04: {len(night)} at {night.stop_id.nunique()} stops")
    print("busiest stops:", st.merge(stops, on="stop_id").stop_name.value_counts().head(5).to_dict())

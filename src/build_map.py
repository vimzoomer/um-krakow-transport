import sys
from pathlib import Path
import pandas as pd
import folium
from branca.colormap import LinearColormap

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "out"
OUT.mkdir(parents=True, exist_ok=True)
DATE = sys.argv[1] if len(sys.argv) > 1 else "20261124"
FEEDS = {"A": ("Autobusy MPK", "#1f6fd1"), "M": ("Autobusy Mobilis", "#2a9d5c"), "T": ("Tramwaje", "#d62828")}


def load(feed):
    d = RAW / feed
    r = lambda n, **kw: pd.read_csv(d / n, dtype=str, **kw)
    cd = r("calendar_dates.txt")
    services = set(cd[(cd.date == DATE) & (cd.exception_type == "1")].service_id)
    trips = r("trips.txt")
    trips = trips[trips.service_id.isin(services)]
    st = r("stop_times.txt", usecols=["trip_id", "stop_id", "departure_time"])
    st = st[st.trip_id.isin(trips.trip_id)].merge(trips[["trip_id", "route_id"]], on="trip_id")
    hms = st.departure_time.str.split(":", expand=True).astype(int)
    st["hour"] = (hms[0] + hms[1] / 60) % 24
    stops = r("stops.txt")
    routes = r("routes.txt")
    st = st.merge(stops[["stop_id", "stop_code", "stop_name", "stop_lat", "stop_lon"]], on="stop_id")
    st = st.merge(routes[["route_id", "route_short_name"]], on="route_id")
    st["feed"] = feed
    shapes = r("shapes.txt")
    top_shape = trips.groupby("route_id").shape_id.agg(lambda s: s.value_counts().index[0])
    lines = []
    for route_id, shape_id in top_shape.items():
        pts = shapes[shapes.shape_id == shape_id].copy()
        pts["seq"] = pts.shape_pt_sequence.astype(int)
        pts = pts.sort_values("seq")
        name = routes.loc[routes.route_id == route_id, "route_short_name"].iloc[0]
        lines.append((name, list(zip(pts.shape_pt_lat.astype(float), pts.shape_pt_lon.astype(float)))))
    return st, lines


frames, all_lines = [], {}
for f in FEEDS:
    st, lines = load(f)
    frames.append(st)
    all_lines[f] = lines
st = pd.concat(frames)
st["group"] = st.stop_code.str.split("-").str[0]
st["lat"] = st.stop_lat.astype(float)
st["lon"] = st.stop_lon.astype(float)

g = st.groupby("group").agg(
    name=("stop_name", "first"),
    lat=("lat", "mean"),
    lon=("lon", "mean"),
    total=("trip_id", "size"),
    peak=("hour", lambda h: ((h >= 7) & (h < 9)).sum() / 2),
    night=("hour", lambda h: (h < 4).sum()),
    lines=("route_short_name", lambda s: ", ".join(sorted(s.unique(), key=lambda x: (len(x), x)))),
    modes=("feed", lambda s: "".join(sorted(s.unique()))),
).reset_index()
g.to_csv(OUT / f"stop_groups_{DATE}.csv", index=False)

m = folium.Map(location=[50.06, 19.94], zoom_start=12, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", attr="Tiles © Esri — Esri, DeLorme, NAVTEQ")
for f, (label, color) in FEEDS.items():
    fg = folium.FeatureGroup(name=f"Trasy: {label}", show=(f == "T"))
    for name, coords in all_lines[f]:
        folium.PolyLine(coords, color=color, weight=2, opacity=0.6, tooltip=f"{label} {name}").add_to(fg)
    fg.add_to(m)

cm = LinearColormap(["#d73027", "#fc8d59", "#fee08b", "#91cf60", "#1a9850"], vmin=0, vmax=60,
                    caption="Odjazdy / h w szczycie 7–9 (wszystkie linie)")
peak_fg = folium.FeatureGroup(name="Przystanki: częstotliwość w szczycie", show=True)
for row in g.itertuples():
    folium.CircleMarker(
        [row.lat, row.lon], radius=3 + min(row.peak, 80) ** 0.5,
        color=cm(min(row.peak, 60)), fill=True, fill_opacity=0.85, weight=0,
        tooltip=f"<b>{row.name}</b><br>szczyt: {row.peak:.0f}/h<br>doba: {row.total}<br>noc 0–4: {row.night}<br>linie: {row.lines}",
    ).add_to(peak_fg)
peak_fg.add_to(m)
cm.add_to(m)

night_fg = folium.FeatureGroup(name="Noc 0–4: brak odjazdów (czarne)", show=False)
for row in g[g.night == 0].itertuples():
    folium.CircleMarker([row.lat, row.lon], radius=3, color="#222", fill=True, fill_opacity=0.8, weight=0,
                        tooltip=f"{row.name}: brak kursów nocnych").add_to(night_fg)
night_fg.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
path = OUT / f"mapa_{DATE}.html"
m.save(path)
print(path)
print(f"grup przystanków: {len(g)}, bez kursów nocnych: {(g.night == 0).sum()}, "
      f"< 4 odjazdy/h w szczycie: {(g.peak < 4).sum()}")
print(g.sort_values("peak", ascending=False).head(5)[["name", "peak", "night", "modes"]].to_string(index=False))

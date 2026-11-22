# Kraków Public Transport Analysis

Machine Learning 26/27 project: analysing public transport accessibility in Kraków using GTFS data from [ZTP Kraków](https://gtfs.ztp.krakow.pl/) (CC BY 4.0).

## Usage

```bash
uv sync
uv run python src/download_gtfs.py
uv run python src/explore_gtfs.py
uv run python src/build_map.py 20261124
open data/out/mapa_20261124.html
```

## Data

- `A` – MPK buses
- `M` – Mobilis buses
- `T` – trams

`build_map.py <YYYYMMDD>` computes, for every stop, the number of departures per hour in the 7–9 peak, per day, and at night (0–4). It saves the result to `data/out/stop_groups_<date>.csv` and generates an interactive map at `data/out/mapa_<date>.html`.

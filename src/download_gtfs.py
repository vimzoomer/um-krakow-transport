import zipfile
from pathlib import Path
from urllib.request import urlretrieve

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
BASE = "https://gtfs.ztp.krakow.pl"

RAW.mkdir(parents=True, exist_ok=True)
for feed in ["A", "M", "T"]:
    zip_path = RAW / f"GTFS_KRK_{feed}.zip"
    urlretrieve(f"{BASE}/GTFS_KRK_{feed}.zip", zip_path)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(RAW / feed)
    print(f"{feed}: {zip_path}")

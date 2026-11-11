"""Regenerate the visibly simulated data used in the offline classroom demo."""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(3003)
STATIONS = [
    ("MED-BEME · Belén", "Medellín", 6.23, -75.59, 8.0),
    ("MED-ALTA · El Poblado", "Medellín", 6.19, -75.56, 15.0),
    ("MED-UNNV · Universidad", "Medellín", 6.27, -75.57, 28.0),
    ("ITA-CONC · Itagüí", "Itagüí", 6.17, -75.61, 10.0),
    ("SAB-CJUS · Sabaneta", "Sabaneta", 6.15, -75.62, 21.0),
    ("COP-CIED · Copacabana", "Copacabana", 6.35, -75.51, 31.0),
]


def main() -> None:
    output = Path(__file__).parent / "data" / "demo_air_quality.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    start = date(2026, 10, 1)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["fecha", "estacion", "municipio", "latitud", "longitud", "pm25"])
        for day in range(35):
            for name, city, lat, lon, base in STATIONS:
                value = base + 2 * math.sin(day / 4 + base) + math.cos(day / 6) + random.gauss(0, .8)
                writer.writerow([(start + timedelta(days=day)).isoformat(), name, city, lat, lon, round(max(3, min(36, value)), 1)])
    print(f"Datos de demostración escritos en {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
generate_solar_data.py — Tutorial T7.2 resource
================================================
Generates a synthetic CSV of hourly solar generation data for use in the
simulated probe interface.

The output contains four columns:

    timestamp         ISO 8601 datetime (hourly)
    cloud_cover       0–100 %  (autocorrelated random series)
    uv_index          0–11     (clear-sky estimate from solar geometry)
    generation_index  0–100    (derived: see formula below)

The generation_index mirrors the formula used in the probe interface:

    generation_index = max(0, (1 − cloud_cover/100) × (uv_index/11) × 100)

Parameters shape the output within plausible bounds for the chosen location
and season. The script does not model atmospheric aerosols, terrain shading,
or panel efficiency — it is a teaching tool, not a simulation.

Usage examples
--------------
# Defaults: Delft, summer, 7 days, seed 42
python generate_solar_data.py

# Winter week in Paris
python generate_solar_data.py --lat 48.85 --lon 2.35 --season winter

# Two weeks in Edinburgh, spring, different seed each run
python generate_solar_data.py --lat 55.95 --lon -3.19 --season spring --days 14 --seed 0

# Full help
python generate_solar_data.py --help

Dependencies
------------
None beyond the Python standard library (math, csv, random, argparse, datetime).
"""

import argparse
import csv
import math
import random
from datetime import date, datetime, timedelta


# ---------------------------------------------------------------------------
# Season presets
# ---------------------------------------------------------------------------
# doy          Representative day-of-year (used for solar geometry only).
# cloud_mean   Mean cloud cover (%) for this season and a mid-latitude
#              Northern European location (~50–55 °N). Adjust for other
#              regions by passing --cloud-mean on the command line.
# cloud_std    Standard deviation of cloud cover (%).

SEASONS: dict[str, dict] = {
    "spring": {"doy": 91,  "cloud_mean": 63, "cloud_std": 22},  # ~1 April
    "summer": {"doy": 172, "cloud_mean": 52, "cloud_std": 26},  # ~21 June
    "autumn": {"doy": 274, "cloud_mean": 70, "cloud_std": 20},  # ~1 October
    "winter": {"doy": 355, "cloud_mean": 80, "cloud_std": 16},  # ~21 December
}

# First day of each season (month, day) — used to set output timestamps.
SEASON_START: dict[str, tuple[int, int]] = {
    "spring": (3, 20),
    "summer": (6, 21),
    "autumn": (9, 23),
    "winter": (12, 21),
}


# ---------------------------------------------------------------------------
# Solar geometry
# ---------------------------------------------------------------------------

def _declination(doy: int) -> float:
    """Solar declination angle in radians for a given day-of-year."""
    return math.radians(23.45 * math.sin(math.radians(360 / 365 * (doy - 81))))


def _elevation(lat_rad: float, decl: float, solar_hour: float) -> float:
    """
    Solar elevation angle in radians.

    lat_rad    Latitude in radians.
    decl       Solar declination in radians (from _declination).
    solar_hour Local solar time in decimal hours (12.0 = solar noon).
    """
    hour_angle = math.radians((solar_hour - 12.0) * 15.0)
    sin_elev = (
        math.sin(lat_rad) * math.sin(decl)
        + math.cos(lat_rad) * math.cos(decl) * math.cos(hour_angle)
    )
    # Clamp to [-1, 1] to guard against floating-point drift at the horizon.
    return math.asin(max(-1.0, min(1.0, sin_elev)))


def _uv_clear_sky(elev_rad: float, lat_deg: float) -> float:
    """
    Approximate clear-sky UV index from solar elevation angle.

    Returns 0 when the sun is below the horizon. At higher latitudes the
    atmosphere path length is longer, so the peak UV index is attenuated.
    Values are consistent with WHO-reported ranges for Northern Europe:
    ~1–2 in Dutch winter, ~5–7 in Dutch summer.
    """
    if elev_rad <= 0.0:
        return 0.0
    lat_factor = max(0.25, 1.0 - abs(lat_deg) / 90.0 * 0.55)
    uv = 11.0 * lat_factor * math.sin(elev_rad)
    return round(min(11.0, max(0.0, uv)), 2)


# ---------------------------------------------------------------------------
# Cloud cover time series
# ---------------------------------------------------------------------------

def _cloud_series(
    n: int,
    mean: float,
    std: float,
    ar: float = 0.88,
    rng=None,  # random.Random or None
) -> list:
    """
    Autocorrelated hourly cloud cover series (0–100 %).

    Uses an AR(1) process so the sky changes gradually rather than jumping
    between independent random values each hour.

    ar    Autocorrelation coefficient. 0 = independent; 1 = never changes.
          0.88 means roughly 8–10 hours for a change to fully propagate,
          which matches observed cloud persistence at mid-latitudes.
    """
    if rng is None:
        rng = random.Random()
    # Noise standard deviation adjusted so the long-run variance matches `std`.
    noise_std = std * math.sqrt(1.0 - ar ** 2)
    series = [max(0.0, min(100.0, rng.gauss(mean, std)))]
    for _ in range(n - 1):
        next_val = mean + ar * (series[-1] - mean) + rng.gauss(0.0, noise_std)
        series.append(max(0.0, min(100.0, next_val)))
    return series


# ---------------------------------------------------------------------------
# Generation index
# ---------------------------------------------------------------------------

def _gen_index(cloud_pct: float, uv: float) -> float:
    """
    Normalised solar generation index (0–100).

    Mirrors the formula used in the probe interface so that students can
    verify that the script and the interface agree:

        max(0, (1 − cloud_cover / 100) × (uv_index / 11) × 100)
    """
    return round(max(0.0, (1.0 - cloud_pct / 100.0) * (uv / 11.0) * 100.0), 1)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate(
    lat: float,
    lon: float,
    season: str,
    days: int,
    seed: int,
    start: date,
    cloud_mean=None,  # float or None
) -> list[dict]:
    """
    Return a list of hourly row dicts.

    cloud_mean overrides the season preset when provided, allowing fine-tuning
    for locations where the preset is a poor fit (e.g. Mediterranean summers).
    """
    params = SEASONS[season]
    decl   = _declination(params["doy"])
    lat_r  = math.radians(lat)
    mean   = cloud_mean if cloud_mean is not None else params["cloud_mean"]
    rng    = random.Random(seed)

    n_hours  = days * 24
    cloud_ts = _cloud_series(n_hours, mean, params["cloud_std"], rng=rng)

    rows = []
    for h in range(n_hours):
        dt = datetime(start.year, start.month, start.day) + timedelta(hours=h)

        # Convert UTC clock to approximate solar time by shifting for longitude.
        # One hour ≈ 15° of longitude; this ignores the equation of time (~±16 min).
        solar_hour = dt.hour + dt.minute / 60.0 + lon / 15.0

        elev = _elevation(lat_r, decl, solar_hour)
        uv   = _uv_clear_sky(elev, lat)
        cc   = cloud_ts[h]
        gi   = _gen_index(cc, uv)

        rows.append({
            "timestamp":        dt.strftime("%Y-%m-%dT%H:%M"),
            "cloud_cover":      round(cc, 1),
            "uv_index":         uv,
            "generation_index": gi,
        })
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic hourly solar generation data for tutorial T7.2.\n"
            "Output is a CSV with columns: timestamp, cloud_cover, uv_index, generation_index."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lat", type=float, default=52.0,
        metavar="DEGREES",
        help="Latitude in decimal degrees, positive = North  (default: 52.0 — Delft)",
    )
    parser.add_argument(
        "--lon", type=float, default=4.36,
        metavar="DEGREES",
        help="Longitude in decimal degrees, positive = East  (default: 4.36 — Delft)",
    )
    parser.add_argument(
        "--season", choices=list(SEASONS), default="summer",
        help="Season preset that sets solar geometry and cloud statistics  (default: summer)",
    )
    parser.add_argument(
        "--days", type=int, default=7,
        metavar="N",
        help="Number of days to generate  (default: 7)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help=(
            "Random seed. Use the same seed to reproduce identical output; "
            "use 0 for a different series each run  (default: 42)"
        ),
    )
    parser.add_argument(
        "--year", type=int, default=2025,
        help="Calendar year for output timestamps  (default: 2025)",
    )
    parser.add_argument(
        "--cloud-mean", type=float, default=None,
        metavar="PCT",
        help=(
            "Override the season preset's mean cloud cover (0–100 %%). "
            "Useful for locations where the Northern Europe preset is a poor fit."
        ),
    )
    parser.add_argument(
        "--output", type=str, default="weather_sample.csv",
        metavar="FILE",
        help="Output CSV filename  (default: weather_sample.csv)",
    )

    args   = parser.parse_args()
    m, d   = SEASON_START[args.season]
    start  = date(args.year, m, d)
    seed   = args.seed if args.seed != 0 else random.randint(1, 2**31)
    rows   = generate(args.lat, args.lon, args.season, args.days, seed, start, args.cloud_mean)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "cloud_cover", "uv_index", "generation_index"]
        )
        writer.writeheader()
        writer.writerows(rows)

    # Summary printed to stdout so students can verify the parameters at a glance.
    n_daylight = sum(1 for r in rows if r["uv_index"] > 0)
    peak_row   = max(rows, key=lambda r: r["generation_index"])
    print(f"Written {len(rows)} rows ({args.days} days × 24 h) to '{args.output}'")
    print(f"  Location    : {args.lat}°N, {args.lon}°E")
    print(f"  Season      : {args.season}  (timestamps start {start})")
    print(f"  Seed        : {seed}")
    print(f"  Daylight hrs: {n_daylight} / {len(rows)}")
    print(f"  Peak index  : {peak_row['generation_index']:.0f}  at {peak_row['timestamp']}")


if __name__ == "__main__":
    main()

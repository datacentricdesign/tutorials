"""Generate a synthetic Spotify streaming history for testing the data donation campaign."""

import json
import random
from datetime import datetime, timedelta

random.seed(42)

ARTISTS = [
    ("Radiohead", ["OK Computer", "Kid A", "In Rainbows"]),
    ("Beyoncé", ["Lemonade", "Renaissance", "4"]),
    ("Kendrick Lamar", ["To Pimp a Butterfly", "DAMN.", "Mr. Morale"]),
    ("Björk", ["Homogenic", "Vespertine", "Vulnicura"]),
    ("Frank Ocean", ["Blonde", "Channel Orange"]),
    ("Mitski", ["Puberty 2", "Be the Cowboy", "Laurel Hell"]),
    ("Nick Drake", ["Pink Moon", "Bryter Layter"]),
    ("Arooj Aftab", ["Vulture Prince", "Night Reign"]),
    ("James Blake", ["James Blake", "Overgrown", "Friends That Break Your Heart"]),
    ("Solange", ["A Seat at the Table", "When I Get Home"]),
    ("The National", ["Sleep Well Beast", "I Am Easy to Find"]),
    ("SZA", ["CTRL", "SOS"]),
    ("Sufjan Stevens", ["Carrie & Lowell", "Illinois"]),
    ("FKA twigs", ["LP1", "Magdalene"]),
    ("Massive Attack", ["Mezzanine", "Blue Lines"]),
]

TRACKS = {
    "Radiohead": [
        ("Karma Police", 264000), ("Creep", 238000), ("Fake Plastic Trees", 285000),
        ("No Surprises", 228000), ("Everything in Its Right Place", 265000),
        ("How to Disappear Completely", 355000), ("Idioteque", 261000),
    ],
    "Beyoncé": [
        ("Lemonade", 222000), ("Formation", 213000), ("Crazy in Love", 235000),
        ("Halo", 261000), ("CUFF IT", 218000), ("BREAK MY SOUL", 261000),
    ],
    "Kendrick Lamar": [
        ("HUMBLE.", 177000), ("Alright", 219000), ("Money Trees", 386000),
        ("Swimming Pools", 314000), ("King Kunta", 234000), ("DNA.", 185000),
    ],
    "Björk": [
        ("Jóga", 298000), ("All Is Full of Love", 271000), ("Hyperballad", 300000),
        ("Army of Me", 197000), ("Hidden Place", 332000),
    ],
    "Frank Ocean": [
        ("Nights", 307000), ("Pink + White", 183000), ("Thinkin Bout You", 200000),
        ("Self Control", 249000), ("Super Rich Kids", 283000),
    ],
    "Mitski": [
        ("Nobody", 199000), ("Your Best American Girl", 231000), ("Washing Machine Heart", 175000),
        ("First Love / Late Spring", 254000), ("Be the Cowboy", 185000),
    ],
    "Nick Drake": [
        ("Pink Moon", 129000), ("Place to Be", 173000), ("Road", 164000),
        ("Hazey Jane II", 212000), ("Northern Sky", 203000),
    ],
    "Arooj Aftab": [
        ("Mohabbat", 282000), ("Last Night", 411000), ("Saans Lo", 349000),
        ("Udhero Na", 264000), ("Diya Hai", 218000),
    ],
    "James Blake": [
        ("Retrograde", 248000), ("The Wilhelm Scream", 239000), ("Limit to Your Love", 237000),
        ("Measurements", 215000), ("Life Is Not the Same", 193000),
    ],
    "Solange": [
        ("Cranes in the Sky", 228000), ("Don't Touch My Hair", 256000), ("Mad", 197000),
        ("Things I Imagined", 172000), ("Stay Flo", 223000),
    ],
    "The National": [
        ("Bloodbuzz Ohio", 231000), ("Sorrow", 243000), ("England", 292000),
        ("Terrible Love", 267000), ("I Need My Girl", 210000),
    ],
    "SZA": [
        ("Good Days", 370000), ("Kill Bill", 154000), ("Snooze", 216000),
        ("Garden (Say It Like Dat)", 223000), ("20 Something", 204000),
    ],
    "Sufjan Stevens": [
        ("Death With Dignity", 227000), ("Should Have Known Better", 277000),
        ("Fourth of July", 363000), ("Chicago", 400000), ("Casimir Pulaski Day", 322000),
    ],
    "FKA twigs": [
        ("Two Weeks", 225000), ("Cellophane", 315000), ("Magdalene", 327000),
        ("Sad Day", 189000), ("Water Me", 173000),
    ],
    "Massive Attack": [
        ("Teardrop", 330000), ("Unfinished Sympathy", 296000), ("Angel", 382000),
        ("Safe from Harm", 390000), ("Paradise Circus", 330000),
    ],
}

PLATFORMS = ["Android", "iOS", "Windows", "macOS", "web player"]
REASONS = ["trackdone", "fwdbtn", "backbtn", "endplay", "clickrow", "playbtn"]


def weighted_hour():
    """Return a realistic listening hour (peaks: morning commute, evening)."""
    weights = [
        1, 1, 1, 1, 1, 2,   # 00–05
        4, 6, 5, 3, 3, 3,   # 06–11
        4, 4, 3, 3, 4, 5,   # 12–17
        7, 8, 7, 5, 3, 2,   # 18–23
    ]
    return random.choices(range(24), weights=weights)[0]


def generate_entries(n=600, start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime(2024, 4, 1)
    if end_date is None:
        end_date = datetime(2025, 3, 31)

    span = (end_date - start_date).days
    entries = []

    # Artist weights — simulate a real user's taste with 3–4 favourites
    artist_weights = [5, 4, 3, 3, 4, 4, 2, 3, 2, 2, 3, 4, 2, 2, 2]

    platform = random.choice(PLATFORMS)

    for _ in range(n):
        artist_name, albums = random.choices(ARTISTS, weights=artist_weights)[0]
        album = random.choice(albums)
        track_name, duration = random.choice(TRACKS[artist_name])

        day_offset = random.randint(0, span)
        ts = start_date + timedelta(
            days=day_offset,
            hours=weighted_hour(),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        skipped = random.random() < 0.15
        ms_played = random.randint(5000, min(30000, duration)) if skipped else duration

        entries.append({
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "username": "synthetic_user",
            "platform": platform,
            "ms_played": ms_played,
            "conn_country": "NL",
            "ip_addr_decrypted": None,
            "user_agent_decrypted": None,
            "master_metadata_track_name": track_name,
            "master_metadata_album_artist_name": artist_name,
            "master_metadata_album_album_name": album,
            "spotify_track_uri": f"spotify:track:synthetic{random.randint(10000,99999)}",
            "episode_name": None,
            "episode_show_name": None,
            "spotify_episode_uri": None,
            "reason_start": random.choice(REASONS),
            "reason_end": random.choice(REASONS),
            "shuffle": random.random() < 0.4,
            "skipped": skipped,
            "offline": random.random() < 0.05,
            "offline_timestamp": None,
            "incognito_mode": False,
        })

    entries.sort(key=lambda e: e["ts"])
    return entries


def generate_legacy_entries(n=600, start_date=None, end_date=None):
    """Legacy format: endTime, artistName, trackName, msPlayed."""
    extended = generate_entries(n, start_date, end_date)
    return [
        {
            "endTime": e["ts"][:16].replace("T", " "),
            "artistName": e["master_metadata_album_artist_name"],
            "trackName": e["master_metadata_track_name"],
            "msPlayed": e["ms_played"],
        }
        for e in extended
    ]


if __name__ == "__main__":
    # Extended format (modern Spotify export)
    entries_extended = generate_entries(700)
    with open("synthetic_spotify_extended.json", "w") as f:
        json.dump(entries_extended, f, indent=2)
    print(f"Extended format: {len(entries_extended)} entries → synthetic_spotify_extended.json")

    # Legacy format
    entries_legacy = generate_legacy_entries(700)
    with open("synthetic_spotify_legacy.json", "w") as f:
        json.dump(entries_legacy, f, indent=2)
    print(f"Legacy format:   {len(entries_legacy)} entries → synthetic_spotify_legacy.json")

    # Summary
    artists = {}
    for e in entries_extended:
        a = e["master_metadata_album_artist_name"]
        artists[a] = artists.get(a, 0) + 1
    print("\nTop 5 artists:")
    for a, c in sorted(artists.items(), key=lambda x: -x[1])[:5]:
        print(f"  {a}: {c} plays")

    total_hours = sum(e["ms_played"] for e in entries_extended) / 3_600_000
    print(f"\nTotal listening: {total_hours:.1f} hours")
    dates = [e["ts"][:10] for e in entries_extended]
    print(f"Date range: {min(dates)} → {max(dates)}")
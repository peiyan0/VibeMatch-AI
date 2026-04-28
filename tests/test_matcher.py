"""Smoke test for matcher (no video needed) and analyzer import check."""
# ── Matcher test ────────────────────────────────────────────────────────────
from src.matcher import MusicMatcher

matcher = MusicMatcher()
print("Weights:", matcher.weights)

video_data = {
    "target_bpm":    120.0,
    "mood":          "Bright/Optimistic",
    "keywords":      ["travel vlog", "bright", "energetic", "cinematic"],
    "motion_energy": 0.7,
}

fake_tracks = [
    {
        "id": "fs_001", "title": "Summer Vibes Loop",  "artist": "SunUser",
        "genre": "Ambient", "mood": "Bright/Optimistic",
        "bpm": 121.0, "duration": 45.0,
        "tags": ["summer", "bright", "upbeat", "travel", "loop"],
        "url": "https://freesound.org/s/1/", "preview_url": None,
        "license": "CC0", "attribution": "No attribution required.",
        "source": "Freesound",
    },
    {
        "id": "fs_002", "title": "Dark Forest",  "artist": "MoodUser",
        "genre": "Ambient", "mood": "Dark/Atmospheric",
        "bpm": 72.0, "duration": 90.0,
        "tags": ["dark", "forest", "eerie", "loop"],
        "url": "https://freesound.org/s/2/", "preview_url": None,
        "license": "CC-BY", "attribution": "Must credit.",
        "source": "Freesound",
    },
    {
        "id": "yt001", "title": "Sunbeam",  "artist": "The Great Outdoors",
        "genre": "Nature", "mood": "Bright/Optimistic",
        "bpm": 120, "duration": 0,
        "tags": ["nature", "bright", "upbeat", "acoustic", "travel vlog"],
        "url": "https://www.youtube.com/audiolibrary",
        "preview_url": None, "license": "CC0",
        "attribution": "No attribution required.", "source": "YouTube Library",
    },
]

results = matcher.match(video_data, fake_tracks)
print()
print("=== Ranked Results ===")
for t in results:
    print(f"  {t['title']:<25}  score={t['match_score']:>5.1f}%  breakdown={t['score_breakdown']}")

# ── Analyzer import check ───────────────────────────────────────────────────
print()
print("Importing VideoAnalyzer...", end=" ")
from src.analyzer import VideoAnalyzer
print("OK — CLIP model not loaded yet (lazy on first encode call)")
print("All checks passed.")

"""
music_fetcher.py — SonicScout Freesound integration

Freesound APIv2 reference: https://freesound.org/docs/api/resources_apiv2.html

Key design decisions:
  • Uses the unified /apiv2/search/ endpoint (replaces deprecated /search/text/
    and /search/content/).  BPM is now a first-class filterable field via
    filter=bpm:[MIN TO MAX].
  • Dual-strategy: BPM-first for high-energy videos (motion_energy > 0.6),
    mood-first for ambient/slow content — both fall back to the other if empty.
  • Similar-sounds discovery: top result feeds /sounds/{id}/similar/ to widen
    the candidate pool with acoustically-close matches.
  • Exponential back-off on HTTP 429, up to MAX_RETRIES attempts.
  • No mock / placeholder data — every result comes from a live API call.
"""

import requests
import os
import json
import time
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL = "https://freesound.org/apiv2"
MAX_RETRIES = 3
RETRY_BACKOFF = 2          # seconds; doubled on each retry
RATE_LIMIT_PAUSE = 5       # extra pause after a 429
MIN_DURATION = 15          # seconds — discard clips shorter than this
MAX_DURATION = 360         # 6 minutes upper cap

# License strings as returned by the Freesound API
CC0_LICENSE = "Creative Commons 0"
CCBY_LICENSE = "Attribution"

# Genre tag keywords to detect from sound tags
GENRE_KEYWORDS = [
    "electronic", "rock", "jazz", "hip-hop", "hiphop", "classical",
    "folk", "drone", "cinematic", "lofi", "lo-fi", "ambient",
    "acoustic", "synthwave", "chillout", "chill", "trap",
]

# Mood tag mappings
MOOD_MAP = {
    "happy":      "Bright/Optimistic",
    "bright":     "Bright/Optimistic",
    "upbeat":     "Bright/Optimistic",
    "cheerful":   "Bright/Optimistic",
    "energetic":  "Bright/Optimistic",
    "dark":       "Dark/Atmospheric",
    "atmospheric":"Dark/Atmospheric",
    "ominous":    "Dark/Atmospheric",
    "tense":      "Dark/Atmospheric",
    "eerie":      "Dark/Atmospheric",
    "calm":       "Balanced/Neutral",
    "peaceful":   "Balanced/Neutral",
    "neutral":    "Balanced/Neutral",
    "soft":       "Balanced/Neutral",
    "relaxing":   "Balanced/Neutral",
    "ambient":    "Balanced/Neutral",
    "sad":        "Melancholic/Emotional",
    "melancholic":"Melancholic/Emotional",
    "emotional":  "Melancholic/Emotional",
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe_get(url: str, params: dict, retries: int = MAX_RETRIES) -> Optional[dict]:
    """
    Perform a GET request with exponential back-off on 429 and transient
    5xx errors.  Returns the parsed JSON dict or None on permanent failure.
    """
    pause = RETRY_BACKOFF
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                logger.warning("Rate limited by Freesound. Waiting %ss…", pause + RATE_LIMIT_PAUSE)
                time.sleep(pause + RATE_LIMIT_PAUSE)
                pause *= 2
                continue
            if resp.status_code in (500, 502, 503, 504):
                logger.warning("Freesound server error %s. Retry %s/%s", resp.status_code, attempt + 1, retries)
                time.sleep(pause)
                pause *= 2
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning("Request timed out (attempt %s/%s)", attempt + 1, retries)
            time.sleep(pause)
            pause *= 2
        except requests.exceptions.RequestException as exc:
            logger.error("Request error: %s", exc)
            return None
    return None


def _infer_mood_from_tags(tags: list) -> str:
    for tag in tags:
        tl = tag.lower()
        for key, mood in MOOD_MAP.items():
            if key in tl:
                return mood
    return "Balanced/Neutral"


def _extract_genre(tags: list) -> str:
    for tag in tags:
        tl = tag.lower().replace("-", "").replace(" ", "")
        for kw in GENRE_KEYWORDS:
            if kw.replace("-", "") in tl:
                return tag.title()
    return "Ambient"


def _generate_attribution(sound: dict) -> str:
    """Proper attribution string per CC licence requirements."""
    license_str = sound.get("license", "")
    if CC0_LICENSE in license_str:
        return "No attribution required (CC0 — Public Domain)."
    name     = sound.get("name", "Unknown")
    username = sound.get("username", "Unknown artist")
    sid      = sound.get("id", "")
    url      = f"https://freesound.org/s/{sid}/"
    return f'"{name}" by {username} ({url}) is licensed under {license_str}.'


def _bpm_from_sound(sound: dict, fallback: float) -> float:
    """
    Extract BPM from the sound dict.  Freesound may include it at the
    top-level 'bpm' field (new API) or nested under analysis (legacy).
    """
    # 1. Top-level field (preferred, returned when fields=bpm is requested)
    bpm = sound.get("bpm")
    if bpm and float(bpm) > 0:
        return float(bpm)
    # 2. Legacy analysis object
    analysis = sound.get("analysis", {}) or {}
    bpm = analysis.get("rhythm.bpm")
    if bpm and float(bpm) > 0:
        return float(bpm)
    return fallback


def _normalize_sound(sound: dict, target_bpm: float) -> dict:
    """Convert a raw Freesound sound dict to SonicScout's internal format."""
    tags      = sound.get("tags", [])
    bpm       = _bpm_from_sound(sound, target_bpm)
    duration  = sound.get("duration", 30)

    # Clean up filename extensions from display name
    title = sound.get("name", "Untitled")
    for ext in (".wav", ".mp3", ".ogg", ".flac", ".aiff"):
        title = title.replace(ext, "")

    previews    = sound.get("previews", {}) or {}
    preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")

    license_raw = sound.get("license", "")
    license_tag = "CC0" if CC0_LICENSE in license_raw else "CC-BY"

    return {
        "id":          f"fs_{sound['id']}",
        "title":       title.strip(),
        "artist":      sound.get("username", "Unknown"),
        "genre":       _extract_genre(tags),
        "mood":        _infer_mood_from_tags(tags),
        "bpm":         round(bpm, 1),
        "duration":    round(duration, 1),
        "tags":        tags[:10],
        "url":         sound.get("url", f"https://freesound.org/s/{sound['id']}/"),
        "preview_url": preview_url,
        "license":     license_tag,
        "attribution": _generate_attribution(sound),
        "source":      "Freesound",
    }


# ---------------------------------------------------------------------------
# Core fields requested from every search call
# ---------------------------------------------------------------------------
SEARCH_FIELDS = (
    "id,name,license,username,previews,duration,tags,url,bpm"
)


# ---------------------------------------------------------------------------
# MusicFetcher
# ---------------------------------------------------------------------------

class MusicFetcher:
    """
    Fetches music candidates from the local YouTube-library JSON and from
    Freesound APIv2.  All Freesound calls use live API data — no mocks.
    """

    def __init__(self):
        self.api_key      = os.getenv("FREESOUND_API_KEY")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch_music(
        self,
        keywords: list,
        mood: str,
        target_bpm: float,
        motion_energy: float = 0.5,
    ) -> tuple:
        """
        Fetch music candidates from Freesound APIv2.

        Args:
            keywords:      Semantic keywords from the video analyser.
            mood:          Detected mood string (e.g. "Bright/Optimistic").
            target_bpm:    Target beats-per-minute derived from visual tempo.
            motion_energy: 0.0 (static) → 1.0 (high action).

        Returns:
            (results: list[dict], status: dict)
        """
        results = []
        status  = {
            "freesound": "Not configured",
        }

        # Freesound ---------------------------------------------------
        if self.api_key:
            try:
                fs = self._fetch_freesound(keywords, mood, target_bpm, motion_energy)
                results.extend(fs)
                status["freesound"] = f"Found {len(fs)} sounds"
            except Exception as exc:
                logger.exception("Freesound fetch failed: %s", exc)
                status["freesound"] = f"Error: {exc}"
        else:
            status["freesound"] = "Missing FREESOUND_API_KEY"

        return results, status



    # ------------------------------------------------------------------
    # Freesound — dual-strategy + similar-sounds expansion
    # ------------------------------------------------------------------

    def _fetch_freesound(
        self,
        keywords: list,
        mood: str,
        target_bpm: float,
        motion_energy: float,
    ) -> list:
        """
        Three-pass strategy — each pass is broader than the last so we
        always surface results even for unusual BPM / mood combinations.

        Pass 1 (primary)  — mood-text query, BPM as soft sort target.
        Pass 2 (secondary)— alternate query terms if pass 1 < 5 results.
        Pass 3 (fallback) — bare mood-only query, no BPM constraint at all.

        KEY DESIGN NOTE
        ---------------
        We intentionally do NOT use filter=bpm:[MIN TO MAX] as a hard filter
        because Freesound only stores BPM for sounds that have been analysed
        by Essentia — a large fraction of the library has no BPM stored at all.
        Filtering on BPM hard-excludes those sounds even though they may be
        perfect matches.  Instead we use sort=bpm:TARGET so the API ranks
        sounds-with-BPM at the top while still returning everything else;
        then we client-side sort the full pool by BPM proximity.

        Similarly, tag:loop is NOT a hard filter — it's added to the query
        as a soft signal so loopable sounds rank higher without excluding
        the rest of the library.
        """
        mood_keywords = self._mood_to_query_terms(keywords, mood)

        # -- Pass 1: primary mood/keyword query, BPM sorted ---------------
        primary = self._search_by_mood(
            mood_keywords, target_bpm, page_size=30
        )

        seen = set()
        combined = []
        for s in primary:
            sid = s.get("id")
            if sid and sid not in seen:
                seen.add(sid)
                combined.append(s)

        # -- Pass 2: alternate terms if too few results -------------------
        if len(combined) < 5:
            alt_terms = self._alt_query_terms(mood)
            secondary = self._search_by_mood(
                alt_terms, target_bpm, page_size=20
            )
            for s in secondary:
                sid = s.get("id")
                if sid and sid not in seen:
                    seen.add(sid)
                    combined.append(s)

        # -- Pass 3: broad fallback — just mood words, any duration -------
        if len(combined) < 3:
            fallback = self._search_broad_fallback(mood, target_bpm)
            for s in fallback:
                sid = s.get("id")
                if sid and sid not in seen:
                    seen.add(sid)
                    combined.append(s)

        # Duration filter (generous: 10 s – 6 min)
        filtered = [
            s for s in combined
            if 10 <= s.get("duration", 30) <= MAX_DURATION
        ]

        # Normalise + sort: sounds with known BPM get precision-ranked;
        # sounds without BPM fall back to target_bpm so they land in the
        # middle of the sorted list rather than always at the bottom.
        normalized = [_normalize_sound(s, target_bpm) for s in filtered]
        normalized.sort(key=lambda x: abs(x["bpm"] - target_bpm))

        # Widen pool with acoustically similar sounds from the top hit
        if normalized:
            try:
                top_raw_id = int(normalized[0]["id"].replace("fs_", ""))
                similar    = self._fetch_similar_sounds(top_raw_id, target_bpm, seen)
                normalized.extend(similar)
            except (ValueError, KeyError):
                pass

        return normalized[:15]

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------

    def _search_by_mood(
        self,
        mood_terms: list,
        target_bpm: float,
        page_size: int = 30,
    ) -> list:
        """
        Text search by mood/genre keywords.

        • License filter is the ONLY hard server-side filter — keeps the
          result pool as large as possible.
        • BPM is used as a *sort target* (sort=bpm:TARGET), not a filter,
          so sounds without stored BPM are still returned.
        • 'loop' is added to the query as a soft signal, not a hard filter.
        """
        license_filter = (
            f'license:"{CC0_LICENSE}" OR license:"{CCBY_LICENSE}"'
        )

        # Build query: music terms + 'loop' as a soft relevance signal
        query_terms = (mood_terms[:4] if mood_terms else ["background", "ambient"])
        query = " ".join(query_terms) + " loop"

        params = {
            "query":     query,
            "filter":    f"({license_filter})",
            "fields":    SEARCH_FIELDS,
            "page_size": page_size,
            "sort":      f"bpm:{int(target_bpm)}",  # rank by BPM proximity
            "token":     self.api_key,
            "format":    "json",
        }

        data = _safe_get(f"{BASE_URL}/search/", params)
        if not data:
            return []
        results = data.get("results", [])
        logger.info("Mood search '%s' → %d results", query[:60], len(results))
        return results

    def _search_broad_fallback(
        self,
        mood: str,
        target_bpm: float,
        page_size: int = 20,
    ) -> list:
        """
        Last-resort search: single mood word + 'music background'.
        No tag, no BPM constraint.  Always returns something.
        """
        mood_word_map = {
            "Bright/Optimistic":     "upbeat",
            "Dark/Atmospheric":      "dark",
            "Balanced/Neutral":      "ambient",
            "Melancholic/Emotional": "emotional",
        }
        mood_word = mood_word_map.get(mood, "ambient")
        license_filter = (
            f'license:"{CC0_LICENSE}" OR license:"{CCBY_LICENSE}"'
        )

        params = {
            "query":     f"{mood_word} music background",
            "filter":    f"({license_filter})",
            "fields":    SEARCH_FIELDS,
            "page_size": page_size,
            "sort":      f"bpm:{int(target_bpm)}",
            "token":     self.api_key,
            "format":    "json",
        }

        data = _safe_get(f"{BASE_URL}/search/", params)
        if not data:
            return []
        results = data.get("results", [])
        logger.info("Broad fallback '%s' → %d results", mood_word, len(results))
        return results

    def _alt_query_terms(self, mood: str) -> list:
        """Alternative Freesound-friendly query terms for pass 2."""
        alt_map = {
            "Bright/Optimistic":     ["cheerful", "happy", "bright", "positive"],
            "Dark/Atmospheric":      ["dark", "eerie", "ominous", "cinematic"],
            "Balanced/Neutral":      ["calm", "peaceful", "relaxing", "meditation"],
            "Melancholic/Emotional": ["sad", "melancholy", "emotional", "piano"],
        }
        return alt_map.get(mood, ["background", "music", "instrumental"])

    # ------------------------------------------------------------------
    # Similar-sounds expansion
    # ------------------------------------------------------------------

    def _fetch_similar_sounds(
        self,
        sound_id: int,
        target_bpm: float,
        already_seen: set,
        page_size: int = 10,
    ) -> list:
        """
        Call /apiv2/sounds/{id}/similar/ to discover acoustically similar
        tracks and widen the recommendation pool.
        Only token auth required (no OAuth2).
        """
        url = f"{BASE_URL}/sounds/{sound_id}/similar/"
        params = {
            "fields":    SEARCH_FIELDS,
            "page_size": page_size,
            "token":     self.api_key,
            "format":    "json",
        }
        data = _safe_get(url, params)
        if not data:
            return []

        similar = []
        for s in data.get("results", []):
            sid = s.get("id")
            if sid and sid not in already_seen:
                duration = s.get("duration", 0)
                if MIN_DURATION <= duration <= MAX_DURATION:
                    already_seen.add(sid)
                    similar.append(_normalize_sound(s, target_bpm))

        logger.info("Similar-sounds expansion added %d tracks", len(similar))
        return similar

    # ------------------------------------------------------------------
    # Sound detail lookup (used externally if needed)
    # ------------------------------------------------------------------

    def get_sound_details(self, sound_id: int) -> Optional[dict]:
        """
        Fetch full metadata + analysis for a specific sound ID.
        Useful for verifying licence of a selected track.
        """
        if not self.api_key:
            return None
        url = f"{BASE_URL}/sounds/{sound_id}/"
        params = {"token": self.api_key, "format": "json"}
        return _safe_get(url, params)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mood_to_query_terms(self, keywords: list, mood: str) -> list:
        """
        Map video analysis keywords → Freesound-compatible music search terms.

        CLIP category labels (e.g. 'educational', 'music performance') and
        vibe labels (e.g. 'fast-paced') don't match Freesound tags well.
        This method translates them into music vocabulary that does.
        """
        # CLIP category labels → Freesound music search terms
        category_to_music = {
            "travel vlog":       ["cinematic", "world"],
            "gaming clip":       ["electronic", "chiptune", "energetic"],
            "tech tutorial":     ["minimal", "electronic", "calm"],
            "nature cinematic":  ["ambient", "orchestral", "peaceful"],
            "cooking demo":      ["acoustic", "light", "upbeat"],
            "sports action":     ["energetic", "drum", "rock"],
            "lifestyle":         ["acoustic", "indie", "chill"],
            "music performance": ["instrumental", "acoustic"],
            "educational":       ["ambient", "minimal", "focus"],
            "motivational":      ["upbeat", "inspiring", "orchestral"],
        }
        # CLIP vibe labels → Freesound music search terms
        vibe_to_music = {
            "cinematic":   "cinematic",
            "energetic":   "energetic",
            "calm":        "calm",
            "dark":        "dark",
            "bright":      "bright",
            "minimalist":  "minimal",
            "retro":       "retro",
            "fast-paced":  "energetic",
            "emotional":   "emotional",
            "ambient":     "ambient",
            "upbeat":      "upbeat",
            "tense":       "tense",
        }

        # Mood-specific seed terms always included
        mood_terms_map = {
            "Bright/Optimistic":     ["upbeat", "happy", "bright"],
            "Dark/Atmospheric":      ["dark", "atmospheric", "drone"],
            "Balanced/Neutral":      ["ambient", "calm", "relaxing"],
            "Melancholic/Emotional": ["melancholic", "emotional", "piano"],
        }
        result_terms = list(mood_terms_map.get(mood, ["background", "ambient"]))

        for kw in keywords:
            kl = kw.lower()
            # Check category mapping first
            if kl in category_to_music:
                result_terms.extend(category_to_music[kl])
            # Then vibe mapping
            elif kl in vibe_to_music:
                result_terms.append(vibe_to_music[kl])
            # Otherwise only keep short single words that could be valid tags
            elif len(kl.split()) == 1 and len(kl) >= 3:
                result_terms.append(kl)

        # Deduplicate while preserving order
        seen: set = set()
        unique = []
        for term in result_terms:
            tl = term.lower()
            if tl not in seen:
                seen.add(tl)
                unique.append(term)

        return unique[:6] or ["background", "music", "ambient"]
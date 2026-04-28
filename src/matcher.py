"""
matcher.py — SonicScout multi-signal music matcher

Improvements over v1
─────────────────────
1. Five-signal scoring             — BPM proximity, semantic keywords, mood,
                                      licence preference, and duration fitness
                                      each contribute a weighted sub-score.
2. Gaussian BPM kernel             — tighter σ=20 gives a steeper score drop
                                      outside the ±15 BPM sweet-spot, rewarding
                                      precise matches more.
3. Semantic matching upgraded      — Jaccard similarity (intersection / union)
                                      instead of a raw count ratio, so tracks
                                      with few but perfectly matching tags rank
                                      higher than those with many near-misses.
4. Mood match maps to 4 moods      — aligned with the expanded mood vocabulary
                                      from the updated analyzer.
5. Licence bonus                   — CC0 tracks receive a small uplift over
                                      CC-BY to prioritise no-attribution tracks
                                      for YouTube monetisation safety.
6. Duration fitness                — penalises clips that are too short (<20s)
                                      or excessively long (>5 min) for typical
                                      vlog use-cases.
7. Per-signal breakdown exposed    — the returned dict includes sub-scores so
                                      the UI can show an explanatory tooltip.
8. Configurable weights            — all weights exposed as __init__ params so
                                      they can be tuned via Streamlit sliders.
"""

import math
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "bpm":       0.35,   # temporal energy alignment
    "semantic":  0.30,   # CLIP keyword ↔ track tag overlap
    "mood":      0.20,   # mood category match
    "licence":   0.08,   # CC0 preference bonus
    "duration":  0.07,   # fitness for typical vlog lengths
}

# Gaussian σ for BPM decay (larger = more forgiving)
BPM_SIGMA = 20.0

# Ideal track duration window for vlog use (seconds)
IDEAL_DURATION_MIN = 30
IDEAL_DURATION_MAX = 180

# Mood compatibility matrix — partial credit for related moods
MOOD_COMPAT = {
    ("Bright/Optimistic",    "Bright/Optimistic"):    1.00,
    ("Bright/Optimistic",    "Balanced/Neutral"):      0.50,
    ("Dark/Atmospheric",     "Dark/Atmospheric"):      1.00,
    ("Dark/Atmospheric",     "Melancholic/Emotional"): 0.60,
    ("Dark/Atmospheric",     "Balanced/Neutral"):      0.30,
    ("Balanced/Neutral",     "Balanced/Neutral"):      1.00,
    ("Balanced/Neutral",     "Bright/Optimistic"):     0.50,
    ("Balanced/Neutral",     "Melancholic/Emotional"): 0.40,
    ("Melancholic/Emotional","Melancholic/Emotional"): 1.00,
    ("Melancholic/Emotional","Balanced/Neutral"):      0.40,
    ("Melancholic/Emotional","Dark/Atmospheric"):      0.60,
}


class MusicMatcher:
    """
    Scores and ranks music tracks against extracted video features.
    """

    def __init__(
        self,
        weights:    Optional[dict] = None,
        bpm_sigma:  float          = BPM_SIGMA,
    ):
        self.weights   = {**DEFAULT_WEIGHTS, **(weights or {})}
        self.bpm_sigma = bpm_sigma

        # Normalise weights so they always sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

        logger.debug("MusicMatcher weights: %s", self.weights)

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def match(self, video_data: dict, music_list: list) -> list:
        """
        Score every track in *music_list* against *video_data*.

        Parameters
        ----------
        video_data  : dict returned by VideoAnalyzer.analyze_video()
        music_list  : list of track dicts (from MusicFetcher)

        Returns
        -------
        List of track dicts (all original fields preserved) with
        additional keys:
            match_score     float 0-100  overall match percentage
            score_breakdown dict         per-signal contributions (0-100 each)
        Sorted descending by match_score.
        """
        if not music_list:
            return []

        target_bpm = float(video_data.get("target_bpm", 100))
        mood       = video_data.get("mood", "Balanced/Neutral")
        keywords   = [k.lower() for k in video_data.get("keywords", [])]

        scored = []
        for track in music_list:
            breakdown = self._score_track(track, target_bpm, mood, keywords)
            total     = sum(
                self.weights[sig] * val
                for sig, val in breakdown.items()
                if sig in self.weights
            )
            final_pct = round(min(total * 100, 100), 1)
            scored.append({
                **track,
                "match_score":     final_pct,
                "score_breakdown": {k: round(v * 100, 1) for k, v in breakdown.items()},
            })

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        logger.info(
            "Matched %d tracks; top score %.1f%% (%s)",
            len(scored), scored[0]["match_score"], scored[0]["title"],
        )
        return scored

    # ──────────────────────────────────────────────────────────
    # Scoring sub-signals
    # ──────────────────────────────────────────────────────────

    def _score_track(
        self,
        track:      dict,
        target_bpm: float,
        mood:       str,
        keywords:   list,
    ) -> dict:
        return {
            "bpm":      self._score_bpm(track, target_bpm),
            "semantic": self._score_semantic(track, keywords),
            "mood":     self._score_mood(track, mood),
            "licence":  self._score_licence(track),
            "duration": self._score_duration(track),
        }

    def _score_bpm(self, track: dict, target_bpm: float) -> float:
        """
        Gaussian kernel centred on target_bpm.
        Returns 1.0 for a perfect match, decays smoothly with distance.
        """
        track_bpm = float(track.get("bpm") or target_bpm)
        diff      = abs(target_bpm - track_bpm)
        return float(math.exp(-(diff ** 2) / (2 * self.bpm_sigma ** 2)))

    def _score_semantic(self, track: dict, keywords: list) -> float:
        """
        Jaccard similarity between video keywords and track tags.
        Also checks partial substring matches for broad coverage.
        """
        if not keywords:
            return 0.5  # neutral if no keywords

        track_tags = [t.lower() for t in track.get("tags", [])]
        if not track_tags:
            return 0.0

        kw_set  = set(keywords)
        tag_set = set(track_tags)

        # Exact Jaccard
        exact_intersection = kw_set & tag_set
        exact_union        = kw_set | tag_set
        jaccard            = len(exact_intersection) / len(exact_union) if exact_union else 0.0

        # Partial match bonus — keyword appears as substring in any tag or vice-versa
        partial_hits = sum(
            1 for kw in kw_set
            if any(kw in tag or tag in kw for tag in tag_set)
        )
        partial_score = min(partial_hits / max(len(kw_set), 1), 1.0) * 0.4

        return min(jaccard + partial_score, 1.0)

    def _score_mood(self, track: dict, video_mood: str) -> float:
        """
        Mood compatibility lookup.  Uses the MOOD_COMPAT matrix for partial
        credit on related moods; defaults to 0 for completely unrelated pairs.
        """
        track_mood = track.get("mood", "Balanced/Neutral")
        key = (video_mood, track_mood)
        if key in MOOD_COMPAT:
            return MOOD_COMPAT[key]
        # Try reversed key (symmetry for pairs not explicitly listed)
        rev = (track_mood, video_mood)
        if rev in MOOD_COMPAT:
            return MOOD_COMPAT[rev]
        return 0.0

    def _score_licence(self, track: dict) -> float:
        """
        CC0 = 1.0 (no attribution, safest for monetised YouTube).
        CC-BY = 0.6 (requires attribution, still legal).
        Anything else = 0.2 (caution).
        """
        lic = (track.get("license") or "").upper()
        if lic in ("CC0", "CC0 1.0", "CREATIVE COMMONS 0"):
            return 1.0
        if lic in ("CC-BY", "ATTRIBUTION"):
            return 0.6
        return 0.2

    def _score_duration(self, track: dict) -> float:
        """
        Penalises tracks much shorter or longer than the ideal vlog window
        (30 s – 3 min) using a trapezoid function: full score inside the
        ideal range, linearly dropping to 0 outside a tolerance band.
        """
        dur = float(track.get("duration") or 0)

        # Zero duration means unknown (local library) — give neutral score
        if dur <= 0:
            return 0.7

        low_hard  = 10                   # <10 s is too short
        low_soft  = IDEAL_DURATION_MIN   # 30 s is the soft lower bound
        high_soft = IDEAL_DURATION_MAX   # 180 s is the soft upper bound
        high_hard = 360                  # >6 min is too long

        if low_soft <= dur <= high_soft:
            return 1.0
        if dur < low_hard or dur > high_hard:
            return 0.0
        if dur < low_soft:
            return (dur - low_hard) / (low_soft - low_hard)
        # dur > high_soft
        return 1.0 - (dur - high_soft) / (high_hard - high_soft)

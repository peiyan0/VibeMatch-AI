"""
analyzer.py — SonicScout video analysis pipeline

Improvements over v1
─────────────────────
1. Smarter frame sampling          — 12 evenly-spaced frames instead of 3.
2. Optical-flow motion energy      — dense Farneback flow magnitude supplements
                                      SSIM for a more accurate motion score.
3. Wider BPM range                 — mapped 60-180 BPM instead of the
                                      original 80-160, covering lo-fi to drum-&-bass.
4. Colour-aware mood               — combines HSV value (brightness) with
                                      saturation to produce 4 mood categories
                                      instead of 3.
5. Richer CLIP label taxonomy      — 10 categories × 12 vibes, with labels
                                      phrased as natural sentences for better
                                      CLIP zero-shot accuracy.
6. Keyword confidence threshold    — only returns keywords whose CLIP similarity
                                      exceeds a minimum confidence floor, avoiding
                                      spurious matches.
7. Scene-change detection          — SSIM spike detection marks cut density,
                                      which augments the motion score.
8. Returns motion_energy           — float 0-1 forwarded to MusicFetcher's
                                      dual-strategy selector.
"""

import cv2
import numpy as np
import logging
from PIL import Image
import torch
from sentence_transformers import SentenceTransformer
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# CLIP label taxonomy
# Phrasing as sentences improves zero-shot CLIP performance.
# ─────────────────────────────────────────────────────────────
CATEGORIES = [
    "a travel vlog of landscapes and adventures",
    "a gaming highlights clip with action gameplay",
    "a technology tutorial with screens and code",
    "cinematic nature footage of forests and wildlife",
    "a cooking or food preparation video",
    "a sports or fitness action video",
    "a lifestyle or fashion video",
    "a music performance or concert video",
    "an educational or talking-head video",
    "a motivational montage or highlight reel",
]

VIBES = [
    "cinematic and dramatic",
    "energetic and high-intensity",
    "calm and relaxing",
    "dark and moody",
    "bright and cheerful",
    "minimalist and clean",
    "retro and nostalgic",
    "fast-paced and thrilling",
    "emotional and heartfelt",
    "ambient and atmospheric",
    "upbeat and happy",
    "tense and suspenseful",
]

# Short readable labels returned in the analysis dict (same order as above)
CATEGORY_LABELS = [
    "travel vlog", "gaming clip", "tech tutorial", "nature cinematic",
    "cooking demo", "sports action", "lifestyle", "music performance",
    "educational", "motivational",
]
VIBE_LABELS = [
    "cinematic", "energetic", "calm", "dark", "bright", "minimalist",
    "retro", "fast-paced", "emotional", "ambient", "upbeat", "tense",
]

# Minimum average CLIP similarity to accept a label (tune 0-1)
CLIP_CONFIDENCE_THRESHOLD = 0.20

# Optical-flow sample stride (process every N-th frame pair for speed)
FLOW_STRIDE = 5

# SSIM drop that signals a hard scene cut
SCENE_CUT_SSIM_THRESHOLD = 0.70


class VideoAnalyzer:
    """Analyses a video clip and returns features needed for music matching."""

    def __init__(self):
        self.model  = SentenceTransformer("clip-ViT-B-32")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        # Pre-encode text labels once (reused across calls)
        all_text = CATEGORIES + VIBES
        self._text_embeddings = self.model.encode(all_text, convert_to_numpy=True)
        logger.info("VideoAnalyzer initialised on %s", self.device)

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def analyze_video(self, video_path: str) -> dict:
        """
        Main analysis entry point.

        Returns
        -------
        dict with keys:
            visual_tempo   float 0-1  (0=static, 1=very fast)
            motion_energy  float 0-1  (optical-flow based; forwarded to fetcher)
            target_bpm     float      estimated ideal BPM
            keywords       list[str]  top category + vibe labels
            mood           str        one of four mood categories
            scene_cuts     int        number of detected hard scene cuts
            duration       float      video length in seconds
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps          = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration     = total_frames / fps

        # Determine which frame indices to grab for CLIP
        n_samples       = min(12, max(3, total_frames // 30))
        sample_indices  = set(
            int(total_frames * i / (n_samples - 1))
            for i in range(n_samples)
        ) if n_samples > 1 else {total_frames // 2}

        frames          = []        # PIL frames for CLIP
        ssim_scores     = []        # frame-to-frame SSIM
        flow_magnitudes = []        # optical-flow magnitudes
        scene_cuts      = 0

        prev_gray  = None
        prev_small = None
        count      = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            small = cv2.resize(frame, (128, 128))
            gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                # ── SSIM (structural similarity) ──────────────────────
                score, _ = ssim(prev_gray, gray, full=True)
                ssim_scores.append(float(score))
                if score < SCENE_CUT_SSIM_THRESHOLD:
                    scene_cuts += 1

                # ── Dense optical flow (every FLOW_STRIDE frames) ──────
                if count % FLOW_STRIDE == 0 and prev_small is not None:
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_small, gray,
                        None,
                        pyr_scale=0.5, levels=3, winsize=15,
                        iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
                    )
                    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                    flow_magnitudes.append(float(np.mean(mag)))

            prev_gray  = gray
            prev_small = gray if count % FLOW_STRIDE == 0 else prev_small

            # ── Sample frames for CLIP ────────────────────────────────
            if count in sample_indices:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(rgb))

            count += 1

        cap.release()

        # ── Aggregate motion signals ──────────────────────────────────
        avg_ssim   = float(np.mean(ssim_scores))   if ssim_scores   else 1.0
        avg_flow   = float(np.mean(flow_magnitudes)) if flow_magnitudes else 0.0

        # SSIM-based tempo: 0=static, 1=rapid cuts
        ssim_tempo = 1.0 - avg_ssim

        # Flow-based energy: normalise against a practical ceiling of 8 px/frame
        flow_energy = min(avg_flow / 8.0, 1.0)

        # Cut density contribution
        cut_density = min(scene_cuts / max(duration, 1) / 2.0, 1.0)

        # Combined visual tempo (weighted blend)
        visual_tempo_score = float(
            0.40 * ssim_tempo + 0.45 * flow_energy + 0.15 * cut_density
        )
        visual_tempo_score = max(0.0, min(1.0, visual_tempo_score))

        # Motion energy is the flow-dominant signal (for fetcher strategy)
        motion_energy = float(
            0.30 * ssim_tempo + 0.60 * flow_energy + 0.10 * cut_density
        )
        motion_energy = max(0.0, min(1.0, motion_energy))

        # ── BPM mapping (60-180 BPM) ──────────────────────────────────
        # 60 BPM = very slow/ambient; 180 BPM = drum-and-bass / intense action
        target_bpm = 60.0 + (visual_tempo_score * 120.0)

        # ── Semantic & mood analysis ──────────────────────────────────
        keywords = self._extract_keywords(frames)
        mood     = self._analyze_mood(frames)

        logger.info(
            "Analysis: tempo=%.2f motion=%.2f bpm=%.0f cuts=%d mood=%s",
            visual_tempo_score, motion_energy, target_bpm, scene_cuts, mood,
        )

        return {
            "visual_tempo":  round(visual_tempo_score, 3),
            "motion_energy": round(motion_energy, 3),
            "target_bpm":    round(target_bpm, 1),
            "keywords":      keywords,
            "mood":          mood,
            "scene_cuts":    scene_cuts,
            "duration":      round(duration, 2),
        }

    # ──────────────────────────────────────────────────────────
    # CLIP keyword extraction
    # ──────────────────────────────────────────────────────────

    def _extract_keywords(self, frames: list) -> list:
        """
        CLIP zero-shot classification over sampled frames.

        Returns top 2 category labels + top 3 vibe labels that exceed
        the confidence threshold, with high-confidence labels first.
        """
        if not frames:
            return []

        img_embeddings  = self.model.encode(frames, convert_to_numpy=True)
        # text embeddings were pre-encoded at init
        similarities    = np.dot(img_embeddings, self._text_embeddings.T)
        avg_sim         = np.mean(similarities, axis=0)  # shape (n_labels,)

        n_cat = len(CATEGORIES)
        cat_scores  = avg_sim[:n_cat]
        vibe_scores = avg_sim[n_cat:]

        # Top categories — accept those above threshold
        top_cat_idx  = cat_scores.argsort()[-2:][::-1]
        top_cats     = [
            CATEGORY_LABELS[i] for i in top_cat_idx
            if cat_scores[i] >= CLIP_CONFIDENCE_THRESHOLD
        ]

        # Top vibes — accept those above threshold
        top_vibe_idx = vibe_scores.argsort()[-3:][::-1]
        top_vibes    = [
            VIBE_LABELS[i] for i in top_vibe_idx
            if vibe_scores[i] >= CLIP_CONFIDENCE_THRESHOLD
        ]

        return top_cats + top_vibes

    # ──────────────────────────────────────────────────────────
    # Mood analysis (HSV brightness + saturation)
    # ──────────────────────────────────────────────────────────

    def _analyze_mood(self, frames: list) -> str:
        """
        Combines HSV Value (brightness) and Saturation to derive mood.

        Mood categories
        ───────────────
        Bright/Optimistic   → high brightness, moderate-to-high saturation
        Dark/Atmospheric    → low brightness (any saturation)
        Melancholic/Emotional → low saturation, mid brightness
        Balanced/Neutral    → everything else
        """
        if not frames:
            return "Balanced/Neutral"

        brightness_vals = []
        saturation_vals = []

        for img in frames:
            arr = np.array(img)
            hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
            saturation_vals.append(float(np.mean(hsv[:, :, 1])))
            brightness_vals.append(float(np.mean(hsv[:, :, 2])))

        avg_v = float(np.mean(brightness_vals))   # 0-255
        avg_s = float(np.mean(saturation_vals))   # 0-255

        if avg_v > 170:
            return "Bright/Optimistic"
        if avg_v < 75:
            return "Dark/Atmospheric"
        if avg_s < 60:
            return "Melancholic/Emotional"
        return "Balanced/Neutral"

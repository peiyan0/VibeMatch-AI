# Freesound API v2 - Agent Documentation

## Overview

Freesound provides CC0 (Public Domain) and Creative Commons licensed audio. Use this for **motion-synced background music** and **ambient textures** in VibeMatch AI.

**Base URL:** `https://freesound.org/apiv2`

**Authentication:** API key required (free). Get at: `https://freesound.org/apiv2/apply`

---

## Quick Reference for Agent

| Task | Endpoint | Auth Required |
|------|----------|---------------|
| Search by text + license | `GET /search/text/` | API key only |
| Search by BPM/features | `GET /search/content/` | API key only |
| Search by both | `GET /search/combined/` (deprecated but works) | API key only |
| Get sound details | `GET /sounds/{id}/` | API key only |
| Get preview URL | From sound response | None |
| Download original file | `GET /sounds/{id}/download/` | OAuth2 required |

**For VibeMatch AI:** Use `search/content/` for BPM matching, `search/text/` for mood tags. Use **preview URLs** (no OAuth needed).

---

## Endpoint 1: Text Search (for mood/genre matching)

### Request
```http
GET /apiv2/search/text/?query={query}&filter={filter}&page={page}&page_size={size}&token={YOUR_TOKEN}
```

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query` | string | Search terms | `"calm piano"` |
| `filter` | string | License or tag filter | `license:"Creative Commons 0"` |
| `page` | int | Page number (default 1) | `2` |
| `page_size` | int | Results per page (15-150) | `15` |
| `token` | string | Your API key | `abc123...` |

### License Filter Values (Important!)
```
license:"Creative Commons 0"          # CC0 - Public Domain (best)
license:"Attribution"                  # CC-BY - requires credit
license:"Attribution Noncommercial"    # CC-BY-NC - NO commercial use
license:"Sampling+"                    # Limited use
```

### Response Structure (JSON)
```json
{
  "count": 1247,
  "next": "https://freesound.org/apiv2/search/text/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123456,
      "name": "calm-piano-loop.wav",
      "license": "Creative Commons 0",
      "username": "artist_name",
      "previews": {
        "preview-hq-mp3": "https://cdn.freesound.org/preview/123/123456-hq.mp3",
        "preview-hq-ogg": "https://cdn.freesound.org/preview/123/123456-hq.ogg",
        "preview-lq-mp3": "https://cdn.freesound.org/preview/123/123456-lq.mp3"
      },
      "duration": 32.5,
      "tags": ["piano", "calm", "ambient", "loop"],
      "analysis": {
        "rhythm.bpm": 70.2,
        "lowlevel.pitch.mean": 440.5
      }
    }
  ]
}
```

### Python Implementation for Agent
```python
import requests

def search_freesound_by_mood(mood_query: str, license_type: str = "cc0", token: str = None) -> list:
    """
    Search Freesound by textual mood description.
    
    Args:
        mood_query: e.g., "happy acoustic guitar", "dark ambient drone"
        license_type: "cc0", "by", "nc" (maps to license strings)
        token: API key from freesound.org
    
    Returns:
        List of sound dicts with preview URLs
    """
    license_map = {
        "cc0": 'license:"Creative Commons 0"',
        "by": 'license:"Attribution"',
        "nc": 'license:"Attribution Noncommercial"'  # NOT for monetized YouTube
    }
    
    url = "https://freesound.org/apiv2/search/text/"
    params = {
        "query": mood_query,
        "filter": license_map.get(license_type, license_map["cc0"]),
        "page_size": 10,
        "token": token,
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    return response.json()["results"]
```

---

## Endpoint 2: Content Search (for BPM/Motion Matching) ⭐ **Most Important for VibeMatch AI**

This searches by **audio features** (BPM, pitch, timbre) - perfect for matching your video's motion energy.

### Request
```http
GET /apiv2/search/content/?descriptors_filter={filter}&filter={license_filter}&token={token}
```

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `descriptors_filter` | string | Range query on audio features | `rhythm.bpm:[100 TO 120]` |
| `filter` | string | License or tag filter | `tag:loop` |
| `page_size` | int | Results per page | `15` |
| `token` | string | API key | `abc123...` |

### Descriptors Available (most useful for you)

| Descriptor | Description | Example |
|------------|-------------|---------|
| `rhythm.bpm` | Beats per minute | `[60 TO 80]` (slow), `[120 TO 140]` (upbeat) |
| `lowlevel.pitch.mean` | Average pitch (Hz) | `[200 TO 500]` |
| `lowlevel.pitch.salience` | Clarity of pitch (0-1) | `[0.7 TO 1]` (melodic vs noise) |
| `lowlevel.dynamic.mean` | Average loudness (dB) | `[-20 TO -10]` |
| `rhythm.beats_count` | Number of beats | `[16 TO 32]` |

### Combined Example: BPM + Tag + License
```python
# Motion energy 0.7 (high action) -> BPM 120-140
bpm_min = 120
bpm_max = 140

url = "https://freesound.org/apiv2/search/content/"
params = {
    "descriptors_filter": f"rhythm.bpm:[{bpm_min} TO {bpm_max}]",
    "filter": 'tag:loop AND license:"Creative Commons 0"',  # Multiple filters with AND
    "page_size": 20,
    "token": token,
    "format": "json"
}
```

### Response (same structure as text search, plus richer analysis)
```json
{
  "results": [{
    "id": 789012,
    "name": "fast-drum-loop.wav",
    "analysis": {
      "rhythm.bpm": 128.4,
      "rhythm.beats_count": 32,
      "lowlevel.pitch.mean": 320.5,
      "lowlevel.dynamic.mean": -12.3
    }
  }]
}
```

### Python Implementation for Motion-to-BPM
```python
def search_freesound_by_bpm(bpm_min: int, bpm_max: int, 
                            tags: list = None, 
                            license_type: str = "cc0",
                            token: str = None) -> list:
    """
    Search Freesound by BPM range for motion-matching.
    
    Args:
        bpm_min: Minimum beats per minute
        bpm_max: Maximum beats per minute
        tags: Optional list of tags e.g., ["drone", "ambient"]
        license_type: "cc0" or "by"
        token: API key
    
    Returns:
        List of sounds matching BPM criteria
    """
    # Build descriptor filter
    descriptor_filter = f"rhythm.bpm:[{bpm_min} TO {bpm_max}]"
    
    # Build metadata filter
    license_map = {"cc0": 'license:"Creative Commons 0"', "by": 'license:"Attribution"'}
    meta_filters = [license_map.get(license_type, license_map["cc0"])]
    
    if tags:
        tag_filters = [f'tag:{tag}' for tag in tags]
        meta_filters.extend(tag_filters)
    
    combined_filter = " AND ".join(meta_filters)
    
    url = "https://freesound.org/apiv2/search/content/"
    params = {
        "descriptors_filter": descriptor_filter,
        "filter": combined_filter,
        "page_size": 15,
        "token": token,
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["results"]
```

---

## Endpoint 3: Get Sound Details (for license verification)

### Request
```http
GET /apiv2/sounds/{sound_id}/?token={token}
```

### Response includes full metadata and analysis
```json
{
  "id": 123456,
  "name": "sound-name.wav",
  "license": "Creative Commons 0",
  "url": "https://freesound.org/people/username/sounds/123456/",
  "analysis": {
    "rhythm.bpm": 70.2,
    "lowlevel.pitch.mean": 440.5,
    "lowlevel.dynamic.mean": -18.7,
    "rhythm.beats_count": 24
  },
  "previews": {
    "preview-hq-mp3": "https://cdn.freesound.org/preview/123/123456-hq.mp3"
  },
  "duration": 45.2,
  "tags": ["ambient", "piano", "slow"]
}
```

### Python Implementation
```python
def get_sound_details(sound_id: int, token: str) -> dict:
    """Get full metadata and analysis for a specific sound."""
    url = f"https://freesound.org/apiv2/sounds/{sound_id}/"
    params = {"token": token, "format": "json"}
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
```

---

## VibeMatch AI Integration Logic

### Complete Agent Function
```python
class VibeMatchAIFreesoundAgent:
    def __init__(self, api_token: str):
        self.token = api_token
        self.base_url = "https://freesound.org/apiv2"
    
    def match_video_to_sound(self, motion_energy: float, mood_tags: list) -> dict:
        """
        Core matching function for VibeMatch AI.
        
        Args:
            motion_energy: 0.0 (static) to 1.0 (high action)
            mood_tags: e.g., ["calm", "piano"] or ["aggressive", "electronic"]
        
        Returns:
            Best matching sound with preview URL
        """
        # Map motion energy to BPM
        # motion_energy 0 = 60 BPM (slow), 1 = 140 BPM (fast)
        bpm_center = 60 + (motion_energy * 80)
        bpm_min = int(bpm_center - 15)
        bpm_max = int(bpm_center + 15)
        
        # Build query based on mood (from CLIP analysis)
        mood_query = " ".join(mood_tags[:3])  # Use top 3 mood tags
        
        # Strategy 1: BPM-first (for motion-heavy videos)
        if motion_energy > 0.6:
            results = self._search_by_bpm(bpm_min, bpm_max, mood_tags)
        else:
            # Strategy 2: Mood-first (for slow/ambient videos)
            results = self._search_by_mood(mood_query, bpm_min, bpm_max)
        
        # Filter for usable duration (>20s, <5min)
        results = [r for r in results if 20 <= r.get("duration", 0) <= 300]
        
        # Sort by BPM accuracy (closest to center)
        for r in results:
            sound_bpm = r.get("analysis", {}).get("rhythm.bpm", bpm_center)
            r["bpm_score"] = 1 - abs(sound_bpm - bpm_center) / 80
        
        results.sort(key=lambda x: x.get("bpm_score", 0), reverse=True)
        
        return results[0] if results else None
    
    def _search_by_bpm(self, bpm_min: int, bpm_max: int, tags: list) -> list:
        """Search using content API with BPM filter."""
        url = f"{self.base_url}/search/content/"
        tag_str = " AND ".join([f'tag:{t}' for t in tags[:3]])
        license_filter = 'license:"Creative Commons 0"'
        
        params = {
            "descriptors_filter": f"rhythm.bpm:[{bpm_min} TO {bpm_max}]",
            "filter": f"{license_filter} AND {tag_str}" if tags else license_filter,
            "page_size": 10,
            "token": self.token,
            "format": "json"
        }
        
        response = requests.get(url, params=params)
        return response.json().get("results", [])
    
    def _search_by_mood(self, mood_query: str, bpm_min: int, bpm_max: int) -> list:
        """Search using text API, then filter by BPM from analysis."""
        url = f"{self.base_url}/search/text/"
        params = {
            "query": mood_query,
            "filter": 'license:"Creative Commons 0"',
            "page_size": 20,
            "token": self.token,
            "format": "json"
        }
        
        response = requests.get(url, params=params)
        results = response.json().get("results", [])
        
        # Filter by BPM (parse from analysis JSON string if present)
        filtered = []
        for r in results:
            analysis = r.get("analysis", {})
            bpm = analysis.get("rhythm.bpm")
            if bpm and bpm_min <= bpm <= bpm_max:
                filtered.append(r)
        
        return filtered
    
    def get_preview_url(self, sound: dict, quality: str = "hq") -> str:
        """
        Extract preview URL from sound object.
        quality: "hq" (high quality mp3) or "lq" (low quality)
        """
        previews = sound.get("previews", {})
        key = f"preview-{quality}-mp3" if quality == "hq" else "preview-lq-mp3"
        return previews.get(key)
```

---

## Error Handling for Agent

| HTTP Status | Meaning | Agent Action |
|-------------|---------|--------------|
| 200 | Success | Process results |
| 400 | Bad request - missing param | Check query/mood_tags not empty |
| 401/403 | Auth failed | Verify token, re-prompt user |
| 404 | Sound not found | Fallback to text search |
| 429 | Rate limited | Wait 2 seconds, retry (max 3 times) |
| 5xx | Server error | Fallback to YouTube Audio Library |

### Rate Limit Handling
```python
import time
from requests.exceptions import HTTPError

def rate_limited_search(func):
    """Decorator to handle Freesound's 60 req/min limit."""
    last_call = 0
    
    def wrapper(*args, **kwargs):
        nonlocal last_call
        elapsed = time.time() - last_call
        if elapsed < 1.0:  # Minimum 1 second between calls
            time.sleep(1.0 - elapsed)
        
        try:
            result = func(*args, **kwargs)
            last_call = time.time()
            return result
        except HTTPError as e:
            if e.response.status_code == 429:
                time.sleep(5)  # Wait 5 seconds on rate limit
                return func(*args, **kwargs)
            raise
    return wrapper
```

---

## Attribution Requirements (for CC-BY license)

When using non-CC0 sounds, generate attribution text:

```python
def generate_attribution(sound: dict) -> str:
    """Generate required attribution text for YouTube description."""
    name = sound.get("name", "Unknown")
    username = sound.get("username", "Unknown artist")
    license_name = sound.get("license", "Creative Commons")
    sound_url = f"https://freesound.org/s/{sound.get('id')}/"
    
    return f'"{name}" by {username} ({sound_url}) is licensed under {license_name}'
```

---

## Summary for Coding Agent

**Do use Freesound for:**
- BPM-matched background music (via `search/content/` endpoint)
- CC0-licensed sounds (guaranteed safe for monetization)
- Ambient textures and loops (large library)
- Quick preview generation (no OAuth for preview URLs)

**Don't use Freesound for:**
- Full-quality downloads without OAuth (use previews instead)
- Extremely popular/mainstream music (not the focus)
- Real-time streaming (use preview URLs directly)

**Fallback strategy:** If Freesound returns no results, fall back to YouTube Audio Library local CSV.
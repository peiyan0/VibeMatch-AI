# 🎵 SonicScout: AI Music Matchmaker

**SonicScout** is an intelligent AI agent designed for content creators and YouTubers. It bridge the gap between visual storytelling and audio accompaniment by automatically analyzing video vibes and matching them with legally safe, high-quality CC0 and Public Domain music.

---

## ✨ Key Features

- 🎬 **Visual Tempo Analysis**: Uses SSIM (Structural Similarity) and Optical Flow to determine the "energy" and required BPM.
- 🏷️ **Semantic Scene Labeling**: Leverages CLIP-ViT-B-32 to identify video categories and vibes.
- 🌓 **Mood Detection**: Analyzes lighting, color palette, and saturation to infer the emotional state.
- 🎼 **Smart Matching Engine**: A 5-factor scoring system (BPM, Semantics, Mood, License, Duration).
- 🔊 **Live Freesound Integration**: Fetches real-time candidates from the Freesound API (v2).
- 🛡️ **Zero-Strike Policy**: Enforces metadata guardrails to ensure 100% legal safety for monetization.

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have Python 3.9+ installed. We recommend using a virtual environment.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/peiyan0/ai-music-selection.git
cd ai-music-selection

# Install dependencies
pip install -r requirements.txt
```

### 3. API Configuration
Create a `.env` file in the root directory and add your Freesound API key:
```env
FREESOUND_API_KEY=your_key_here
```
*Get your key at: [freesound.org/apiv2/apply](https://freesound.org/apiv2/apply)*

### 4. Run the Dashboard
```bash
streamlit run app.py
```

---

## 🧠 Project Philosophy: Why Selection Over Generation?

While AI music *generation* is popular, it often carries legal risks regarding training data and commercial rights. SonicScout takes a different approach: **Intelligent Selection.**

1. **Copyright Safety**: By sourcing from **CC0 and Public Domain** sources, we ensure your videos are 100% safe for monetization.
2. **Zero Cost**: No subscription traps or "10 downloads per month" limits.
3. **Human Quality**: Why settle for AI loops when you can have tracks recorded by real musicians for free?

---

## 🔬 Technical Methodology

### The Matching Engine
The "Brain" of SonicScout uses a weighted matching equation to rank candidates:

$$Match Score = (S_{visual} \cdot W_{genre}) + (E_{motion} \cdot W_{tempo}) + M_{mood}$$

- **$S_{visual}$**: Semantic similarity (Jaccard) between CLIP-identified keywords and track tags.
- **$E_{motion}$**: Gaussian correlation between visual motion energy and track BPM.
- **$M_{mood}$**: Compatibility bonus for aligned emotional profiles.

### Feature Extraction
- **Visual Tempo**: We calculate the **Structural Similarity Index (SSIM)** between sequential frames. A low SSIM indicates high motion or frequent cuts, signaling a need for higher BPM music.
- **Semantic Vibe**: We use **Zero-Shot CLIP Classification** to map video scenes (e.g., "travel vlog in Bali") directly to musical styles (e.g., "Acoustic", "World", "Tropical").

---

## 🏗️ Repository Structure

```text
.
├── assets/             # Static assets
├── docs/               # Detailed documentation
├── src/                # Core logic
│   ├── analyzer.py     # Video processing (OpenCV + CLIP)
│   ├── matcher.py      # Multi-factor scoring engine
│   └── music_fetcher.py # Live API fetching logic
├── tests/              # Smoke tests and validation scripts
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
└── README.md           # You are here
```

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **ML Models**: CLIP (OpenAI), Sentence Transformers
- **Computer Vision**: OpenCV, scikit-image
- **API**: Freesound API v2
- **Data**: Freesound CC0/CC-BY Repository

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
*Music fetched via Freesound is subject to its original CC0 or CC-BY licenses.*

---

*Built with ❤️ for creators*

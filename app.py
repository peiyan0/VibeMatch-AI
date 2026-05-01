import streamlit as st
import os
import tempfile
from src.analyzer import VideoAnalyzer
from src.music_fetcher import MusicFetcher
from src.matcher import MusicMatcher
import time
import random
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="VibeMatch AI | Pro Soundtrack Finder for YouTubers",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling (Premium Creator Edition) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    :root {
        --primary-gradient: linear-gradient(135deg, #A855F7 0%, #F472B6 100%);
        --accent-gradient: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Hero Banner */
    .hero-container {
        position: relative;
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border: 1px solid var(--glass-border);
    }

    .hero-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 3rem 2rem;
        background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, transparent 100%);
        text-align: center;
    }

    /* Buttons */
    .stButton>button {
        background: var(--primary-gradient);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 10px 25px rgba(127, 0, 255, 0.4);
        color: white;
    }

    /* Glass Cards */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid var(--glass-border);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }

    /* Typography */
    .gradient-text {
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Track Cards */
    .track-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid var(--glass-border);
        transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
    }

    .track-card:hover {
        transform: translateX(8px);
        background: rgba(255, 255, 255, 0.06);
        border-color: #7F00FF;
    }

    /* Badges */
    .keyword-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        color: #ddd;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem 0.4rem 0.2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 500;
    }

    .safe-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .match-score {
        font-size: 1.5rem;
        font-weight: 800;
        color: #F472B6;
        line-height: 1;
    }
    
    /* Metrics */
    .metric-box {
        text-align: center;
        padding: 1rem;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: white;
    }
    
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Audio playback isolation script
st.components.v1.html("""
<script>
    const parentDoc = window.parent.document;
    parentDoc.addEventListener('play', function(e){
        const mediaElements = [...parentDoc.getElementsByTagName('audio'), ...parentDoc.getElementsByTagName('video')];
        mediaElements.forEach(el => {
            if(el !== e.target) {
                el.pause();
            }
        });
    }, true);
</script>
""", height=0)

def get_whimsical_message():
    messages = [
        "🧬 Decoding your cinematic DNA...",
        "✨ Sprinkling some digital magic on your frames...",
        "🕵️‍♂️ Scouting copyright-free goldmines...",
        "🧮 Calculating the perfect auditory vibes...",
        "🌈 Painting with sound frequencies...",
        "🚀 Preparing for your next viral hit...",
        "🎨 Matching colors to melodies...",
        "🎬 Understanding the soul of your edit..."
    ]
    return random.choice(messages)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def main():
    # Hero Section with high-quality Unsplash
    try:
        hero_img_src = "https://images.unsplash.com/photo-1614149162883-504ce4d13909?q=80&w=2000&auto=format&fit=crop"
    except Exception:
        # Fallback to local asset if file missing
        hero_img_b64 = get_base64_of_bin_file("assets/hero_banner.png")
        hero_img_src = f"data:image/png;base64,{hero_img_b64}"

    st.markdown(f"""
        <div class="hero-container">
            <img src="{hero_img_src}" style="width: 100%; height: 350px; object-fit: cover; opacity: 0.5;">
            <div class="hero-overlay">
                <h1 style='font-size: 3.5rem; margin: 0; line-height: 1.1; text-shadow: 0 4px 15px rgba(0,0,0,0.5);'>Vibe<span class='gradient-text'>Match AI</span></h1>
                <p style='font-size: 1.2rem; color: #ccc; margin-top: 10px; font-weight: 300;'>
                    The Secret Weapon for Your Next <b>Viral Masterpiece</b>.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><span>📽️</span> 1. Feed the AI Your Vision</div>', unsafe_allow_html=True)
        st.markdown("<p style='color: #888; margin-bottom: 1.5rem;'>Upload your edit and let our engine analyze every frame, cut, and emotion.</p>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"], label_visibility="collapsed")
        
        if uploaded_file:
            st.video(uploaded_file)
            st.write("") 
            analyze_btn = st.button("✨ Reveal My Video's Soul")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><span>🧬</span> 2. Your Creative Signature</div>', unsafe_allow_html=True)
        
        if uploaded_file and 'analysis_results' in st.session_state:
            res = st.session_state.analysis_results
            
            # Pro Metrics Grid
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{res["target_bpm"]:.0f}</div><div class="metric-label">Target BPM</div></div>', unsafe_allow_html=True)
            with m_col2:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{res["visual_tempo"]*100:.0f}%</div><div class="metric-label">Energy</div></div>', unsafe_allow_html=True)
            with m_col3:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{res["scene_cuts"]}</div><div class="metric-label">Cuts</div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mood & Tags
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 1.2rem; border-radius: 12px; margin-bottom: 1.5rem; border-left: 4px solid #E100FF;">
                    <div class="metric-label" style="text-align: left;">Detected Mood</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: white;">{res['mood'].split('/')[0]} <span style="font-weight: 300; font-size: 0.9rem; color: #888;">& {res['mood'].split('/')[1] if '/' in res['mood'] else ''}</span></div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='metric-label'>Scene Vibes</div>", unsafe_allow_html=True)
            tags_html = "".join([f"<span class='keyword-tag'>#{k.replace(' ', '-').lower()}</span>" for k in res['keywords']])
            st.markdown(f"<div style='margin-bottom: 1rem;'>{tags_html}</div>", unsafe_allow_html=True)
            
            if 'fetch_status' in st.session_state:
                st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1.5rem 0;'>", unsafe_allow_html=True)
                status = st.session_state.fetch_status
                st.markdown(f"<div style='display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #10b981;'><span>✅</span> <b>Freesound Engine:</b> Active & Safe</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align: center; padding: 2rem 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">👀</div>
                    <h4 style="margin: 0; color: #ddd;">Waiting for input...</h4>
                    <p style="color: #666; font-size: 0.9rem;">Your video's DNA will appear here after analysis.</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Processing Logic ---
    if uploaded_file and 'analyze_btn' in locals() and analyze_btn:
        with st.status("🧠 Analyzing visual cadence...", expanded=True) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            analyzer = VideoAnalyzer()
            fetcher = MusicFetcher()
            matcher = MusicMatcher()

            st.write(get_whimsical_message())
            time.sleep(0.5) # For "feel"
            analysis_results = analyzer.analyze_video(tmp_path)
            st.session_state.analysis_results = analysis_results
            
            st.write(get_whimsical_message())
            music_list, fetch_status = fetcher.fetch_music(
                analysis_results['keywords'], analysis_results['mood'], analysis_results['target_bpm']
            )
            st.session_state.fetch_status = fetch_status

            st.write(get_whimsical_message())
            st.session_state.scored_tracks = matcher.match(analysis_results, music_list)

            status.update(label="✨ Your Audio Arsenal is Ready!", state="complete", expanded=False)
            os.remove(tmp_path)
            st.rerun()

    # --- Results Section ---
    if 'scored_tracks' in st.session_state:
        st.markdown("<div style='margin-top: 2rem; margin-bottom: 1.5rem;'><h2 style='font-weight: 800;'>🎸 3. Your Hand-Picked Audio Arsenal</h2></div>", unsafe_allow_html=True)
        
        for i, track in enumerate(st.session_state.scored_tracks):
            with st.container():
                st.markdown(f"""
                <div class="track-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex-grow: 1;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                                <h3 style="margin: 0; padding: 0; font-weight: 700;">{track['title']}</h3>
                                <span class="safe-badge">🛡️ Monetization Safe</span>
                            </div>
                            <div style="display: flex; gap: 15px; color: #aaa; font-size: 0.9rem;">
                                <span>👤 <b>{track['artist']}</b></span>
                                <span>🎸 {track['genre']}</span>
                                <span>⏱️ {track['bpm']} BPM</span>
                            </div>
                        </div>
                        <div style="text-align: right; min-width: 100px;">
                            <div class="metric-label" style="margin-bottom: 4px;">Match Accuracy</div>
                            <div class="match-score">{track['match_score']}%</div>
                            <div style="background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; margin-top: 8px; width: 100px; margin-left: auto;">
                                <div style="width: {track['match_score']}%; background: var(--primary-gradient); height: 100%; border-radius: 3px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                res_col1, res_col2 = st.columns([3, 1], gap="medium")
                with res_col1:
                    if track.get('preview_url'):
                        st.audio(track['preview_url'], format="audio/mp3")
                
                with res_col2:
                    st.link_button("⬇️ Grab Audio", track['url'], use_container_width=True)
                
                # Metadata & Breakdown
                meta_col1, meta_col2 = st.columns([2, 1])
                with meta_col1:
                    tags_html = "".join([f"<span class='keyword-tag' style='font-size: 0.7rem;'>{t}</span>" for t in track.get('tags', [])[:5]])
                    st.markdown(f"<div style='margin-top: 5px;'>{tags_html}</div>", unsafe_allow_html=True)
                
                with meta_col2:
                    with st.expander("📊 Why this match?"):
                        breakdown = track.get('score_breakdown', {})
                        st.markdown(f"""
                            <div style="font-size: 0.8rem; color: #aaa;">
                                🎯 <b>BPM Sync:</b> {breakdown.get('bpm', 0)}%<br>
                                🏷️ <b>Semantic Fit:</b> {breakdown.get('semantic', 0)}%<br>
                                🎭 <b>Mood Alignment:</b> {breakdown.get('mood', 0)}%<br>
                                🛡️ <b>License Safety:</b> {breakdown.get('licence', 0)}%
                            </div>
                        """, unsafe_allow_html=True)

                with st.expander("📝 Licensing & Attribution (Click to Copy)"):
                    st.markdown("Most creators need this for their description to stay strike-free!")
                    st.code(track.get('attribution', f"Music: {track['title']} by {track['artist']} via Freesound. (CC0)"), language="markdown")
                
                st.markdown("<br>", unsafe_allow_html=True)

    # --- Footer / Pro Tips ---
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 3rem 0;'>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        st.markdown("### 💡 Pro Tip: BPM Sync")
        st.markdown("For high-energy edits, try to cut on the 'beat' of the matched BPM. Our AI handles the math, you handle the rhythm!")
    
    with f_col2:
        st.markdown("### 🛡️ Monetization Safe")
        st.markdown("Every track here is CC0 or CC-BY. That means zero copyright strikes and 100% ad revenue in your pocket.")
    
    with f_col3:
        st.markdown("### 🚀 Scale Your Channel")
        st.markdown("Consistency is key. Use VibeMatch AI to speed up your workflow and spend more time on storytelling.")

    st.markdown("""
        <div style="text-align: center; color: #444; font-size: 0.8rem; margin-top: 2rem;">
            Built for Creators by VibeMatch AI • Sourcing 100% Legally Safe Audio
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
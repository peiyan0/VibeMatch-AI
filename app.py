import streamlit as st
import os
import tempfile
from src.analyzer import VideoAnalyzer
from src.music_fetcher import MusicFetcher
from src.matcher import MusicMatcher
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SonicScout | Creator Music Matchmaker",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling (Theme-Agnostic) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 700;
        font-size: 0.95rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        width: 100%;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
    }

    /* Glass Cards - Uses Native Theme Variables */
    .glass-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(128, 128, 128, 0.15);
        margin-bottom: 1rem;
    }

    /* Typography */
    .gradient-text {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Track Cards - Compacted for Scannability */
    .track-card {
        background-color: var(--background-color);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-left: 5px solid #4facfe;
        border-top: 1px solid rgba(128, 128, 128, 0.15);
        border-right: 1px solid rgba(128, 128, 128, 0.15);
        border-bottom: 1px solid rgba(128, 128, 128, 0.15);
        transition: transform 0.2s ease;
    }

    .track-card:hover {
        transform: translateX(3px);
        border-color: rgba(79, 172, 254, 0.5);
    }

    /* Badges & Tags */
    .keyword-tag {
        display: inline-block;
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem 0.2rem 0.2rem 0;
        border: 1px solid rgba(128, 128, 128, 0.3);
    }

    .safe-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .match-score {
        font-size: 1.2rem;
        font-weight: 800;
        color: #4facfe;
    }
    
    /* Utility for secondary text */
    .text-secondary {
        color: rgba(128, 128, 128, 0.9);
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.iframe(src="""
<script>
    const parentDoc = window.parent.document;
    // Listener for exclusive playback across all audio/video elements
    parentDoc.addEventListener('play', function(e){
        const mediaElements = [...parentDoc.getElementsByTagName('audio'), ...parentDoc.getElementsByTagName('video')];
        mediaElements.forEach(el => {
            if(el !== e.target) {
                el.pause();
            }
        });
    }, true);
</script>
""", height=1)

# --- App Logic ---
def main():
    # Hero Section - Compacted
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0 2rem 0;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.2rem;'>🎵 Sonic<span class='gradient-text'>Scout</span></h1>
            <p class='text-secondary' style='max-width: 600px; margin: 0 auto;'>
                The AI music matchmaker for creators. Find <b>100% Monetization-Safe</b> tracks that fit your video's exact vibe.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="medium")

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 1️⃣ Drop Your Clip")
        st.markdown("<p class='text-secondary'>Upload a sample scene to analyze its visual energy.</p>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("", type=["mp4", "mov", "avi"], label_visibility="collapsed")
        
        if uploaded_file:
            st.video(uploaded_file)
            st.write("") 
            analyze_btn = st.button("✨ Analyze Vibe & Match Music")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 2️⃣ Video DNA")
        
        if uploaded_file and 'analysis_results' in st.session_state:
            res = st.session_state.analysis_results
            
            # Using custom HTML for stats to prevent Streamlit metric truncation
            st.markdown(f"""
                <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                    <div>
                        <div class="text-secondary" style="font-size: 0.8rem; text-transform: uppercase;">Visual Energy</div>
                        <div style="font-size: 1.4rem; font-weight: 700;">{res['visual_tempo']:.2f}</div>
                    </div>
                    <div>
                        <div class="text-secondary" style="font-size: 0.8rem; text-transform: uppercase;">Target Pace</div>
                        <div style="font-size: 1.4rem; font-weight: 700;">{res['target_bpm']:.0f} <span style="font-size: 1rem; font-weight: normal;">BPM</span></div>
                    </div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div class="text-secondary" style="font-size: 0.8rem; text-transform: uppercase;">Detected Mood</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-color);">{res['mood'].title()}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Scene Vibes:**")
            tags_html = "".join([f"<span class='keyword-tag'>#{k.lower()}</span>" for k in res['keywords']])
            st.markdown(f"<div style='margin-bottom: 1rem;'>{tags_html}</div>", unsafe_allow_html=True)
            
            if 'fetch_status' in st.session_state:
                st.markdown("<hr style='border-color: rgba(128,128,128,0.2); margin: 1rem 0;'>", unsafe_allow_html=True)
                status = st.session_state.fetch_status
                st.caption(f"✅ **Freesound (CC0):** {status.get('freesound', 'Active')} connection")
        else:
            st.info("👋 Waiting for your video! Upload a clip to reveal its visual DNA.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Processing Logic ---
    if uploaded_file and 'analyze_btn' in locals() and analyze_btn:
        with st.status("🧠 Analyzing visual cadence and extracting semantics...", expanded=True) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            analyzer = VideoAnalyzer()
            fetcher = MusicFetcher()
            matcher = MusicMatcher()

            st.write("👀 Watching your video...")
            analysis_results = analyzer.analyze_video(tmp_path)
            st.session_state.analysis_results = analysis_results
            
            st.write("🕵️‍♂️ Scouting copyright-free libraries...")
            music_list, fetch_status = fetcher.fetch_music(
                analysis_results['keywords'], analysis_results['mood'], analysis_results['target_bpm']
            )
            st.session_state.fetch_status = fetch_status

            st.write("🧮 Calculating creator match scores...")
            st.session_state.scored_tracks = matcher.match(analysis_results, music_list)

            status.update(label="Matchmaking Complete!", state="complete", expanded=False)
            os.remove(tmp_path)
            st.rerun()

    # --- Results Section ---
    if 'scored_tracks' in st.session_state:
        st.markdown("<h3 style='margin-top: 1rem;'>3️⃣ Your Custom Soundtrack</h3>", unsafe_allow_html=True)
        
        for track in st.session_state.scored_tracks:
            with st.container():
                st.markdown(f"""
                <div class="track-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex-grow: 1;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                                <h4 style="margin: 0; padding: 0;">{track['title']}</h4>
                                <span class="safe-badge">🛡️ Safe</span>
                            </div>
                            <div class="text-secondary" style="font-size: 0.85rem; margin-bottom: 8px;">
                                👤 <b>{track['artist']}</b> &nbsp;•&nbsp; 🎸 {track['genre']} &nbsp;•&nbsp; ⏱️ {track['bpm']} BPM
                            </div>
                        </div>
                        <div style="text-align: right; min-width: 80px;">
                            <div class="match-score">{track['match_score']}%</div>
                            <div style="background: rgba(128,128,128,0.2); height: 4px; border-radius: 2px; margin-top: 4px;">
                                <div style="width: {track['match_score']}%; background: #4facfe; height: 100%; border-radius: 2px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_player, col_actions = st.columns([4, 1])
                
                with col_player:
                    if track.get('preview_url'):
                        st.audio(track['preview_url'], format="audio/mp3")
                    
                    with st.expander("📝 Copy Attribution"):
                        st.code(track.get('attribution', 'No attribution required.'), language="markdown")
                
                with col_actions:
                    st.link_button("⬇️ Download", track['url'], use_container_width=True)
                
                st.write("") # Minimal padding

if __name__ == "__main__":
    main()
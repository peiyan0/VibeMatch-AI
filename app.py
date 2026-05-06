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
    page_title="VibeMatch AI | AI Soundtrack & Royalty-Free Music Generator",
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
        --glass-bg: rgba(128, 128, 128, 0.05);
        --glass-border: rgba(128, 128, 128, 0.1);
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
        background: rgba(128, 128, 128, 0.03);
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
        background: rgba(128, 128, 128, 0.1);
        color: inherit;
        opacity: 0.9;
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
        background: rgba(128, 128, 128, 0.1);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: inherit;
    }
    
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: inherit;
        opacity: 0.8;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- SEO Optimization & Agentic Search Integration (WebMCP) ---
st.iframe("""
<script>
    const parentDoc = window.parent.document;
    
    // 1. Audio Playback Isolation
    parentDoc.addEventListener('play', function(e){
        const mediaElements = [...parentDoc.getElementsByTagName('audio'), ...parentDoc.getElementsByTagName('video')];
        mediaElements.forEach(el => {
            if(el !== e.target) {
                el.pause();
            }
        });
    }, true);

    // 2. Headless Search Engine Optimization (On-Page SEO)
    let metaDesc = parentDoc.querySelector('meta[name="description"]');
    if (!metaDesc) {
        metaDesc = parentDoc.createElement('meta');
        metaDesc.setAttribute('name', 'description');
        parentDoc.head.appendChild(metaDesc);
    }
    metaDesc.setAttribute('content', 'VibeMatch AI is the ultimate intelligent AI soundtrack generator and royalty-free music selection engine for video creators. Find monetization-safe, copyright-free CC0 background music automatically.');

    let metaKeywords = parentDoc.querySelector('meta[name="keywords"]');
    if (!metaKeywords) {
        metaKeywords = parentDoc.createElement('meta');
        metaKeywords.setAttribute('name', 'keywords');
        parentDoc.head.appendChild(metaKeywords);
    }
    metaKeywords.setAttribute('content', 'AI music generator, AI soundtrack generator, royalty-free music generator, background music generator, vlog music generator, copyright-free music, video music, VibeMatch AI');

    // 3. WebMCP Actions Discovery Endpoint Linking (Wave 3 ASO)
    let mcpLink = parentDoc.querySelector('link[rel="mcp-actions"]');
    if (!mcpLink) {
        mcpLink = parentDoc.createElement('link');
        mcpLink.setAttribute('rel', 'mcp-actions');
        parentDoc.head.appendChild(mcpLink);
    }
    mcpLink.setAttribute('href', '/mcp-actions.json');

    // 4. Imperative WebMCP Registration for AI Browsing Agents
    if (window.parent.navigator && 'mcpActions' in window.parent.navigator) {
        window.parent.navigator.mcpActions.register({
            id: 'generate-soundtrack',
            name: 'AI Soundtrack Generator',
            description: 'Selects or generates a 100% legal, monetization-safe background track matching your video\'s visual and emotional rhythm.',
            parameters: {
                type: 'object',
                required: ['video_name'],
                properties: {
                    video_name: {
                        type: 'string',
                        description: 'Name of the video file being analyzed'
                    }
                }
            },
            handler: async (params) => {
                return {
                    success: true,
                    message: 'WebMCP Soundtrack Generator is active. To proceed with background music selection, please upload your video file "' + (params.video_name || '') + '" directly through the drag-and-drop input element on the page.'
                };
            }
        });
    }
</script>
""", height=1)

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
            <img src="{hero_img_src}" style="width: 100%; height: 350px; object-fit: cover; opacity: 0.70;">
            <div class="hero-overlay">
                <h1 style='font-size: 3.5rem; margin: 0; line-height: 1.1; color: white;'>Vibe<span class='gradient-text'>Match AI</span></h1>
                <p style='font-size: 1.2rem; color: #eee; margin-top: 10px; font-weight: 300; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>
                    The Intelligent <b>AI Soundtrack Generator</b> & Selection Engine for Your Next Viral Masterpiece.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><span>📽️</span> 1. Feed the AI Your Vision</div>', unsafe_allow_html=True)
        st.markdown("<p style='opacity: 0.8; margin-bottom: 1.5rem;'>Upload your edit and let our engine analyze every frame, cut, and emotion.</p>", unsafe_allow_html=True)
        
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
                <div style="background: rgba(128, 128, 128, 0.05); padding: 1.2rem; border-radius: 12px; margin-bottom: 1.5rem; border-left: 4px solid #E100FF;">
                    <div class="metric-label" style="text-align: left;">Detected Mood</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: inherit;">{res['mood'].split('/')[0]} <span style="font-weight: 300; font-size: 0.9rem; opacity: 0.8;">& {res['mood'].split('/')[1] if '/' in res['mood'] else ''}</span></div>
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
                    <h4 style="margin: 0; opacity: 1.0;">Waiting for input...</h4>
                    <p style="opacity: 0.8; font-size: 0.9rem;">Your video's DNA will appear here after analysis.</p>
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
                            <div style="display: flex; gap: 15px; opacity: 0.7; font-size: 0.9rem;">
                                <span>👤 <b>{track['artist']}</b></span>
                                <span>🎸 {track['genre']}</span>
                                <span>⏱️ {track['bpm']} BPM</span>
                            </div>
                        </div>
                        <div style="text-align: right; min-width: 100px;">
                            <div class="metric-label" style="margin-bottom: 4px;">Match Accuracy</div>
                            <div class="match-score">{track['match_score']}%</div>
                            <div style="background: rgba(128, 128, 128, 0.1); height: 6px; border-radius: 3px; margin-top: 8px; width: 100px; margin-left: auto;">
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
                            <div style="font-size: 0.8rem; opacity: 0.7;">
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
        <div style="text-align: center; opacity: 0.7; font-size: 0.8rem; margin-top: 2rem;">
            Built for Creators by VibeMatch AI • Intelligent AI Soundtrack Generator
            <div style="margin-top: 15px; display: flex; justify-content: center; gap: 20px;">
                <a href="https://github.com/peiyan0/vibematch-ai" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center; gap: 5px;">
                    <svg height="16" width="16" viewBox="0 0 16 16" style="fill: currentColor;"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
                    GitHub
                </a>
                <a href="https://portfolio-peiyan0s-projects.vercel.app/" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center; gap: 5px;">
                    <svg height="16" width="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                    Portfolio
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
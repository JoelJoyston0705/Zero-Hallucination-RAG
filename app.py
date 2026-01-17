"""
Zero-Hallucination RAG - Premium UI
Industry-standard dark theme with glassmorphism design
"""
import streamlit as st
import os
import time
import config
from security import (
    is_authenticated, render_login_page, logout,
    security_check, record_query, check_rate_limit
)

# Page config
st.set_page_config(
    page_title="Bible RAG | Verified Scripture Search",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# AUTHENTICATION FIRST (Before any UI)
# ========================================
if not is_authenticated():
    render_login_page()
    st.stop()

# ========================================
# GLOBAL DESIGN SYSTEM (CSS)
# ========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&display=swap');

    :root {
        --primary: #ffffff;
        --accent: #7c3aed;
        --bg-main: #0b0b0b;
        --bg-sidebar: #121212;
        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.6);
        --card-bg: #181818;
        --border: rgba(255, 255, 255, 0.1);
    }

    /* Deep Black Background */
    .stApp {
        background: var(--bg-main) !important;
        background-image: none !important;
    }

    #MainMenu, footer, header {visibility: hidden;}

    /* Typography */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    h1, h2, h3, .hero-title {
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        color: var(--text-primary) !important;
    }

    .block-container {
        padding: 4rem 2rem !important;
        max-width: 1100px !important;
    }

    /* Hero Section */
    .hero-badge {
        background: var(--card-bg);
        color: var(--text-primary);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid var(--border);
        display: inline-block;
        margin-bottom: 2rem;
    }

    .hero-title {
        font-size: 5rem !important;
        text-align: left;
        margin-bottom: 0.5rem !important;
        line-height: 1.0 !important;
    }

    .hero-subtitle {
        font-size: 1.25rem;
        color: var(--text-secondary);
        margin-bottom: 4rem;
        max-width: 700px;
    }

    /* Pulse Animation */
    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
    }

    .status-indicator {
        display: inline-block;
        width: 8px; height: 8px;
        background: #4ade80;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-green 2s infinite;
        vertical-align: middle;
    }

    /* Input Console */
    div[data-testid="stTextArea"] textarea {
        background: #1e1e1e !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 1.25rem !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }

    div[data-testid="stTextArea"] textarea::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: rgba(255, 255, 255, 0.3) !important;
    }

    /* Suggestion Pills */
    button[key*="pill_"] {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 100px !important;
        padding: 0.4rem 1.25rem !important;
        font-size: 0.85rem !important;
        width: auto !important;
        min-width: 100px !important;
    }

    /* Answer Card */
    .answer-card {
        background: #121212;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 2rem;
        margin-top: 4rem;
    }

    .metric-badge {
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.8);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Global Button Contrast fix */
    .stButton > button {
        background: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }

    .stButton > button * {
        color: #000000 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'rag' not in st.session_state: st.session_state.rag = None
if 'verified_rag' not in st.session_state: st.session_state.verified_rag = None
if 'answer' not in st.session_state: st.session_state.answer = None

@st.cache_resource
def get_rag():
    try:
        from rag_system import BibleRAG
        return BibleRAG(language="en")
    except Exception as e:
        st.error(f"Error loading RAG: {e}")
        return None

@st.cache_resource
def get_verified_rag(_base_rag):
    try:
        from verifier_agent import VerifiedBibleRAG
        return VerifiedBibleRAG(_base_rag, enable_verification=True)
    except Exception as e:
        st.error(f"Error loading verifier: {e}")
        return None

# Load RAG
if st.session_state.rag is None:
    st.session_state.rag = get_rag()
    if st.session_state.rag:
        st.session_state.verified_rag = get_verified_rag(st.session_state.rag)

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div style="padding: 1rem 0; margin-bottom: 2rem;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #fff; letter-spacing: -0.05em; margin-bottom: 0.5rem;">
                Bible RAG
            </div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; display: flex; align-items: center;">
                <span class="status-indicator"></span> Verified Console
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    username = st.session_state.get('username', 'Guest')
    st.markdown(f"""
        <div style="background: #1e1e1e; padding: 0.75rem 1rem; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 2rem; display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.2rem;">👤</span>
            <div><div style="font-size: 0.85rem; font-weight: 700; color: #fff;">{username}</div><div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">Research Access</div></div>
        </div>
    """, unsafe_allow_html=True)

    _, _, remaining = check_rate_limit()
    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <div style="color: rgba(255,255,255,0.4); font-size: 0.7rem; text-transform: uppercase; font-weight: 800; letter-spacing: 0.1em; margin-bottom: 1rem;">System Status</div>
            <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem; border: 1px solid var(--border);">
                <div style="color: rgba(255,255,255,0.5); font-size: 0.75rem; margin-bottom: 0.5rem;">Queries Token</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #fff;">{remaining}<span style="font-size: 0.9rem; color: rgba(255,255,255,0.2);"> / 10</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🛠️ System Intelligence"):
        st.markdown("""<div style="color: rgba(255,255,255,0.5); font-size: 0.8rem; line-height: 2; padding: 0.5rem 0;">• Model: <span style="color:#fff;">GPT-4o-mini</span><br>• Store: <span style="color:#fff;">FAISS Vector</span><br>• Agent: <span style="color:#4ade80;">Active ✓</span></div>""", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        logout()
        st.rerun()

# Hero
st.markdown('''
    <div style="margin-top: 2rem; margin-bottom: 4rem;">
        <span class="hero-badge">Divine Intelligence</span>
        <div class="hero-title" style="font-size: 6rem !important;">The Verified<br>Bible RAG</div>
        <div class="hero-subtitle">A high-fidelity research application designed for grounded biblical analysis.</div>
    </div>
''', unsafe_allow_html=True)

# Main Input
if st.session_state.rag:
    col1, col2 = st.columns([12, 1])
    with col1:
        question = st.text_area("prompt", placeholder="Send a message... (Enter to search, Shift+Enter for new line)", height=120, label_visibility="collapsed", key="bible_prompt")
    with col2:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)
        search = st.button("⮕", key="search_btn")
    
    # Enter-to-Submit JS
    import streamlit.components.v1 as components
    components.html("""
        <script>
        function setup() {
            const doc = window.parent.document;
            const textarea = doc.querySelector('textarea[aria-label="prompt"]');
            const searchBtn = Array.from(doc.querySelectorAll('button')).find(btn => btn.innerText.includes('⮕'));
            
            if (textarea && searchBtn && !textarea.dataset.listenerAdded) {
                textarea.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        textarea.blur();
                        setTimeout(() => { searchBtn.click(); }, 150);
                    }
                });
                textarea.dataset.listenerAdded = 'true';
            }
        }
        setInterval(setup, 1000);
        </script>
        """, height=0)

    if search and question:
        is_allowed, query, err = security_check(question)
        if not is_allowed: st.error(f"⚠️ {err}")
        else:
            with st.spinner(""):
                res = st.session_state.verified_rag.query(query) if st.session_state.verified_rag else st.session_state.rag.query(query)
                st.session_state.answer = {"q": query, "a": res["answer"], "s": res["sources"], "v": res.get("verification", {})}
                record_query()
                st.rerun()

# Pills
if st.session_state.rag:
    st.markdown('<div class="pills-container" style="margin-top:1rem; display:flex; gap:0.75rem; flex-wrap:wrap;">', unsafe_allow_html=True)
    for text, key in [("Who is Job?", "job"), ("Abraham's life", "abraham"), ("The Law", "law"), ("Meaning of Love", "love")]:
        if st.button(text, key=f"pill_{key}"):
            with st.spinner(""):
                res = st.session_state.verified_rag.query(text) if st.session_state.verified_rag else st.session_state.rag.query(text)
                st.session_state.answer = {"q": text, "a": res["answer"], "s": res["sources"], "v": res.get("verification", {})}
                record_query(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Answer Display
if st.session_state.answer:
    ans = st.session_state.answer
    v = ans.get("v", {})
    rate = v.get("grounding_rate", 0.0)
    
    if v.get("rejected") or rate < 0.5: icon, status, color = "⚠️", "Verification Failed", "#ef4444"
    elif rate < 0.8: icon, status, color = "◑", "Partial Verification", "#fbbf24"
    else: icon, status, color = "🛡️", "Highly Verified", "#4ade80"
    
    sources_html = "".join([f'<span style="background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.6); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:0.4rem 0.8rem; font-size:0.75rem; margin-right:0.5rem;">📖 {s}</span>' for s in ans["s"][:6]])
    
    st.markdown(f'''
<div class="answer-card">
    <div style="color:rgba(255,255,255,0.5); font-size:0.85rem; text-transform:uppercase; font-weight:700; margin-bottom:1rem;">Research Query</div>
    <div style="font-size:1.25rem; font-weight:700; color:#fff; margin-bottom:2rem;">{ans["q"]}</div>
    <div style="display:flex; gap:1rem; margin-bottom:2.5rem;">
        <div class="metric-badge" style="color:{color};">{icon} {status}</div>
        <div class="metric-badge">Accuracy: {rate*100:.0f}%</div>
    </div>
    <div style="font-size:1.1rem; line-height:1.8; color:#fff; border-left:2px solid #333; padding-left:1.5rem; margin-bottom:3rem;">{ans["a"]}</div>
    <div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:1.5rem; border:1px solid rgba(255,255,255,0.1);">
        <div style="color:rgba(255,255,255,0.3); font-size:0.7rem; text-transform:uppercase; font-weight:800; margin-bottom:1rem;">Vector Grounding Sources</div>
        {sources_html}
    </div>
</div>
''', unsafe_allow_html=True)

# Footer
st.markdown('<div style="height:100px;"></div><div style="border-top:1px solid rgba(255,255,255,0.05); padding:2rem 0; color:rgba(255,255,255,0.2); font-size:0.75rem; display:flex; justify-content:space-between;"><div>© 2026 Bible RAG Console • Grounded in Truth</div><div>🛡️ Zero-Hallucination | ✓ Agent Verified</div></div>', unsafe_allow_html=True)

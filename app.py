"""
Scripture Search - Figma-style Design with Security
"""
import streamlit as st
import os
import config
from rag_system import BibleRAG
from security import (
    is_authenticated, render_login_page, logout,
    security_check, record_query, check_rate_limit
)

# Page config
st.set_page_config(
    page_title="Scripture Search",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Figma-style CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    #MainMenu, footer, header {visibility: hidden;}
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #ffffff;
    }
    
    .block-container {
        padding: 2rem 2rem !important;
        max-width: 800px !important;
    }
    
    /* Hero Title */
    .hero-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 600;
        color: #1a1a1a;
        margin: 3rem 0 3rem 0;
        line-height: 1.2;
    }
    
    .hero-highlight {
        color: #1a1a1a;
    }
    
    /* Large Input Box */
    .prompt-container {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
    }
    
    /* Streamlit Input Override */
    .stTextArea > div > div > textarea {
        background: #ffffff !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        font-size: 1rem !important;
        color: #1a1a1a !important;
        resize: none !important;
        min-height: 80px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        box-shadow: none !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: #9ca3af !important;
    }
    
    .stTextArea label {
        display: none !important;
    }
    
    /* ALL Buttons - Default Pill Style */
    .stButton > button {
        background: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 100px !important;
        padding: 0.6rem 1.25rem !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        width: auto !important;
        min-width: auto !important;
    }
    
    .stButton > button:hover {
        background: #f5f5f5 !important;
        border-color: #d1d5db !important;
    }
    
    /* Submit Button Override - Target first column button */
    .stColumn:last-child .stButton > button {
        background: #1a1a1a !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        padding: 0 !important;
        font-size: 1.25rem !important;
    }
    
    .stColumn:last-child .stButton > button:hover {
        background: #333333 !important;
    }
    
    /* Suggestion Pills styling retained */
    .suggestions {
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    
    .suggestion-pill {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 100px;
        padding: 0.6rem 1.25rem;
        font-size: 0.9rem;
        color: #1a1a1a;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .suggestion-pill:hover {
        background: #f5f5f5;
        border-color: #d1d5db;
    }
    
    /* Answer Card */
    .answer-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 2rem 0;
    }
    
    .answer-question {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }
    
    .answer-badge {
        display: inline-block;
        background: #1a1a1a;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    
    .answer-text {
        font-size: 1rem;
        line-height: 1.7;
        color: #1a1a1a;
    }
    
    .sources-row {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
        font-size: 0.8rem;
        color: #6b7280;
    }
    
    /* Footer */
    .footer-info {
        text-align: center;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #f3f4f6;
    }
    
    .footer-badges {
        display: flex;
        justify-content: center;
        gap: 2rem;
        color: #9ca3af;
        font-size: 0.8rem;
    }
    
    .footer-badge {
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #1a1a1a !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'rag' not in st.session_state:
    st.session_state.rag = None
if 'answer' not in st.session_state:
    st.session_state.answer = None

@st.cache_resource
def get_rag():
    try:
        return BibleRAG(language="en")
    except:
        return None

# ========================================
# AUTHENTICATION CHECK
# ========================================
if not is_authenticated():
    render_login_page()
    st.stop()

# ========================================
# AUTHENTICATED CONTENT BELOW
# ========================================

# Load RAG
if st.session_state.rag is None:
    st.session_state.rag = get_rag()

# Show rate limit info in sidebar
with st.sidebar:
    st.markdown("### 🔐 Security")
    _, _, remaining = check_rate_limit()
    st.info(f"Queries remaining: {remaining}/30 per hour")
    if st.button("🚪 Logout"):
        logout()
        st.rerun()

# Hero Title
st.markdown('''
    <div class="hero-title">
        Search the Bible with<br>
        <span class="hero-highlight">Scripture Search 📖</span>
    </div>
''', unsafe_allow_html=True)

# Main Input Area
if st.session_state.rag:
    col1, col2 = st.columns([10, 1])
    
    with col1:
        question = st.text_area(
            "prompt",
            placeholder="Ask any question about the Bible...",
            height=100,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<div style='height: 50px'></div>", unsafe_allow_html=True)
        search = st.button("→")
    
    if search and question:
        # Security check
        is_allowed, sanitized_query, error = security_check(question)
        
        if not is_allowed:
            st.error(f"⚠️ {error}")
        else:
            with st.spinner(""):
                result = st.session_state.rag.query(sanitized_query)
                st.session_state.answer = {"q": sanitized_query, "a": result["answer"], "s": result["sources"]}
                record_query()  # Record for rate limiting
                st.rerun()
    
    # Suggestion Pills
    st.markdown('<div class="suggestions">', unsafe_allow_html=True)
    
    examples = [
        ("Who speaks in Job 38:1?", "job"),
        ("Abraham's promises", "abraham"),
        ("The Ten Commandments", "commandments"),
        ("What is love?", "love")
    ]
    
    cols = st.columns(len(examples))
    for i, (text, key) in enumerate(examples):
        with cols[i]:
            if st.button(text, key=key, use_container_width=True):
                with st.spinner(""):
                    result = st.session_state.rag.query(text)
                    st.session_state.answer = {"q": text, "a": result["answer"], "s": result["sources"]}
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("⚠️ Run `python setup.py` first")

# Answer Display
if st.session_state.answer:
    ans = st.session_state.answer
    text = ans["a"]
    
    badge = "Search Result"
    if "📖 Direct verse" in text:
        badge = "Direct Verse"
        text = text.split("\n\n", 1)[-1] if "\n\n" in text else text
    elif "📚 Thematic" in text:
        badge = "Thematic"
        text = text.split("\n\n", 1)[-1] if "\n\n" in text else text
    
    sources = " • ".join(ans["s"][:6]) if ans["s"] else ""
    
    st.markdown(f'''
        <div class="answer-card">
            <div class="answer-question">❓ {ans["q"]}</div>
            <span class="answer-badge">{badge}</span>
            <div class="answer-text">{text}</div>
            <div class="sources-row">📖 {sources}</div>
        </div>
    ''', unsafe_allow_html=True)

# Footer
st.markdown('''
    <div class="footer-info">
        <div class="footer-badges">
            <span class="footer-badge">🛡️ Scripture only</span>
            <span class="footer-badge">📚 Always cited</span>
            <span class="footer-badge">✓ Zero hallucination</span>
        </div>
    </div>
''', unsafe_allow_html=True)

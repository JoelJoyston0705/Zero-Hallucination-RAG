"""
Security module for Bible RAG application.
Provides input sanitization, rate limiting, content filtering, and authentication.
"""
import re
import html
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
import streamlit as st

# ============================================
# CONFIGURATION
# ============================================

# Password for app access (change this!)
APP_PASSWORD_HASH = hashlib.sha256("scripture2024".encode()).hexdigest()

# Rate limiting
MAX_QUERIES_PER_HOUR = 30
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Query limits
MAX_QUERY_LENGTH = 500
MIN_QUERY_LENGTH = 3

# Blocked patterns (inappropriate content)
BLOCKED_PATTERNS = [
    r'<script',
    r'javascript:',
    r'on\w+\s*=',
    r'data:text/html',
    r'vbscript:',
]

# Off-topic keywords (not Bible-related)
OFF_TOPIC_KEYWORDS = [
    'hack', 'password', 'credit card', 'social security',
    'bank account', 'ignore previous', 'forget instructions',
    'act as', 'pretend to be', 'jailbreak', 'bypass',
]

# ============================================
# INPUT SANITIZATION
# ============================================

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    """
    if not text:
        return ""
    
    # HTML escape
    text = html.escape(text)
    
    # Remove any remaining HTML-like tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def check_blocked_patterns(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if input contains blocked patterns.
    Returns (is_safe, error_message)
    """
    text_lower = text.lower()
    
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, "Input contains blocked content."
    
    return True, None

def check_off_topic(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if query is off-topic (not Bible-related).
    Returns (is_valid, error_message)
    """
    text_lower = text.lower()
    
    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword in text_lower:
            return False, f"Please ask questions related to the Bible only."
    
    return True, None

def validate_query_length(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate query length.
    Returns (is_valid, error_message)
    """
    if len(text) < MIN_QUERY_LENGTH:
        return False, f"Query too short. Please enter at least {MIN_QUERY_LENGTH} characters."
    
    if len(text) > MAX_QUERY_LENGTH:
        return False, f"Query too long. Maximum {MAX_QUERY_LENGTH} characters allowed."
    
    return True, None

def validate_input(text: str) -> Tuple[bool, str, Optional[str]]:
    """
    Complete input validation pipeline.
    Returns (is_valid, sanitized_text, error_message)
    """
    # Sanitize first
    sanitized = sanitize_input(text)
    
    # Check length
    is_valid, error = validate_query_length(sanitized)
    if not is_valid:
        return False, sanitized, error
    
    # Check blocked patterns
    is_valid, error = check_blocked_patterns(sanitized)
    if not is_valid:
        return False, sanitized, error
    
    # Check off-topic
    is_valid, error = check_off_topic(sanitized)
    if not is_valid:
        return False, sanitized, error
    
    return True, sanitized, None

# ============================================
# RATE LIMITING
# ============================================

def init_rate_limit():
    """Initialize rate limiting in session state."""
    if 'query_timestamps' not in st.session_state:
        st.session_state.query_timestamps = []

def check_rate_limit() -> Tuple[bool, Optional[str], int]:
    """
    Check if user is within rate limit.
    Returns (is_allowed, error_message, remaining_queries)
    """
    init_rate_limit()
    
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    # Clean old timestamps
    st.session_state.query_timestamps = [
        ts for ts in st.session_state.query_timestamps 
        if ts > window_start
    ]
    
    query_count = len(st.session_state.query_timestamps)
    remaining = MAX_QUERIES_PER_HOUR - query_count
    
    if query_count >= MAX_QUERIES_PER_HOUR:
        oldest = min(st.session_state.query_timestamps)
        reset_time = oldest + RATE_LIMIT_WINDOW
        wait_minutes = int((reset_time - current_time) / 60) + 1
        return False, f"Rate limit exceeded. Try again in {wait_minutes} minutes.", 0
    
    return True, None, remaining

def record_query():
    """Record a query for rate limiting."""
    init_rate_limit()
    st.session_state.query_timestamps.append(time.time())

# ============================================
# AUTHENTICATION
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str) -> bool:
    """Verify if password is correct."""
    return hash_password(password) == APP_PASSWORD_HASH

def init_auth():
    """Initialize authentication in session state."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

def is_authenticated() -> bool:
    """Check if user is authenticated."""
    init_auth()
    return st.session_state.authenticated

def authenticate(password: str) -> bool:
    """Attempt to authenticate with password."""
    init_auth()
    if verify_password(password):
        st.session_state.authenticated = True
        return True
    return False

def logout():
    """Log out the user."""
    st.session_state.authenticated = False

def render_login_page():
    """Render the login page."""
    st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: 4rem auto;
                padding: 2rem;
                background: #f9fafb;
                border-radius: 16px;
                text-align: center;
            }
            .login-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 0.5rem;
            }
            .login-subtitle {
                color: #6b7280;
                margin-bottom: 1.5rem;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('''
        <div class="login-container">
            <div class="login-title">🔐 Scripture Search</div>
            <div class="login-subtitle">Enter password to continue</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            if authenticate(password):
                st.rerun()
            else:
                st.error("Incorrect password")

# ============================================
# API KEY VALIDATION
# ============================================

def validate_api_key(api_key: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate OpenAI API key format.
    Returns (is_valid, error_message)
    """
    if not api_key:
        return False, "OpenAI API key not found. Set OPENAI_API_KEY in .env file."
    
    # Check format (sk-... or sk-proj-...)
    if not (api_key.startswith('sk-') and len(api_key) > 20):
        return False, "Invalid API key format."
    
    return True, None

# ============================================
# QUERY LOGGING (Optional)
# ============================================

def log_query(query: str, success: bool):
    """
    Log query for audit purposes.
    In production, this would write to a secure log file or database.
    """
    if 'query_log' not in st.session_state:
        st.session_state.query_log = []
    
    st.session_state.query_log.append({
        'timestamp': datetime.now().isoformat(),
        'query': query[:100],  # Truncate for privacy
        'success': success
    })
    
    # Keep only last 50 entries in session
    st.session_state.query_log = st.session_state.query_log[-50:]

# ============================================
# SECURITY MIDDLEWARE
# ============================================

def security_check(query: str) -> Tuple[bool, str, Optional[str]]:
    """
    Complete security check for a query.
    Returns (is_allowed, sanitized_query, error_message)
    """
    # 1. Rate limit check
    is_allowed, error, remaining = check_rate_limit()
    if not is_allowed:
        return False, query, error
    
    # 2. Input validation
    is_valid, sanitized, error = validate_input(query)
    if not is_valid:
        return False, sanitized, error
    
    return True, sanitized, None

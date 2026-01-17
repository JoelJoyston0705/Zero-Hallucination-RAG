"""
Security module for Bible RAG application.
Provides input sanitization, rate limiting, content filtering, and authentication.
"""
import re
import html
import hashlib
import time
import json
import os
import config
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st

# ============================================
# CONFIGURATION
# ============================================

APP_PASSWORD_HASH = hashlib.sha256("scripture2024".encode()).hexdigest()
MAX_QUERIES_PER_HOUR = 10
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
MAX_QUERY_LENGTH = 500
MIN_QUERY_LENGTH = 3

BLOCKED_PATTERNS = [
    r'<script',
    r'javascript:',
    r'on\w+\s*=',
    r'data:text/html',
    r'vbscript:',
]

OFF_TOPIC_KEYWORDS = [
    'hack', 'password', 'credit card', 'social security',
    'bank account', 'ignore previous', 'forget instructions',
    'act as', 'pretend to be', 'jailbreak', 'bypass',
]

# ============================================
# INPUT SANITIZATION
# ============================================

def sanitize_input(text: str) -> str:
    if not text: return ""
    text = html.escape(text)
    text = re.sub(r'<[^>]*>', '', text)
    text = text.replace('\x00', '')
    text = ' '.join(text.split())
    return text.strip()

def check_blocked_patterns(text: str) -> Tuple[bool, Optional[str]]:
    text_lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, "Input contains blocked content."
    return True, None

def check_off_topic(text: str) -> Tuple[bool, Optional[str]]:
    text_lower = text.lower()
    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword in text_lower:
            return False, f"Please ask questions related to the Bible only."
    return True, None

def validate_query_length(text: str) -> Tuple[bool, Optional[str]]:
    if len(text) < MIN_QUERY_LENGTH:
        return False, f"Query too short. Please enter at least {MIN_QUERY_LENGTH} characters."
    if len(text) > MAX_QUERY_LENGTH:
        return False, f"Query too long. Maximum {MAX_QUERY_LENGTH} characters allowed."
    return True, None

def validate_input(text: str) -> Tuple[bool, str, Optional[str]]:
    sanitized = sanitize_input(text)
    is_valid, error = validate_query_length(sanitized)
    if not is_valid: return False, sanitized, error
    is_valid, error = check_blocked_patterns(sanitized)
    if not is_valid: return False, sanitized, error
    is_valid, error = check_off_topic(sanitized)
    if not is_valid: return False, sanitized, error
    return True, sanitized, None

# ============================================
# RATE LIMITING
# ============================================

def init_rate_limit():
    if 'query_timestamps' not in st.session_state:
        st.session_state.query_timestamps = []

def check_rate_limit() -> Tuple[bool, Optional[str], int]:
    username = st.session_state.get('username')
    if not username:
        return True, None, MAX_QUERIES_PER_HOUR
        
    users = load_users()
    user_data = users.get(username, {})
    timestamps = user_data.get("query_timestamps", [])
    
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    # Filter for active window
    active_timestamps = [ts for ts in timestamps if ts > window_start]
    
    # Update user data if changed
    if len(active_timestamps) != len(timestamps):
        users[username]["query_timestamps"] = active_timestamps
        save_users(users)
        
    query_count = len(active_timestamps)
    remaining = MAX_QUERIES_PER_HOUR - query_count
    
    if query_count >= MAX_QUERIES_PER_HOUR:
        oldest = min(active_timestamps)
        reset_time = oldest + RATE_LIMIT_WINDOW
        wait_minutes = int((reset_time - current_time) / 60) + 1
        return False, f"Access limit reached. Tokens reset in {wait_minutes} mins.", 0
        
    return True, None, remaining

def record_query():
    username = st.session_state.get('username')
    if not username:
        return
        
    users = load_users()
    if username in users:
        if "query_timestamps" not in users[username]:
            users[username]["query_timestamps"] = []
        users[username]["query_timestamps"].append(time.time())
        save_users(users)

# ============================================
# USER MANAGEMENT & AUTHENTICATION
# ============================================

def load_users() -> dict:
    if os.path.exists(config.USERS_FILE):
        try:
            with open(config.USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users: dict):
    os.makedirs(os.path.dirname(config.USERS_FILE), exist_ok=True)
    with open(config.USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str) -> Tuple[bool, str]:
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = {
        "password_hash": hash_password(password),
        "created_at": str(datetime.now())
    }
    save_users(users)
    return True, "Registration successful! You can now log in."

def init_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
        
    # Session Persistence Recovery
    if not st.session_state.authenticated:
        try:
            # Check query params for token
            token = st.query_params.get("session_token")
                
            if token:
                users = load_users()
                # Check all users
                for user, data in users.items():
                    if data.get("session_token") == token:
                        st.session_state.authenticated = True
                        st.session_state.username = user
                        st.rerun()
                        return
        except Exception:
            pass

def is_authenticated() -> bool:
    init_auth()
    return st.session_state.authenticated

def authenticate(username: str, password: str) -> bool:
    init_auth()
    users = load_users()
    
    is_success = False
    if username == "admin" and hash_password(password) == APP_PASSWORD_HASH:
        is_success = True
        authenticated_user = "admin"
    elif username in users:
        if users[username]["password_hash"] == hash_password(password):
            is_success = True
            authenticated_user = username
            
    if is_success:
        # Generate persistent session token
        session_token = hashlib.sha256(f"{authenticated_user}{time.time()}".encode()).hexdigest()[:16]
        st.session_state.authenticated = True
        st.session_state.username = authenticated_user
        
        # Save token to user db (Even for admin for persistent experience)
        if authenticated_user == "admin" and "admin" not in users:
            users["admin"] = {"password_hash": APP_PASSWORD_HASH, "is_system": True}
            
        if authenticated_user in users:
            users[authenticated_user]["session_token"] = session_token
            save_users(users)
            
        # Set URL Parameter (Persistence)
        st.query_params["session_token"] = session_token
        return True
    return False

def logout():
    username = st.session_state.get('username')
    if username and username != "admin":
        users = load_users()
        if username in users:
            if "session_token" in users[username]:
                del users[username]["session_token"]
                save_users(users)
                
    st.session_state.authenticated = False
    st.session_state.username = None
    st.query_params.clear()

def render_login_page():
    """Render the AnythngLLM style login page."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
            
            :root {
                --bg-main: #0b0b0b;
                --card-bg: #181818;
                --text-primary: #ffffff;
                --text-secondary: rgba(255, 255, 255, 0.5);
                --border: rgba(255, 255, 255, 0.1);
            }

            #MainMenu, footer, header {visibility: hidden;}
            
            .stApp {
                background: var(--bg-main) !important;
                background-image: none !important;
            }
            
            * { font-family: 'Inter', sans-serif !important; }
            
            .login-container {
                max-width: 440px;
                margin: 4rem auto 0 auto;
                padding: 3.5rem;
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 16px;
                box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
                text-align: center;
            }
            
            .login-title {
                font-size: 2.25rem !important;
                font-weight: 900 !important;
                color: #ffffff !important;
                margin-bottom: 0.75rem !important;
                letter-spacing: -0.04em !important;
                line-height: 1.1 !important;
            }
            
            .login-subtitle {
                color: var(--text-secondary);
                font-size: 1rem;
                margin-bottom: 2.5rem;
                font-weight: 400;
            }
            
            .login-badge {
                display: inline-block;
                background: #ffffff;
                color: #000000;
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-size: 0.7rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 2.5rem;
            }
            
            div[data-testid="stTextInput"] input {
                background-color: #1e1e1e !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                text-shadow: 0 0 0 #ffffff !important; 
                padding: 0.85rem 1rem !important;
                font-size: 1rem !important;
            }
            
            div[data-testid="stTextInput"] input::placeholder {
                color: rgba(255, 255, 255, 0.3) !important;
            }
            
            div[data-testid="stTextInput"] input:focus {
                border-color: rgba(255, 255, 255, 0.3) !important;
                background-color: #252525 !important;
            }
            
            .stTextInput label {
                color: rgba(255, 255, 255, 0.8) !important;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            /* Primary Button styling - High Contrast White */
            .stButton > button, 
            div[data-testid="stFormSubmitButton"] button {
                background: #ffffff !important;
                color: #000000 !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 0.75rem 1.5rem !important;
                font-weight: 700 !important;
                width: 100% !important;
                transition: opacity 0.2s ease !important;
            }

            .stButton > button *,
            div[data-testid="stFormSubmitButton"] button * {
                color: #000000 !important;
            }
            
            .stButton > button:hover,
            div[data-testid="stFormSubmitButton"] button:hover {
                opacity: 0.9 !important;
            }

            /* Secondary button (Toggle) override */
            button[key="mode_toggle"] {
                background: rgba(255, 255, 255, 0.05) !important;
                color: #ffffff !important;
                border: 1px solid var(--border) !important;
            }

            button[key="mode_toggle"] * {
                color: #ffffff !important;
            }

            
            .stAlert {
                background: rgba(239, 68, 68, 0.1) !important;
                border: 1px solid rgba(239, 68, 68, 0.2) !important;
                color: #f87171 !important;
            }

            div[data-testid="stForm"] {
                border: none !important;
                padding: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = "login"

    mode = st.session_state.auth_mode
    title = "Verified Scripture RAG" if mode == "login" else "Create Account"
    subtitle = "Secure portal for grounded biblical analysis" if mode == "login" else "Join the research community"
    
    st.markdown(f'''
        <div class="login-container">
            <span class="login-badge">Divine Intelligence</span>
            <div class="login-title">{title}</div>
            <div class="login-subtitle">{subtitle}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("auth_form", clear_on_submit=False):
            username = st.text_input("Username", key="auth_username", placeholder="Enter username...")
            password = st.text_input("Password", type="password", key="auth_password", placeholder="Enter password...")
            if mode == "register":
                confirm_password = st.text_input("Confirm Password", type="password", key="auth_confirm")
                submit = st.form_submit_button("Register Account", use_container_width=True)
            else:
                submit = st.form_submit_button("Login to System", use_container_width=True)
            
            if submit:
                if mode == "login":
                    if authenticate(username, password):
                        st.success(f"Welcome back! Loading system...")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    if not username or not password:
                        st.error("Please fill in all fields.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        success, message = register_user(username, password)
                        if success:
                            st.success(message)
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(message)
        
        toggle_text = "Don't have an account? Register here" if mode == "login" else "Already have an account? Login here"
        if st.button(toggle_text, use_container_width=True, type="secondary", key="mode_toggle"):
            st.session_state.auth_mode = "register" if mode == "login" else "login"
            st.rerun()

def security_check(query: str) -> Tuple[bool, str, Optional[str]]:
    is_allowed, error, remaining = check_rate_limit()
    if not is_allowed: return False, query, error
    is_valid, sanitized, error = validate_input(query)
    if not is_valid: return False, sanitized, error
    return True, sanitized, None

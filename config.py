import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration - Using OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Free, fast, multilingual support
LLM_MODEL = "gpt-4o-mini"  # Cost-effective OpenAI model
TEMPERATURE = 0.1  # Low temperature for consistency

# Vector Store Configuration
VECTOR_STORE_PATH = "vector_stores"
FAISS_INDEX_EN = "faiss_index_en"
FAISS_INDEX_TA = "faiss_index_ta"

# Data Configuration
DATA_PATH = "data"
BIBLE_DATA_EN = os.path.join(DATA_PATH, "bible_kjv_en.txt")
BIBLE_DATA_TA = os.path.join(DATA_PATH, "bible_kjv_ta.txt")

# RAG Configuration - Optimized for SPEED
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5  # Reduced for faster results
MAX_TOKENS = 300  # Limit response length for speed

# Language Configuration
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ta": "Tamil"
}




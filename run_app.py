"""
Launcher script to avoid segfault issues on macOS.
This preloads the problematic modules before streamlit runs.
"""
import os
import sys

# Set environment variables before any imports
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# Preload the problematic modules
print("Preloading modules...")
import torch
from sentence_transformers import SentenceTransformer
print("Modules loaded successfully!")

# Now run streamlit
if __name__ == "__main__":
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", "app.py", "--server.headless=true"]
    sys.exit(stcli.main())

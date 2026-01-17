import os
import sys
import config

# Lazy load heavy modules
def get_vector_store():
    import torch
    # Force CPU for stability during indexing
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    from vector_store import BibleVectorStore
    return BibleVectorStore

def run_fix():
    print("Starting index fix...")
    from bible_parser import BibleParser
    
    # 1. Parse
    parser = BibleParser(language="en")
    print("Parsing Bible...")
    verses = parser.parse_kjv_text(config.BIBLE_DATA_EN)
    print(f"Parsed {len(verses)} verses")
    
    # 2. Chunk
    print("Creating chunks...")
    chunks = parser.create_chunks(verses, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
    print(f"Created {len(chunks)} chunks")
    
    # 3. Vectorize (Lazy load)
    print("Loading vector store (this may take a moment)...")
    try:
        VectorStoreClass = get_vector_store()
        vector_store = VectorStoreClass(language="en")
        vector_store.create_index(chunks)
        print("SUCCESS: Vector store recreated with fixed indexing!")
    except Exception as e:
        print(f"ERROR during indexing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_fix()

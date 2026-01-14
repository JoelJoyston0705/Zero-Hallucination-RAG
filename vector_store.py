"""
Vector store management using FAISS for Bible RAG.
"""
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from tqdm import tqdm
import config

class BibleVectorStore:
    def __init__(self, language: str = "en"):
        self.language = language
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.index = None
        self.chunks = []
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # Set up paths
        os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)
        index_name = config.FAISS_INDEX_EN if language == "en" else config.FAISS_INDEX_TA
        self.index_path = os.path.join(config.VECTOR_STORE_PATH, f"{index_name}.index")
        self.metadata_path = os.path.join(config.VECTOR_STORE_PATH, f"{index_name}_metadata.pkl")
        
    def create_index(self, chunks: List[Dict]):
        """
        Create FAISS index from Bible chunks.
        """
        print(f"Creating vector index for {self.language} language...")
        self.chunks = chunks
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        print("Generating embeddings...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True, batch_size=32)
        
        # Convert to numpy array
        embeddings = np.array(embeddings).astype('float32')
        self.dimension = embeddings.shape[1]
        
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add embeddings to index
        print("Adding embeddings to FAISS index...")
        self.index.add(embeddings)
        
        print(f"Index created with {self.index.ntotal} vectors")
        
        # Save index and metadata
        self.save_index()
        
    def save_index(self):
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            return
        
        print(f"Saving index to {self.index_path}...")
        faiss.write_index(self.index, self.index_path)
        
        # Save metadata (chunks)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        print("Index saved successfully!")
    
    def load_index(self):
        """Load FAISS index and metadata from disk."""
        if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
            return False
        
        print(f"Loading index from {self.index_path}...")
        self.index = faiss.read_index(self.index_path)
        
        # Load metadata
        with open(self.metadata_path, 'rb') as f:
            self.chunks = pickle.load(f)
        
        print(f"Index loaded with {self.index.ntotal} vectors")
        return True
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar chunks in the vector store.
        Returns top_k most similar chunks with metadata.
        """
        if self.index is None or len(self.chunks) == 0:
            raise ValueError("Index not loaded. Please load or create index first.")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Search in index
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Retrieve chunks with metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    'text': chunk['text'],
                    'references': chunk.get('references', []),
                    'book': chunk.get('book', 'Unknown'),
                    'chapter': chunk.get('chapter', 0),
                    'distance': float(distances[0][i]),
                    'language': chunk.get('language', self.language)
                })
        
        return results




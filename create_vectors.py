"""
Simple vector store creation script
"""
import os
import sys

# Set environment to avoid memory issues
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import config
from bible_parser import BibleParser
from vector_store import BibleVectorStore

def main():
    print('Creating vector store for English Bible...')

    # Parse Bible text
    parser = BibleParser(language='en')
    print('Parsing Bible text...')
    verses = parser.parse_kjv_text('data/bible_kjv_en.txt')
    print(f'Parsed {len(verses)} verses')

    # Create chunks
    print('Creating chunks...')
    chunks = parser.create_chunks(
        verses,
        chunk_size=config.CHUNK_SIZE,
        overlap=config.CHUNK_OVERLAP
    )
    print(f'Created {len(chunks)} chunks')

    # Create vector store
    print('Creating embeddings and vector store...')
    print('This will take a few minutes...')
    vector_store = BibleVectorStore(language='en')
    vector_store.create_index(chunks)
    print('Vector store created successfully!')

if __name__ == '__main__':
    main()

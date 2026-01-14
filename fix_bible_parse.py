"""
Re-parse the Bible with proper book name extraction for Gutenberg format
"""
import os
import re
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import config

def parse_gutenberg_bible(filepath):
    """Parse Gutenberg KJV Bible format."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    verses = []
    lines = text.split('\n')
    
    # Book name patterns for Gutenberg format
    book_patterns = [
        r"The First Book of Moses: Called Genesis",
        r"The Second Book of Moses: Called Exodus", 
        r"The Third Book of Moses: Called Leviticus",
        r"The Fourth Book of Moses: Called Numbers",
        r"The Fifth Book of Moses: Called Deuteronomy",
        r"The Book of Joshua",
        r"The Book of Judges",
        r"The Book of Ruth",
        r"The First Book of Samuel",
        r"The Second Book of Samuel",
        r"The First Book of the Kings",
        r"The Second Book of the Kings",
        r"The First Book of the Chronicles",
        r"The Second Book of the Chronicles",
        r"Ezra",
        r"The Book of Nehemiah",
        r"The Book of Esther",
        r"The Book of Job",
        r"The Book of Psalms",
        r"The Proverbs",
        r"Ecclesiastes",
        r"The Song of Solomon",
        r"The Book of the Prophet Isaiah",
        r"The Book of the Prophet Jeremiah",
        r"The Lamentations of Jeremiah",
        r"The Book of the Prophet Ezekiel",
        r"The Book of Daniel",
        r"Hosea",
        r"Joel",
        r"Amos",
        r"Obadiah",
        r"Jonah",
        r"Micah",
        r"Nahum",
        r"Habakkuk",
        r"Zephaniah",
        r"Haggai",
        r"Zechariah",
        r"Malachi",
        r"The Gospel According to Saint Matthew",
        r"The Gospel According to Saint Mark",
        r"The Gospel According to Saint Luke",
        r"The Gospel According to Saint John",
        r"The Acts of the Apostles",
        r"The Epistle.*to the Romans",
        r"The First Epistle.*to the Corinthians",
        r"The Second Epistle.*to the Corinthians",
        r"The Epistle.*to the Galatians",
        r"The Epistle.*to the Ephesians",
        r"The Epistle.*to the Philippians",
        r"The Epistle.*to the Colossians",
        r"The First Epistle.*to the Thessalonians",
        r"The Second Epistle.*to the Thessalonians",
        r"The First Epistle.*to Timothy",
        r"The Second Epistle.*to Timothy",
        r"The Epistle.*to Titus",
        r"The Epistle.*to Philemon",
        r"The Epistle.*to the Hebrews",
        r"The General Epistle of James",
        r"The First Epistle.*of Peter",
        r"The Second.*Epistle.*of Peter",
        r"The First Epistle.*of John",
        r"The Second Epistle.*of John",
        r"The Third Epistle.*of John",
        r"The General Epistle of Jude",
        r"The Revelation"
    ]
    
    # Short book names for references
    book_short_names = {
        "Genesis": "Genesis", "Exodus": "Exodus", "Leviticus": "Leviticus",
        "Numbers": "Numbers", "Deuteronomy": "Deuteronomy", "Joshua": "Joshua",
        "Judges": "Judges", "Ruth": "Ruth", "Samuel": "Samuel", "Kings": "Kings",
        "Chronicles": "Chronicles", "Ezra": "Ezra", "Nehemiah": "Nehemiah",
        "Esther": "Esther", "Job": "Job", "Psalms": "Psalms", "Proverbs": "Proverbs",
        "Ecclesiastes": "Ecclesiastes", "Song": "Song of Solomon", "Isaiah": "Isaiah",
        "Jeremiah": "Jeremiah", "Lamentations": "Lamentations", "Ezekiel": "Ezekiel",
        "Daniel": "Daniel", "Hosea": "Hosea", "Joel": "Joel", "Amos": "Amos",
        "Obadiah": "Obadiah", "Jonah": "Jonah", "Micah": "Micah", "Nahum": "Nahum",
        "Habakkuk": "Habakkuk", "Zephaniah": "Zephaniah", "Haggai": "Haggai",
        "Zechariah": "Zechariah", "Malachi": "Malachi", "Matthew": "Matthew",
        "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts",
        "Romans": "Romans", "Corinthians": "Corinthians", "Galatians": "Galatians",
        "Ephesians": "Ephesians", "Philippians": "Philippians", "Colossians": "Colossians",
        "Thessalonians": "Thessalonians", "Timothy": "Timothy", "Titus": "Titus",
        "Philemon": "Philemon", "Hebrews": "Hebrews", "James": "James",
        "Peter": "Peter", "Jude": "Jude", "Revelation": "Revelation"
    }
    
    current_book = None
    current_book_short = "Unknown"
    verse_pattern = re.compile(r'^(\d+):(\d+)\s+(.+)$')
    
    verse_text_buffer = []
    current_chapter = None
    current_verse = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line is a book name
        is_book = False
        for pattern in book_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                current_book = line
                # Extract short name
                for short, full in book_short_names.items():
                    if short.lower() in line.lower():
                        current_book_short = full
                        break
                is_book = True
                break
        
        if is_book:
            # Save any buffered verse
            if verse_text_buffer and current_chapter and current_verse:
                full_text = ' '.join(verse_text_buffer)
                verses.append({
                    'book': current_book_short,
                    'chapter': current_chapter,
                    'verse': current_verse,
                    'text': full_text,
                    'reference': f"{current_book_short} {current_chapter}:{current_verse}"
                })
                verse_text_buffer = []
            continue
        
        # Check for verse pattern
        match = verse_pattern.match(line)
        if match:
            # Save previous verse if exists
            if verse_text_buffer and current_chapter and current_verse:
                full_text = ' '.join(verse_text_buffer)
                verses.append({
                    'book': current_book_short,
                    'chapter': current_chapter,
                    'verse': current_verse,
                    'text': full_text,
                    'reference': f"{current_book_short} {current_chapter}:{current_verse}"
                })
            
            current_chapter = int(match.group(1))
            current_verse = int(match.group(2))
            verse_text_buffer = [match.group(3)]
        else:
            # Continuation of previous verse
            if line and not line.startswith('***') and current_chapter:
                verse_text_buffer.append(line)
    
    # Save last verse
    if verse_text_buffer and current_chapter and current_verse:
        full_text = ' '.join(verse_text_buffer)
        verses.append({
            'book': current_book_short,
            'chapter': current_chapter,
            'verse': current_verse,
            'text': full_text,
            'reference': f"{current_book_short} {current_chapter}:{current_verse}"
        })
    
    return verses

def create_chunks(verses, chunk_size=500, overlap=50):
    """Create chunks from verses."""
    chunks = []
    current_text = []
    current_references = []
    current_book = None
    current_chapter = None
    
    for verse in verses:
        book = verse['book']
        chapter = verse['chapter']
        
        # Save chunk if needed
        if (current_book and current_book != book) or \
           (current_chapter and current_chapter != chapter) or \
           (len(' '.join(current_text)) > chunk_size):
            
            if current_text:
                chunks.append({
                    'text': ' '.join(current_text),
                    'references': list(set(current_references)),
                    'book': current_book,
                    'chapter': current_chapter,
                    'language': 'en'
                })
                current_text = []
                current_references = []
        
        current_book = book
        current_chapter = chapter
        current_text.append(verse['text'])
        current_references.append(verse['reference'])
    
    # Add remaining
    if current_text:
        chunks.append({
            'text': ' '.join(current_text),
            'references': list(set(current_references)),
            'book': current_book,
            'chapter': current_chapter,
            'language': 'en'
        })
    
    return chunks

def main():
    print("Re-parsing Bible with proper format...")
    
    # Parse Bible
    verses = parse_gutenberg_bible('data/bible_kjv_en.txt')
    print(f"Parsed {len(verses)} verses")
    
    # Show sample
    print("\nSample verses:")
    for v in verses[:5]:
        print(f"  {v['reference']}: {v['text'][:50]}...")
    
    # Create chunks
    chunks = create_chunks(verses, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
    print(f"\nCreated {len(chunks)} chunks")
    
    # Create embeddings
    print("\nLoading embedding model...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    
    print("Creating embeddings (this takes a few minutes)...")
    texts = [chunk['text'] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embeddings = np.array(embeddings).astype('float32')
    
    # Create FAISS index
    print("Creating FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"Index created with {index.ntotal} vectors")
    
    # Save
    os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)
    index_path = os.path.join(config.VECTOR_STORE_PATH, f"{config.FAISS_INDEX_EN}.index")
    metadata_path = os.path.join(config.VECTOR_STORE_PATH, f"{config.FAISS_INDEX_EN}_metadata.pkl")
    
    faiss.write_index(index, index_path)
    with open(metadata_path, 'wb') as f:
        pickle.dump(chunks, f)
    
    print(f"\nVector store saved!")
    print("Done! Restart the app to see proper book names.")

if __name__ == '__main__':
    main()

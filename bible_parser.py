"""
Parse Bible text files into structured format for RAG.
"""
import re
import os
from typing import List, Dict

class BibleParser:
    def __init__(self, language: str = "en"):
        self.language = language
        
    def parse_kjv_text(self, filepath: str) -> List[Dict]:
        """
        Parse KJV Bible text file into structured verses.
        Returns list of dictionaries with book, chapter, verse, text.
        Handles multiple formats: eBible, standard KJV, etc.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Bible file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        verses = []
        lines = text.split('\n')
        
        # Pattern 1: "Book Chapter:Verse Text" (eBible format)
        ebible_pattern = re.compile(r'^([A-Z][A-Za-z\s]+?)\s+(\d+):(\d+)\s+(.+)$')
        
        # Pattern 2: "Chapter:Verse Text" (with book context)
        verse_pattern = re.compile(r'^(\d+):(\d+)\s+(.+)$')
        
        # Pattern 3: Book name on its own line
        book_pattern = re.compile(r'^(THE\s+)?([A-Z\s]{3,})$')
        
        current_book = None
        current_chapter = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Try eBible format first: "Book Chapter:Verse Text"
            ebible_match = ebible_pattern.match(line)
            if ebible_match:
                book, chapter, verse, content = ebible_match.groups()
                current_book = book.strip().title()
                current_chapter = int(chapter)
                verses.append({
                    'book': current_book,
                    'chapter': current_chapter,
                    'verse': int(verse),
                    'text': content.strip(),
                    'reference': f"{current_book} {chapter}:{verse}"
                })
                continue
            
            # Try book name detection (all caps, 3+ chars, reasonable length)
            if book_pattern.match(line) and 3 <= len(line.split()) <= 5 and len(line) < 30:
                # Check if it's actually a book name (not just random caps)
                potential_book = line.title().strip()
                # Common Bible books
                common_books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
                               'Joshua', 'Judges', 'Ruth', 'Samuel', 'Kings', 'Chronicles',
                               'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
                               'Ecclesiastes', 'Song', 'Isaiah', 'Jeremiah', 'Lamentations',
                               'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah',
                               'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai',
                               'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John',
                               'Acts', 'Romans', 'Corinthians', 'Galatians', 'Ephesians',
                               'Philippians', 'Colossians', 'Thessalonians', 'Timothy',
                               'Titus', 'Philemon', 'Hebrews', 'James', 'Peter', 'John',
                               'Jude', 'Revelation']
                
                # Check if any common book name is in the line
                if any(book in potential_book for book in common_books):
                    current_book = potential_book
                    continue
            
            # Try simple verse pattern: "Chapter:Verse Text"
            verse_match = verse_pattern.match(line)
            if verse_match:
                chapter, verse, content = verse_match.groups()
                current_chapter = int(chapter)
                if current_book:
                    verses.append({
                        'book': current_book,
                        'chapter': current_chapter,
                        'verse': int(verse),
                        'text': content.strip(),
                        'reference': f"{current_book} {chapter}:{verse}"
                    })
                else:
                    # Create verse without book name (will be set later)
                    verses.append({
                        'book': 'Unknown',
                        'chapter': current_chapter,
                        'verse': int(verse),
                        'text': content.strip(),
                        'reference': f"Unknown {chapter}:{verse}"
                    })
                continue
            
            # Continuation of previous verse (if we have context)
            if verses and current_book:
                # Append to last verse if it's clearly continuation text
                if len(line) > 10 and not line[0].isdigit():
                    verses[-1]['text'] += ' ' + line
        
        # If we still don't have enough verses, try alternative parsing
        if len(verses) < 100:
            print(f"Warning: Only found {len(verses)} verses. Trying alternative parsing...")
            alt_verses = self._parse_alternative_format(text)
            if len(alt_verses) > len(verses):
                verses = alt_verses
        
        # Clean up and validate verses
        verses = [v for v in verses if v['text'].strip() and len(v['text'].strip()) > 5]
        
        print(f"Parsed {len(verses)} verses from Bible text")
        return verses
    
    def _parse_alternative_format(self, text: str) -> List[Dict]:
        """Alternative parsing for different Bible text formats."""
        verses = []
        
        # Try to find verse references in text
        # Pattern: Book Chapter:Verse or (Book Chapter:Verse)
        verse_ref_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+):(\d+)')
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            matches = verse_ref_pattern.findall(sentence)
            if matches:
                for match in matches:
                    book, chapter, verse = match
                    # Extract text after reference
                    text_part = sentence.split(f"{book} {chapter}:{verse}")[-1].strip()
                    if text_part:
                        verses.append({
                            'book': book,
                            'chapter': int(chapter),
                            'verse': int(verse),
                            'text': text_part,
                            'reference': f"{book} {chapter}:{verse}"
                        })
            else:
                # If no reference found, create a general entry
                if len(sentence) > 20:  # Only include substantial sentences
                    verses.append({
                        'book': 'Unknown',
                        'chapter': 1,
                        'verse': len(verses) + 1,
                        'text': sentence,
                        'reference': f"Unknown {1}:{len(verses) + 1}"
                    })
        
        return verses if verses else self._parse_simple_format(text)
    
    def _parse_simple_format(self, text: str) -> List[Dict]:
        """Simple format: split by paragraphs and create verses."""
        verses = []
        paragraphs = text.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) > 10:  # Only include substantial paragraphs
                verses.append({
                    'book': 'Unknown',
                    'chapter': (i // 50) + 1,
                    'verse': (i % 50) + 1,
                    'text': para,
                    'reference': f"Passage {i + 1}"
                })
        
        return verses
    
    def create_chunks(self, verses: List[Dict], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Create overlapping chunks from verses for embedding.
        """
        chunks = []
        
        # Group verses by book and chapter
        current_book = None
        current_chapter = None
        current_text = []
        current_references = []
        
        for verse in verses:
            book = verse['book']
            chapter = verse['chapter']
            verse_text = verse['text']
            reference = verse['reference']
            
            # If new book/chapter or chunk too large, save current chunk
            if (current_book and current_book != book) or \
               (current_chapter and current_chapter != chapter) or \
               (len(' '.join(current_text)) > chunk_size):
                
                if current_text:
                    chunk_text = ' '.join(current_text)
                    chunks.append({
                        'text': chunk_text,
                        'references': list(set(current_references)),
                        'book': current_book,
                        'chapter': current_chapter,
                        'language': self.language
                    })
                
                # Start new chunk with overlap
                if overlap > 0 and current_text:
                    overlap_words = ' '.join(current_text[-overlap:]).split()
                    current_text = overlap_words
                    current_references = current_references[-overlap:]
                else:
                    current_text = []
                    current_references = []
            
            current_book = book
            current_chapter = chapter
            current_text.append(verse_text)
            current_references.append(reference)
            
            # Create chunk if size reached
            if len(' '.join(current_text)) >= chunk_size:
                chunk_text = ' '.join(current_text)
                chunks.append({
                    'text': chunk_text,
                    'references': list(set(current_references)),
                    'book': current_book,
                    'chapter': current_chapter,
                    'language': self.language
                })
                
                # Keep overlap for next chunk
                if overlap > 0:
                    overlap_words = ' '.join(current_text[-overlap:]).split()
                    current_text = overlap_words
                    current_references = current_references[-overlap:]
                else:
                    current_text = []
                    current_references = []
        
        # Add remaining text as final chunk
        if current_text:
            chunk_text = ' '.join(current_text)
            chunks.append({
                'text': chunk_text,
                'references': list(set(current_references)),
                'book': current_book,
                'chapter': current_chapter,
                'language': self.language
            })
        
        return chunks


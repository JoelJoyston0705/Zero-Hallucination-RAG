"""
Download King James Version Bible text from public domain sources.
"""
import os
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path

def download_kjv_english():
    """Download King James Version Bible in English from public domain source."""
    print("Downloading KJV Bible (English)...")
    
    # Try multiple sources for reliability (ordered by preference)
    sources = [
        # Source 1: eBible corpus (most reliable format)
        "https://raw.githubusercontent.com/BibleNLP/ebible/master/corpus/eng-kjv2006.txt",
        # Source 2: Alternative GitHub source
        "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/cross_references/t_kjv.txt",
        # Source 3: Direct text file
        "https://raw.githubusercontent.com/githubuser0xFFFF/Quran-Translation/master/Other%20Religious%20Texts/Bible/KJV.txt",
    ]
    
    for source_url in sources:
        try:
            print(f"Trying source: {source_url[:60]}...")
            response = requests.get(source_url, timeout=60, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200 and len(response.text) > 10000:
                print(f"✓ Successfully downloaded from source (size: {len(response.text)} characters)")
                return response.text
            else:
                print(f"  Response status: {response.status_code}, Size: {len(response.text) if response.text else 0}")
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    print("All direct sources failed. Trying alternative method...")
    
    # Fallback: Download book by book using bible-api.com
    print("Using bible-api.com to download book by book...")
    books = [
        ("genesis", 50), ("exodus", 40), ("leviticus", 27), ("numbers", 36), ("deuteronomy", 34),
        ("joshua", 24), ("judges", 21), ("ruth", 4), ("1 samuel", 31), ("2 samuel", 24),
        ("1 kings", 22), ("2 kings", 25), ("1 chronicles", 29), ("2 chronicles", 36), ("ezra", 10),
        ("nehemiah", 13), ("esther", 10), ("job", 42), ("psalms", 150), ("proverbs", 31),
        ("ecclesiastes", 12), ("song of solomon", 8), ("isaiah", 66), ("jeremiah", 52), ("lamentations", 5),
        ("ezekiel", 48), ("daniel", 12), ("hosea", 14), ("joel", 3), ("amos", 9),
        ("obadiah", 1), ("jonah", 4), ("micah", 7), ("nahum", 3), ("habakkuk", 3),
        ("zephaniah", 3), ("haggai", 2), ("zechariah", 14), ("malachi", 4),
        ("matthew", 28), ("mark", 16), ("luke", 24), ("john", 21), ("acts", 28),
        ("romans", 16), ("1 corinthians", 16), ("2 corinthians", 13), ("galatians", 6), ("ephesians", 6),
        ("philippians", 4), ("colossians", 4), ("1 thessalonians", 5), ("2 thessalonians", 3), ("1 timothy", 6),
        ("2 timothy", 4), ("titus", 3), ("philemon", 1), ("hebrews", 13), ("james", 5),
        ("1 peter", 5), ("2 peter", 3), ("1 john", 5), ("2 john", 1), ("3 john", 1),
        ("jude", 1), ("revelation", 22)
    ]
    
    full_bible = []
    base_url = "https://bible-api.com/"
    
    import time
    for book_name, num_chapters in books:
        book_text = []
        book_display = book_name.replace(" ", " ").title()
        
        for chapter in range(1, num_chapters + 1):
            try:
                book_encoded = book_name.replace(" ", "%20")
                url = f"{base_url}{book_encoded}%20{chapter}?translation=kjv"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # bible-api.com returns text as a single string with verse numbers
                    if 'text' in data:
                        text = data['text']
                        # The text usually comes with verse numbers embedded
                        # Try to parse it or use as is
                        book_text.append(f"{chapter}: {text}")
                    elif 'verses' in data:
                        # If structured verses are available
                        for verse in data['verses']:
                            verse_num = verse.get('verse', 0)
                            verse_text = verse.get('text', '')
                            book_text.append(f"{chapter}:{verse_num} {verse_text}")
                
                time.sleep(0.1)  # Be nice to the API
                
            except Exception as e:
                print(f"Error downloading {book_display} chapter {chapter}: {e}")
                continue
        
        if book_text:
            full_bible.append(f"{book_display.upper()}\n" + "\n".join(book_text))
            print(f"Downloaded {book_display}...")
        time.sleep(0.5)  # Rate limiting
    
    if full_bible:
        return "\n\n".join(full_bible)
    
    return None

def download_kjv_tamil():
    """Download King James Version Bible in Tamil (if available) or use translation."""
    print("Downloading KJV Bible (Tamil)...")
    
    # Tamil Bible sources are harder to find in public domain
    # We'll use a structured approach to get Tamil Bible text
    # Option 1: Use Tamil Bible API if available
    # Option 2: Use a text file source
    
    # For now, we'll create a placeholder that can be filled with actual Tamil Bible text
    # The user can provide Tamil Bible text file or we can try to fetch from available sources
    
    tamil_bible_url = "https://raw.githubusercontent.com/BibleNLP/ebible/master/corpus/tam-uthb.txt"
    
    try:
        response = requests.get(tamil_bible_url, timeout=30)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Error downloading Tamil Bible from primary source: {e}")
    
    # Fallback: Return placeholder text
    print("Warning: Tamil Bible not found in primary source. Please provide Tamil Bible text file.")
    return None

def save_bible_text(text, filepath):
    """Save Bible text to file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Saved Bible text to {filepath}")

def parse_bible_text(text):
    """Parse Bible text into structured format."""
    # This will parse the text into verses with book, chapter, verse format
    verses = []
    lines = text.split('\n')
    
    current_book = None
    current_chapter = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to detect book name (usually in caps or at start of line)
        # This is a simplified parser - may need adjustment based on source format
        if line.isupper() and len(line) > 3:
            current_book = line
            continue
        
        # Try to detect verse pattern (e.g., "1:1 In the beginning...")
        verse_match = re.match(r'^(\d+):(\d+)\s+(.+)$', line)
        if verse_match:
            chapter, verse, content = verse_match.groups()
            current_chapter = chapter
            verses.append({
                'book': current_book or 'UNKNOWN',
                'chapter': chapter,
                'verse': verse,
                'text': content
            })
        else:
            # Append to last verse if exists
            if verses:
                verses[-1]['text'] += ' ' + line
    
    return verses

if __name__ == "__main__":
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Download English Bible
    en_text = download_kjv_english()
    if en_text:
        save_bible_text(en_text, "data/bible_kjv_en.txt")
        print("English Bible downloaded successfully!")
    else:
        print("Failed to download English Bible")
    
    # Download Tamil Bible
    ta_text = download_kjv_tamil()
    if ta_text:
        save_bible_text(ta_text, "data/bible_kjv_ta.txt")
        print("Tamil Bible downloaded successfully!")
    else:
        print("Tamil Bible not available. Please provide Tamil Bible text file manually.")


from bible_parser import BibleParser
import os
import sys

def test_parser():
    parser = BibleParser(language="en")
    bible_file = "/Users/joeljoyston/Bible_RAG/data/bible_kjv_en.txt"
    print(f"Testing parser on {bible_file}...")
    
    verses = parser.parse_kjv_text(bible_file)
    print(f"Total verses found: {len(verses)}")
    
    # Search for Joel 1:1 specifically
    joel_1_1 = [v for v in verses if v['book'] == 'Joel' and v['chapter'] == 1 and v['verse'] == 1]
    if joel_1_1:
        print(f"SUCCESS: Found Joel 1:1 - {joel_1_1[0]['text']}")
    else:
        print("FAILURE: Joel 1:1 not found or mislabeled.")
        # Print some books that WERE found
        books = set(v['book'] for v in verses)
        print(f"Books found: {sorted(list(books))[:10]}... (Total books: {len(books)})")

if __name__ == "__main__":
    test_parser()

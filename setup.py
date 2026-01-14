"""
Setup script to download Bible data and create vector stores.
"""
import os
import sys
from pathlib import Path
import config
from data_downloader import download_kjv_english, download_kjv_tamil, save_bible_text
from bible_parser import BibleParser
from vector_store import BibleVectorStore

def setup_bible_data():
    """Download and process Bible data for all languages."""
    
    # Create data directory
    os.makedirs(config.DATA_PATH, exist_ok=True)
    
    # Download English Bible
    print("=" * 50)
    print("Setting up English Bible...")
    print("=" * 50)
    
    if not os.path.exists(config.BIBLE_DATA_EN):
        print("Downloading English KJV Bible...")
        en_text = download_kjv_english()
        if en_text and len(en_text) > 1000:
            save_bible_text(en_text, config.BIBLE_DATA_EN)
            print("English Bible downloaded successfully!")
        else:
            print("Warning: English Bible download may have failed or returned incomplete data.")
            print("Please check the data file or provide Bible text manually.")
    else:
        print("English Bible file already exists.")
    
    # Download Tamil Bible
    print("\n" + "=" * 50)
    print("Setting up Tamil Bible...")
    print("=" * 50)
    
    if not os.path.exists(config.BIBLE_DATA_TA):
        print("Downloading Tamil Bible...")
        ta_text = download_kjv_tamil()
        if ta_text and len(ta_text) > 1000:
            save_bible_text(ta_text, config.BIBLE_DATA_TA)
            print("Tamil Bible downloaded successfully!")
        else:
            print("⚠️  Warning: Tamil Bible not available from automatic download.")
            print("You can:")
            print("  1. Manually download Tamil Bible text from a public domain source")
            print(f"  2. Save it as: {config.BIBLE_DATA_TA}")
            print("  3. Run this setup script again")
            print("\nThe system will work with English only until Tamil Bible is added.")
            response = input("\nContinue with English only? (y/n): ")
            if response.lower() != 'y':
                print("Setup cancelled. Please add Tamil Bible text and run again.")
                sys.exit(0)
    else:
        print("Tamil Bible file already exists.")

def create_vector_stores():
    """Create vector stores for all languages."""
    
    # Check which languages are available
    languages = []
    if os.path.exists(config.BIBLE_DATA_EN):
        languages.append("en")
    if os.path.exists(config.BIBLE_DATA_TA):
        languages.append("ta")
    
    if not languages:
        print("Error: No Bible text files found!")
        print("Please run the data download step first.")
        return
    
    print(f"\nCreating vector stores for {len(languages)} language(s)...")
    
    for lang in languages:
        print("\n" + "=" * 50)
        print(f"Creating vector store for {config.SUPPORTED_LANGUAGES[lang]}...")
        print("=" * 50)
        
        bible_file = config.BIBLE_DATA_EN if lang == "en" else config.BIBLE_DATA_TA
        
        if not os.path.exists(bible_file):
            print(f"Bible file not found: {bible_file}")
            print("Skipping vector store creation for this language.")
            continue
        
        # Parse Bible text
        parser = BibleParser(language=lang)
        print("Parsing Bible text...")
        verses = parser.parse_kjv_text(bible_file)
        print(f"Parsed {len(verses)} verses")
        
        # Create chunks
        print("Creating chunks...")
        chunks = parser.create_chunks(
            verses,
            chunk_size=config.CHUNK_SIZE,
            overlap=config.CHUNK_OVERLAP
        )
        print(f"Created {len(chunks)} chunks")
        
        # Create vector store
        vector_store = BibleVectorStore(language=lang)
        vector_store.create_index(chunks)
        print(f"Vector store created for {config.SUPPORTED_LANGUAGES[lang]}!")
    
    print("\n" + "=" * 50)
    print("Setup completed!")
    print("=" * 50)

if __name__ == "__main__":
    print("Bible RAG Setup")
    print("=" * 50)
    
    # Check for Google API key
    if not config.GOOGLE_API_KEY:
        print("Warning: GOOGLE_API_KEY not found in environment.")
        print("The system will work but with limited response generation.")
        print("Please set GOOGLE_API_KEY in .env file for full functionality.")
        print("Get your FREE API key from: https://aistudio.google.com/")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Setup Bible data
    setup_bible_data()
    
    # Create vector stores
    create_vector_stores()
    
    print("\nSetup complete! You can now run the Streamlit app with:")
    print("streamlit run app.py")


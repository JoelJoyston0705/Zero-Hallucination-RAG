# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API key (optional, but recommended for better responses)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

**Note:** The system will work without an OpenAI API key, but responses will be limited to showing retrieved passages only.

### 3. Download Bible Data and Create Vector Stores

Run the setup script:

```bash
python setup.py
```

This will:
- Download KJV Bible text (English)
- Attempt to download Tamil Bible (if available)
- Parse the Bible text into structured verses
- Create embeddings using sentence transformers
- Build FAISS vector stores for fast retrieval
- Save everything for future use

**Time:** This process may take 10-30 minutes depending on your internet connection and computer speed.

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Tamil Bible Setup

If the automatic Tamil Bible download fails, you can manually add Tamil Bible text:

1. Download Tamil Bible text from a public domain source
2. Save it as `data/bible_kjv_ta.txt`
3. Run `python setup.py` again to create the Tamil vector store

## Testing

Test the RAG system:

```bash
python test_rag.py --language en
```

## Troubleshooting

### Issue: "Vector store not found"

**Solution:** Run `python setup.py` to create the vector stores.

### Issue: "Error downloading Bible"

**Solution:** 
- Check your internet connection
- The script will try multiple sources automatically
- You can manually download Bible text and place it in the `data/` directory

### Issue: "OpenAI API key not found"

**Solution:**
- The system works without an API key, but with limited functionality
- For full functionality, add your API key to `.env` file
- Get an API key from https://platform.openai.com/

### Issue: "Out of memory" during setup

**Solution:**
- Reduce `CHUNK_SIZE` in `config.py`
- Process one language at a time
- Use a machine with more RAM

## Usage Tips

1. **Ask specific questions:** "What does the Bible say about love?" works better than "Tell me about the Bible"

2. **Use natural language:** The system understands questions in natural language

3. **Check sources:** Every answer includes Bible references - verify them!

4. **Language switching:** Use the sidebar to switch between English and Tamil

5. **Clear history:** Use the "Clear History" button to start fresh

## Zero Hallucination Guarantee

The system is designed to:
- Only use retrieved Bible passages
- Not add information not in the passages
- Cite sources for every answer
- Say "I cannot find" instead of guessing

If you notice any hallucinations, please report them!

## Next Steps

- Add more languages by following the language addition guide in README.md
- Customize the UI in `app.py`
- Adjust retrieval parameters in `config.py`
- Add more Bible versions (requires modifying the data downloader)

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review the code comments
3. Check if vector stores are properly created
4. Verify Bible text files are in the `data/` directory




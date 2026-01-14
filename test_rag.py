"""
Test script for Bible RAG system.
"""
import sys
import config
from rag_system import BibleRAG

def test_rag_system(language="en"):
    """Test the RAG system with sample questions."""
    print(f"Testing Bible RAG system ({language})...")
    print("=" * 50)
    
    try:
        # Initialize RAG system
        rag = BibleRAG(language=language)
        print("✓ RAG system initialized successfully")
        
        # Test questions
        if language == "en":
            test_questions = [
                "What does the Bible say about love?",
                "Tell me about Jesus' birth",
                "What is the first commandment?",
            ]
        else:
            test_questions = [
                "வேதாகமம் அன்பைப் பற்றி என்ன சொல்கிறது?",
                "இயேசுவின் பிறப்பைப் பற்றி சொல்லுங்கள்",
            ]
        
        # Test each question
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*50}")
            print(f"Test {i}: {question}")
            print("="*50)
            
            try:
                result = rag.query(question)
                print(f"\nAnswer:")
                print(result["answer"])
                print(f"\nSources: {', '.join(result['sources'][:5])}")
                print(f"Number of retrieved chunks: {len(result.get('retrieved_chunks', []))}")
            except Exception as e:
                print(f"Error: {e}")
        
        print("\n" + "="*50)
        print("Testing completed!")
        print("="*50)
        
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        print("Make sure you have run setup.py first to create vector stores.")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Bible RAG system")
    parser.add_argument("--language", "-l", default="en", choices=["en", "ta"],
                       help="Language to test (default: en)")
    args = parser.parse_args()
    
    test_rag_system(args.language)




"""
Verification script to check if the Bible RAG system is properly set up.
"""
import os
import sys
import config

def check_setup():
    """Check if the system is properly set up."""
    print("=" * 60)
    print("Bible RAG Setup Verification")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # Check Python version
    print("\n1. Checking Python version...")
    if sys.version_info < (3, 8):
        issues.append("Python 3.8 or higher is required")
        print("   ❌ Python version too old")
    else:
        print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check dependencies
    print("\n2. Checking dependencies...")
    required_packages = [
        'streamlit', 'openai', 'langchain', 'faiss', 
        'sentence_transformers', 'requests', 'numpy'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✓ {package}")
        except ImportError:
            issues.append(f"Missing package: {package}")
            print(f"   ❌ {package} not installed")
    
    # Check environment variables
    print("\n3. Checking environment variables...")
    if config.OPENAI_API_KEY:
        print("   ✓ OPENAI_API_KEY is set")
    else:
        warnings.append("OPENAI_API_KEY not set (optional but recommended)")
        print("   ⚠️  OPENAI_API_KEY not set (optional)")
    
    # Check data files
    print("\n4. Checking data files...")
    if os.path.exists(config.BIBLE_DATA_EN):
        size = os.path.getsize(config.BIBLE_DATA_EN)
        print(f"   ✓ English Bible found ({size:,} bytes)")
    else:
        issues.append("English Bible file not found")
        print("   ❌ English Bible file not found")
    
    if os.path.exists(config.BIBLE_DATA_TA):
        size = os.path.getsize(config.BIBLE_DATA_TA)
        print(f"   ✓ Tamil Bible found ({size:,} bytes)")
    else:
        warnings.append("Tamil Bible file not found (optional)")
        print("   ⚠️  Tamil Bible file not found (optional)")
    
    # Check vector stores
    print("\n5. Checking vector stores...")
    os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)
    
    en_index = os.path.join(config.VECTOR_STORE_PATH, f"{config.FAISS_INDEX_EN}.index")
    if os.path.exists(en_index):
        size = os.path.getsize(en_index)
        print(f"   ✓ English vector store found ({size:,} bytes)")
    else:
        issues.append("English vector store not found. Run setup.py to create it.")
        print("   ❌ English vector store not found")
    
    ta_index = os.path.join(config.VECTOR_STORE_PATH, f"{config.FAISS_INDEX_TA}.index")
    if os.path.exists(ta_index):
        size = os.path.getsize(ta_index)
        print(f"   ✓ Tamil vector store found ({size:,} bytes)")
    else:
        warnings.append("Tamil vector store not found (optional)")
        print("   ⚠️  Tamil vector store not found (optional)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nPlease fix these issues before running the application.")
        return False
    else:
        print("\n✓ No critical issues found!")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        print("\nThe system will work, but some features may be limited.")
    
    print("\n" + "=" * 60)
    print("Setup verification complete!")
    print("=" * 60)
    
    if not issues:
        print("\nYou can now run the application with:")
        print("   streamlit run app.py")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)




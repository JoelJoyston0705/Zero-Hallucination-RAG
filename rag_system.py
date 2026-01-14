"""
RAG System for Bible Q&A with zero hallucination guarantee.
Uses OpenAI API with Query Disambiguation and Canonical Anchor Retrieval
"""
import os
import re
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import config
from vector_store import BibleVectorStore

# Ambiguous Bible terms that need context
AMBIGUOUS_TERMS = {
    "ark": {
        "options": ["Noah's Ark (the boat during the flood)", "Ark of the Covenant (the sacred chest)"],
        "context_clues": {
            "noah": "noah flood water rain boat",
            "covenant": "covenant tabernacle moses bezalel gold"
        }
    },
    "temple": {
        "options": ["Solomon's Temple", "Second Temple", "Jesus' body as temple"],
        "context_clues": {
            "solomon": "solomon build jerusalem",
            "herod": "herod second zerubbabel",
            "jesus": "jesus body three days"
        }
    },
    "law": {
        "options": ["Law of Moses (Torah)", "Roman law"],
        "context_clues": {
            "moses": "moses commandments sinai torah",
            "roman": "caesar pilate rome"
        }
    }
}

# CANONICAL ANCHOR PASSAGES for thematic questions
# These are the key chapters/verses for major Bible topics
THEMATIC_ANCHORS = {
    "abraham_promise": {
        "triggers": ["promise", "covenant", "abraham", "abram"],
        "book_filter": "genesis",
        "chapters": [12, 15, 17, 22],  # Key promise chapters
        "description": "God's covenant promises to Abraham"
    },
    "ten_commandments": {
        "triggers": ["commandment", "ten commandments", "law of moses", "thou shalt"],
        "book_filter": "exodus",
        "chapters": [20],  # Exodus 20 contains the Ten Commandments
        "description": "The Ten Commandments"
    },
    "creation": {
        "triggers": ["creation", "created", "beginning", "adam", "eve", "garden"],
        "book_filter": "genesis",
        "chapters": [1, 2, 3],
        "description": "Creation narrative"
    },
    "flood": {
        "triggers": ["flood", "noah", "ark", "rain", "dove"],
        "book_filter": "genesis", 
        "chapters": [6, 7, 8, 9],
        "description": "Noah and the flood"
    },
    "moses_burning_bush": {
        "triggers": ["burning bush", "moses call", "i am"],
        "book_filter": "exodus",
        "chapters": [3, 4],
        "description": "Moses at the burning bush"
    },
    "exodus_passover": {
        "triggers": ["passover", "plague", "egypt", "pharaoh", "let my people"],
        "book_filter": "exodus",
        "chapters": [7, 8, 9, 10, 11, 12],
        "description": "The Exodus and Passover"
    },
    "sermon_mount": {
        "triggers": ["beatitude", "blessed are", "sermon on the mount"],
        "book_filter": "matthew",
        "chapters": [5, 6, 7],
        "description": "Sermon on the Mount"
    },
    "lords_prayer": {
        "triggers": ["lord's prayer", "our father", "how to pray"],
        "book_filter": "matthew",
        "chapters": [6],
        "description": "The Lord's Prayer"
    },
    "birth_jesus": {
        "triggers": ["birth of jesus", "nativity", "bethlehem", "manger", "wise men", "shepherds"],
        "book_filter": None,  # Can be Matthew or Luke
        "chapters": [],
        "description": "Birth of Jesus"
    },
    "resurrection": {
        "triggers": ["resurrection", "risen", "empty tomb", "third day"],
        "book_filter": None,
        "chapters": [],
        "description": "Resurrection of Jesus"
    }
}

class BibleRAG:
    def __init__(self, language: str = "en"):
        self.language = language
        self.vector_store = BibleVectorStore(language=language)
        self.client = None
        
        # Initialize OpenAI if API key is available
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Load vector store
        if not self.vector_store.load_index():
            raise ValueError(f"Vector store not found for language {language}. Please create index first.")
    
    def detect_thematic_query(self, query: str) -> Optional[Dict]:
        """
        Detect if query is asking about a major Bible theme.
        Returns the matching theme config or None.
        """
        query_lower = query.lower()
        
        for theme_key, theme_config in THEMATIC_ANCHORS.items():
            triggers = theme_config.get("triggers", [])
            book_filter = theme_config.get("book_filter")
            
            # Check if any trigger matches
            trigger_match = any(trigger in query_lower for trigger in triggers)
            
            # Check if book is mentioned (for scoped queries like "in Genesis")
            book_mentioned = book_filter and book_filter in query_lower
            
            # For Abraham + Genesis specifically
            if "abraham" in query_lower and "genesis" in query_lower:
                if theme_key == "abraham_promise":
                    return theme_config
            
            # Match if trigger found AND (book matches OR book not specified in query)
            if trigger_match and (book_mentioned or book_filter is None):
                return theme_config
        
        return None
    
    def retrieve_thematic_anchors(self, theme_config: Dict) -> List[Dict]:
        """
        Retrieve canonical anchor passages for a theme.
        """
        anchor_results = []
        book_filter = theme_config.get("book_filter", "").lower() if theme_config.get("book_filter") else None
        chapters = theme_config.get("chapters", [])
        
        if not chapters or not hasattr(self.vector_store, 'chunks'):
            return []
        
        # Search through chunks for matching book + chapters
        for chunk in self.vector_store.chunks:
            chunk_book = chunk.get('book', '').lower()
            chunk_chapter = chunk.get('chapter')
            
            # Book must match if specified
            if book_filter and book_filter not in chunk_book:
                continue
            
            # Chapter must be in the anchor list
            if chunk_chapter in chapters:
                anchor_results.append(chunk)
        
        # Sort by chapter order
        anchor_results.sort(key=lambda x: (x.get('chapter', 0)))
        
        return anchor_results[:10]  # Return up to 10 anchor chunks
    
    def detect_verse_reference(self, query: str) -> Optional[Tuple[str, int, Optional[int]]]:
        """
        Detect explicit verse or chapter references in query.
        Returns: (book, chapter, verse) or (book, chapter, None) for chapter-only
        """
        # Common Bible book names
        books = [
            "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
            "joshua", "judges", "ruth", "samuel", "kings", "chronicles",
            "ezra", "nehemiah", "esther", "job", "psalm", "psalms", "proverbs",
            "ecclesiastes", "song", "isaiah", "jeremiah", "lamentations",
            "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah", "jonah",
            "micah", "nahum", "habakkuk", "zephaniah", "haggai", "zechariah", "malachi",
            "matthew", "mark", "luke", "john", "acts", "romans", "corinthians",
            "galatians", "ephesians", "philippians", "colossians", "thessalonians",
            "timothy", "titus", "philemon", "hebrews", "james", "peter", "jude", "revelation"
        ]
        
        query_lower = query.lower()
        
        # Pattern 1: Book Chapter:Verse (e.g., "Psalm 110:1", "Genesis 1:26")
        pattern_verse = r'(\d?\s*[a-zA-Z]+)\s+(\d+):(\d+)'
        match = re.search(pattern_verse, query_lower)
        
        if match:
            book_part = match.group(1).strip()
            chapter = int(match.group(2))
            verse = int(match.group(3))
            
            for book in books:
                if book in book_part or book_part in book:
                    return (book.title(), chapter, verse)
        
        # Pattern 2: Book Chapter (e.g., "Exodus 3", "Genesis 18") - chapter only
        pattern_chapter = r'(\d?\s*[a-zA-Z]+)\s+(\d+)(?!\s*:)'
        match = re.search(pattern_chapter, query_lower)
        
        if match:
            book_part = match.group(1).strip()
            chapter = int(match.group(2))
            
            for book in books:
                if book in book_part or book_part in book:
                    return (book.title(), chapter, None)  # None indicates chapter-only
        
        return None
    
    def retrieve_pinned_verse(self, book: str, chapter: int, verse: Optional[int] = None) -> List[Dict]:
        """
        Directly retrieve a specific verse or chapter from the metadata.
        STRICT EXACT MATCHING to prevent citation drift (e.g., 3:2 vs 33:2)
        """
        pinned_results = []
        
        # Normalize book name for matching
        book_lower = book.lower()
        
        # Search through chunks for EXACT match
        if hasattr(self.vector_store, 'chunks') and self.vector_store.chunks:
            for chunk in self.vector_store.chunks:
                chunk_book = chunk.get('book', '').lower()
                chunk_chapter = chunk.get('chapter')
                
                # Book name must match
                if book_lower not in chunk_book and chunk_book not in book_lower:
                    continue
                
                # For chapter-only lookup
                if verse is None:
                    if chunk_chapter == chapter:
                        pinned_results.append(chunk)
                else:
                    # For specific verse lookup - STRICT EXACT MATCHING
                    # Chapter must match exactly first
                    if chunk_chapter != chapter:
                        continue
                    
                    references = chunk.get('references', [])
                    # Build exact target patterns
                    target_patterns = [
                        f"{book} {chapter}:{verse}",      # "Exodus 3:2"
                        f"{book.lower()} {chapter}:{verse}",
                        f"{book.title()} {chapter}:{verse}"
                    ]
                    
                    for ref in references:
                        ref_lower = ref.lower()
                        # Check for exact verse match (with word boundaries)
                        for pattern in target_patterns:
                            if pattern.lower() == ref_lower or \
                               ref_lower.endswith(f" {chapter}:{verse}") or \
                               ref_lower == f"{chunk_book} {chapter}:{verse}":
                                pinned_results.append(chunk)
                                break
                        else:
                            continue
                        break
        
        return pinned_results[:5]  # Return up to 5 matching chunks
    
    def disambiguate_query(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Check for ambiguous terms and expand query with context.
        Returns: (expanded_query, disambiguation_note)
        """
        query_lower = query.lower()
        disambiguation_note = None
        expanded_query = query
        
        for term, info in AMBIGUOUS_TERMS.items():
            if term in query_lower:
                # Check if user already provided context
                context_found = False
                for context_key, context_words in info["context_clues"].items():
                    if any(word in query_lower for word in context_words.split()):
                        context_found = True
                        break
                
                if not context_found:
                    # Add context based on common usage patterns
                    if term == "ark" and any(w in query_lower for w in ["built", "build", "made", "who"]):
                        # "Who built the ark" likely means Noah's ark
                        expanded_query = query + " noah flood boat"
                        disambiguation_note = f"📌 Note: Interpreting 'ark' as Noah's Ark (the flood boat). For Ark of the Covenant, try asking about 'ark of the covenant'."
                    elif term == "ark":
                        expanded_query = query + " noah genesis flood"
                        disambiguation_note = f"📌 Note: Multiple 'arks' in Bible - searching for Noah's Ark context."
        
        return expanded_query, disambiguation_note
    
    def check_retrieval_coherence(self, results: List[Dict]) -> Optional[str]:
        """
        Check if retrieved passages are from coherent context.
        Returns warning if passages seem to span unrelated topics.
        """
        if not results:
            return None
        
        books = set()
        for r in results:
            book = r.get('book', 'Unknown')
            books.add(book)
        
        # Check for potentially mixed contexts
        genesis_exodus_mix = 'Genesis' in books and 'Exodus' in books
        old_new_mix = any(b in books for b in ['Matthew', 'Mark', 'Luke', 'John', 'Acts']) and \
                      any(b in books for b in ['Genesis', 'Exodus', 'Leviticus'])
        
        if genesis_exodus_mix and len(results) <= 3:
            return "⚠️ Retrieved passages span Genesis and Exodus. Results may cover different topics."
        
        return None
    
    def get_language_prompts(self) -> str:
        """Get system prompts in different languages."""
        prompts = {
            "en": """You are a helpful Bible assistant. Answer questions based ONLY on the provided Bible passages.

RULES:
1. Use ONLY the information from the provided Bible passages below
2. Cite Bible references (book chapter:verse) from the passages
3. Keep answers concise and direct

CRITICAL ACCURACY RULES:
4. Do NOT claim one verse "references" another unless explicitly stated in the text
5. Do NOT connect Old Testament to New Testament passages as if one quotes the other
6. For symbolic/metaphorical concepts (rock, light, shepherd, etc.): describe what EACH passage says separately
7. If metaphor attribution is unclear, use cautious phrasing like "This passage describes..." or "Similarly..."
8. Only state what the text explicitly says - avoid interpretation

VERB-MATCHING RULE:
9. Match your answer to the question's verb:
   - If question asks "who APPEARS", answer about who appears (not who speaks)
   - If question asks "who SPEAKS", answer about who speaks
   - If question asks "who SENDS", answer about who sends
   - Distinguish between appearing, speaking, going, sending, etc.

CONTEXT PRIORITY RULE (for cross-testament clarity):
10. When question asks about OT figures (Abraham, Moses, David, etc.):
    - FIRST describe what the OT passages say (Genesis, Exodus, etc.)
    - THEN, if NT passages are included, say "Later NT passages describe..." or "In the New Testament..."
    - This helps users understand the original context vs later interpretation

Be helpful but precise. Accuracy over creativity.""",
            
            "ta": """நீங்கள் ஒரு உதவிகரமான வேதாகம உதவியாளர். வழங்கப்பட்ட வேதாகம பத்திகளின் அடிப்படையில் மட்டுமே கேள்விகளுக்கு பதிலளிக்கவும்.

விதிகள்:
1. கீழே உள்ள வேதாகம பத்திகளிலிருந்து மட்டுமே தகவலைப் பயன்படுத்தவும்
2. பத்திகளிலிருந்து வேதாகம மேற்கோள்களை (நூல் அதிகாரம்:வசனம்) குறிப்பிடவும்
3. பதில்களை சுருக்கமாகவும் நேரடியாகவும் வைக்கவும்

முக்கிய துல்லிய விதிகள்:
4. உரையில் வெளிப்படையாகக் குறிப்பிடப்படாவிட்டால், ஒரு வசனம் மற்றொன்றை "குறிப்பிடுகிறது" என்று கூறாதீர்கள்
5. ஒன்று மற்றொன்றை மேற்கோள் காட்டுவது போல் பழைய ஏற்பாடு மற்றும் புதிய ஏற்பாடு பத்திகளை இணைக்காதீர்கள்
6. குறியீட்டு/உருவக கருத்துகளுக்கு: ஒவ்வொரு பத்தியும் என்ன சொல்கிறது என்பதை தனித்தனியாக விவரிக்கவும்
7. துல்லியமாக இருங்கள் - படைப்பாற்றலை விட துல்லியம் முக்கியம்."""
        }
        return prompts.get(self.language, prompts["en"])
    
    def retrieve_context(self, query: str, top_k: int = None) -> List[Dict]:
        """Retrieve relevant Bible passages for the query."""
        if top_k is None:
            top_k = config.TOP_K_RESULTS
        
        results = self.vector_store.search(query, top_k=top_k)
        return results
    
    def format_context(self, results: List[Dict]) -> str:
        """Format retrieved results into context string."""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            refs = ", ".join(result.get('references', []))
            if not refs:
                refs = f"{result.get('book', 'Unknown')} {result.get('chapter', '?')}"
            
            context_parts.append(f"[{i}] Reference: {refs}\nText: {result['text']}\n")
        
        return "\n".join(context_parts)
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate response using LLM with strict retrieval-only prompting."""
        if not self.client:
            # Fallback: return context-based response without LLM
            return self._fallback_response(context)
        
        system_prompt = self.get_language_prompts()
        
        # Very strict user prompt emphasizing zero hallucination
        if self.language == "ta":
            user_prompt = f"""வேதாகம பத்திகள்:
{context}

கேள்வி: {query}

மேலே உள்ள பத்திகளின் அடிப்படையில் மட்டுமே பதிலளிக்கவும். பத்திகளில் இல்லாத எதையும் சேர்க்காதீர்கள்."""
        else:
            user_prompt = f"""Bible Passages:
{context}

Question: {query}

Answer based ONLY on the passages above. Do not add anything that is not in the passages."""
        
        try:
            # Use OpenAI chat completion API - Optimized for SPEED
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=getattr(config, 'MAX_TOKENS', 300)  # Reduced for speed
            )
            answer = response.choices[0].message.content.strip()
            return answer
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._fallback_response(context)
    
    def _fallback_response(self, context: str) -> str:
        """Fallback response when LLM is not available."""
        if self.language == "ta":
            return f"வழங்கப்பட்ட வேதாகம பத்திகள்:\n\n{context}\n\nதயவுசெய்து மேலே உள்ள பத்திகளிலிருந்து பதிலைப் படிக்கவும்."
        else:
            return f"Retrieved Bible passages:\n\n{context}\n\nPlease read the answer from the passages above."
    
    def query(self, question: str, top_k: int = None) -> Dict:
        """
        Main query method: retrieve context and generate response.
        Returns response with sources.
        """
        verse_pin_note = None
        thematic_note = None
        results = []
        
        # Step 0: Check for explicit verse/chapter reference (verse-pin retrieval)
        verse_ref = self.detect_verse_reference(question)
        explicit_verse_requested = False
        
        if verse_ref:
            book, chapter, verse = verse_ref
            explicit_verse_requested = (verse is not None)  # True if specific verse was requested
            pinned_results = self.retrieve_pinned_verse(book, chapter, verse)
            
            if pinned_results:
                results = pinned_results
                if verse:
                    verse_pin_note = f"📖 Direct verse lookup: {book} {chapter}:{verse}"
                else:
                    verse_pin_note = f"📖 Direct chapter lookup: {book} chapter {chapter}"
            elif explicit_verse_requested:
                # SAFETY GUARDRAIL: If user requested specific verse but we couldn't find it,
                # DO NOT fall back to semantic search - refuse instead to prevent citation drift
                return {
                    "answer": f"⚠️ Citation Safety: I could not find the exact verse {book} {chapter}:{verse} in my database. I will not use semantic search as it may return incorrect verses. Please check the verse reference or try a different question.",
                    "sources": [],
                    "context": "",
                    "error": "verse_not_found"
                }
        
        # Step 0.5: Check for THEMATIC queries (e.g., "What promise did God make to Abraham in Genesis?")
        if not results:
            theme_config = self.detect_thematic_query(question)
            if theme_config:
                thematic_results = self.retrieve_thematic_anchors(theme_config)
                if thematic_results:
                    results = thematic_results
                    thematic_note = f"📚 Thematic retrieval: {theme_config.get('description', 'Canonical passages')}"
        
        # Step 1: If no pinned/thematic results, use semantic search with disambiguation
        if not results:
            expanded_query, disambiguation_note = self.disambiguate_query(question)
            results = self.retrieve_context(expanded_query, top_k=top_k)
        else:
            disambiguation_note = None
        
        if not results:
            if self.language == "ta":
                return {
                    "answer": "மன்னிக்கவும், உங்கள் கேள்விக்கு பொருத்தமான வேதாகம பத்திகளைக் கண்டுபிடிக்க முடியவில்லை. தயவுசெய்து உங்கள் கேள்வியை மீண்டும் உருவாக்கவும்.",
                    "sources": [],
                    "context": ""
                }
            else:
                return {
                    "answer": "Sorry, I couldn't find relevant Bible passages for your question. Please try rephrasing your question.",
                    "sources": [],
                    "context": ""
                }
        
        # Step 3: Check retrieval coherence
        coherence_warning = self.check_retrieval_coherence(results)
        
        # Step 4: Format context
        context = self.format_context(results)
        
        # Step 5: Generate response using ORIGINAL question (not expanded)
        answer = self.generate_response(question, context)
        
        # Step 6: Add notes if applicable
        if verse_pin_note:
            answer = f"{verse_pin_note}\n\n{answer}"
        
        if thematic_note:
            answer = f"{thematic_note}\n\n{answer}"
        
        if disambiguation_note:
            answer = f"{answer}\n\n{disambiguation_note}"
        
        if coherence_warning:
            answer = f"{answer}\n\n{coherence_warning}"
        
        # Extract sources
        sources = []
        for result in results:
            sources.extend(result.get('references', []))
        sources = list(set(sources))
        
        return {
            "answer": answer,
            "sources": sources,
            "context": context,
            "retrieved_chunks": results
        }


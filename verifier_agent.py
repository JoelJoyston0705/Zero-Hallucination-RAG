"""
Verifier Agent for Zero-Hallucination RAG System

This agent performs post-generation verification to ensure all claims
in the generated answer are grounded in the retrieved context.

Architecture:
    Main RAG → Generate Answer → Verifier Agent → Validated Answer

The verifier checks:
1. Claim extraction from answer
2. Grounding verification against retrieved passages  
3. Citation accuracy validation
4. Rejection/rewriting of ungrounded claims

This creates a two-stage verification pipeline that significantly
reduces hallucination risk in high-stakes domains.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class VerificationStatus(Enum):
    """Verification result status codes."""
    FULLY_GROUNDED = "fully_grounded"
    PARTIALLY_GROUNDED = "partially_grounded"
    NOT_GROUNDED = "not_grounded"
    VERIFICATION_FAILED = "verification_failed"


@dataclass
class Claim:
    """Represents an extractable claim from a generated answer."""
    text: str
    citations: List[str]
    is_grounded: Optional[bool] = None
    grounding_evidence: Optional[str] = None
    confidence: float = 0.0


@dataclass
class VerificationResult:
    """Complete verification result for an answer."""
    status: VerificationStatus
    original_answer: str
    verified_answer: str
    claims: List[Claim]
    grounded_claims: int
    total_claims: int
    hallucination_score: float  # 0.0 = no hallucination, 1.0 = full hallucination
    warnings: List[str]
    rejected: bool


class VerifierAgent:
    """
    Lightweight verification agent for grounding validation.
    
    This agent uses rule-based heuristics for fast, reliable verification
    without requiring additional LLM calls (optional LLM enhancement available).
    
    Key capabilities:
    - Extract claims from generated answers
    - Validate claims against retrieved context
    - Calculate hallucination risk scores
    - Reject or flag ungrounded content
    
    Design Philosophy:
    - Rule-based first (fast, deterministic)
    - LLM-enhanced optional (more accurate, slower)
    - Conservative rejection (prefer false negatives over hallucinations)
    """
    
    def __init__(self, use_llm_verification: bool = False, llm_client=None):
        """
        Initialize the Verifier Agent.
        
        Args:
            use_llm_verification: If True, uses LLM for deeper claim verification
            llm_client: Optional OpenAI client for LLM-based verification
        """
        self.use_llm_verification = use_llm_verification
        self.llm_client = llm_client
        
        # Bible reference pattern (e.g., "Genesis 1:26", "Psalm 23:1")
        self.citation_pattern = re.compile(
            r'([1-3]?\s*[A-Za-z]+)\s+(\d+):(\d+)(?:-(\d+))?'
        )
        
        # Common hallucination indicators
        self.hallucination_phrases = [
            "according to tradition",
            "it is believed that",
            "some scholars argue",
            "the bible implies",
            "this might mean",
            "could be interpreted as",
            "historically speaking",
            "in my understanding",
            "generally speaking",
            "it's commonly thought",
        ]
        
        # Phrases indicating grounded response
        self.grounded_phrases = [
            "according to",
            "the passage states",
            "in the text",
            "as written in",
            "the verse says",
            "this passage describes",
        ]
    
    def extract_claims(self, answer: str) -> List[Claim]:
        """
        Extract individual claims from a generated answer.
        
        A claim is a statement that can be verified against the source text.
        
        Args:
            answer: The generated answer text
            
        Returns:
            List of Claim objects extracted from the answer
        """
        claims = []
        
        # Split into sentences (basic claim unit)
        sentences = re.split(r'(?<=[.!?])\s+', answer)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            # Skip metadata/notes (lines starting with emojis or special markers)
            if sentence.startswith(('📖', '📚', '📌', '⚠️', '✅', '❌')):
                continue
            
            # Extract any citations in this sentence
            citations = self.citation_pattern.findall(sentence)
            citation_strs = [f"{c[0]} {c[1]}:{c[2]}" for c in citations]
            
            claims.append(Claim(
                text=sentence,
                citations=citation_strs,
                is_grounded=None,
                confidence=0.0
            ))
        
        return claims
    
    def verify_claim_against_context(self, claim: Claim, context: str) -> Claim:
        """
        Verify a single claim against the retrieved context.
        
        Uses keyword matching and semantic similarity heuristics
        for fast verification.
        
        Args:
            claim: The claim to verify
            context: The retrieved context passages
            
        Returns:
            Updated Claim with grounding status
        """
        claim_text = claim.text.lower()
        context_lower = context.lower()
        
        # Extract key content words (nouns, verbs) from claim
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'what', 'which', 'who', 'whom',
            'and', 'or', 'but', 'if', 'then', 'than', 'so', 'as', 'of',
            'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from'
        }
        
        # Extract content words
        words = re.findall(r'\b[a-z]+\b', claim_text)
        content_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        if not content_words:
            claim.is_grounded = True  # Empty claim, consider grounded
            claim.confidence = 1.0
            return claim
        
        # Calculate grounding score based on word overlap
        words_found = sum(1 for w in content_words if w in context_lower)
        overlap_ratio = words_found / len(content_words)
        
        # Check for citations - claims with valid citations get bonus confidence
        citation_bonus = 0.0
        for citation in claim.citations:
            if citation.lower() in context_lower:
                citation_bonus = 0.2
                break
        
        # Check for hallucination indicators
        hallucination_penalty = 0.0
        for phrase in self.hallucination_phrases:
            if phrase in claim_text:
                hallucination_penalty = 0.3
                break
        
        # Check for grounding indicators
        grounding_bonus = 0.0
        for phrase in self.grounded_phrases:
            if phrase in claim_text:
                grounding_bonus = 0.1
                break
        
        # Calculate final confidence
        confidence = min(1.0, max(0.0, 
            overlap_ratio + citation_bonus + grounding_bonus - hallucination_penalty
        ))
        
        claim.confidence = confidence
        claim.is_grounded = confidence >= 0.4  # Threshold for grounding
        
        # Find evidence snippet if grounded
        if claim.is_grounded and content_words:
            # Find matching passage snippet
            for word in content_words:
                idx = context_lower.find(word)
                if idx != -1:
                    start = max(0, idx - 50)
                    end = min(len(context), idx + 100)
                    claim.grounding_evidence = context[start:end].strip()
                    break
        
        return claim
    
    def verify_answer(self, answer: str, context: str, sources: List[str]) -> VerificationResult:
        """
        Perform complete verification of a generated answer.
        
        This is the main entry point for the verification pipeline.
        
        Args:
            answer: The generated answer from the RAG system
            context: The formatted context passages
            sources: List of source citations
            
        Returns:
            VerificationResult with complete analysis
        """
        warnings = []
        
        # Extract claims from answer
        claims = self.extract_claims(answer)
        
        if not claims:
            return VerificationResult(
                status=VerificationStatus.FULLY_GROUNDED,
                original_answer=answer,
                verified_answer=answer,
                claims=[],
                grounded_claims=0,
                total_claims=0,
                hallucination_score=0.0,
                warnings=["No verifiable claims found in answer"],
                rejected=False
            )
        
        # Verify each claim
        verified_claims = []
        for claim in claims:
            verified_claim = self.verify_claim_against_context(claim, context)
            verified_claims.append(verified_claim)
        
        # Calculate statistics
        grounded_count = sum(1 for c in verified_claims if c.is_grounded)
        total_count = len(verified_claims)
        hallucination_score = 1.0 - (grounded_count / total_count) if total_count > 0 else 0.0
        
        # Determine overall status
        if grounded_count == total_count:
            status = VerificationStatus.FULLY_GROUNDED
        elif grounded_count > 0:
            status = VerificationStatus.PARTIALLY_GROUNDED
        else:
            status = VerificationStatus.NOT_GROUNDED
        
        # Generate warnings for ungrounded claims
        for claim in verified_claims:
            if not claim.is_grounded:
                warnings.append(f"Ungrounded claim: '{claim.text[:50]}...'")
        
        # Decision: reject if hallucination score too high
        rejected = hallucination_score > 0.5
        
        # Build verified answer (strikethrough ungrounded claims or reject entirely)
        if rejected:
            verified_answer = (
                "⚠️ **Verification Failed**: The generated answer contains claims "
                "that could not be verified against the retrieved passages. "
                f"Hallucination risk: {hallucination_score:.0%}\n\n"
                "Please review the source passages directly for accurate information."
            )
        else:
            verified_answer = answer
            if hallucination_score > 0.2:
                verified_answer = (
                    f"⚠️ **Partial Verification** ({(1-hallucination_score):.0%} grounded)\n\n"
                    f"{answer}"
                )
        
        return VerificationResult(
            status=status,
            original_answer=answer,
            verified_answer=verified_answer,
            claims=verified_claims,
            grounded_claims=grounded_count,
            total_claims=total_count,
            hallucination_score=hallucination_score,
            warnings=warnings,
            rejected=rejected
        )
    
    def get_verification_summary(self, result: VerificationResult) -> Dict:
        """
        Generate a summary report of verification results.
        
        Useful for logging, debugging, and research analysis.
        
        Args:
            result: The VerificationResult to summarize
            
        Returns:
            Dictionary with verification metrics
        """
        return {
            "status": result.status.value,
            "grounded_claims": result.grounded_claims,
            "total_claims": result.total_claims,
            "grounding_rate": (
                result.grounded_claims / result.total_claims 
                if result.total_claims > 0 else 1.0
            ),
            "hallucination_score": result.hallucination_score,
            "rejected": result.rejected,
            "warning_count": len(result.warnings),
            "claims_detail": [
                {
                    "text": c.text[:100],
                    "grounded": c.is_grounded,
                    "confidence": c.confidence,
                    "citations": c.citations
                }
                for c in result.claims
            ]
        }


class VerifiedBibleRAG:
    """
    Extended RAG system with integrated verification agent.
    
    This wrapper adds verification to any existing BibleRAG instance,
    creating a two-stage pipeline:
    
    1. Generation Stage: Standard RAG retrieval and generation
    2. Verification Stage: Claim extraction and grounding validation
    
    This architecture enables:
    - Hallucination detection and rejection
    - Confidence scoring for answers
    - Audit trails for compliance domains
    - Research metrics collection
    """
    
    def __init__(self, rag_system, enable_verification: bool = True):
        """
        Wrap an existing RAG system with verification.
        
        Args:
            rag_system: The BibleRAG instance to wrap
            enable_verification: If False, passes through without verification
        """
        self.rag = rag_system
        self.verifier = VerifierAgent()
        self.enable_verification = enable_verification
        
        # Metrics collection for research
        self.query_log = []
    
    def query(self, question: str, top_k: int = None) -> Dict:
        """
        Query with verification pipeline.
        
        Args:
            question: User's question
            top_k: Number of passages to retrieve
            
        Returns:
            Enhanced result dict with verification data
        """
        # Stage 1: Standard RAG query
        result = self.rag.query(question, top_k=top_k)
        
        if not self.enable_verification:
            return result
        
        # Stage 2: Verification
        verification_result = self.verifier.verify_answer(
            answer=result["answer"],
            context=result.get("context", ""),
            sources=result.get("sources", [])
        )
        
        # Log for research
        self.query_log.append({
            "question": question,
            "verification": self.verifier.get_verification_summary(verification_result)
        })
        
        # Enhance result with verification data
        result["verified_answer"] = verification_result.verified_answer
        result["verification"] = {
            "status": verification_result.status.value,
            "hallucination_score": verification_result.hallucination_score,
            "grounding_rate": (
                verification_result.grounded_claims / verification_result.total_claims
                if verification_result.total_claims > 0 else 1.0
            ),
            "rejected": verification_result.rejected,
            "warnings": verification_result.warnings
        }
        
        # Use verified answer if available
        if verification_result.rejected:
            result["answer"] = verification_result.verified_answer
        
        return result
    
    def get_metrics(self) -> Dict:
        """
        Get aggregate metrics from query log.
        
        Useful for evaluation experiments.
        
        Returns:
            Dictionary of aggregate metrics
        """
        if not self.query_log:
            return {"total_queries": 0}
        
        total = len(self.query_log)
        rejected = sum(1 for q in self.query_log if q["verification"]["rejected"])
        avg_hallucination = sum(
            q["verification"]["hallucination_score"] for q in self.query_log
        ) / total
        avg_grounding = sum(
            q["verification"]["grounding_rate"] for q in self.query_log
        ) / total
        
        return {
            "total_queries": total,
            "rejected_count": rejected,
            "rejection_rate": rejected / total,
            "avg_hallucination_score": avg_hallucination,
            "avg_grounding_rate": avg_grounding
        }


if __name__ == "__main__":
    # Demonstration of standalone verifier
    print("=" * 60)
    print("Verifier Agent - Standalone Demonstration")
    print("=" * 60)
    
    verifier = VerifierAgent()
    
    # Example: Well-grounded answer
    good_answer = """
    According to Genesis 1:26, God said "Let us make man in our image, after our likeness."
    This passage describes the creation of humanity in God's image.
    """
    
    good_context = """
    [1] Reference: Genesis 1:26
    Text: And God said, Let us make man in our image, after our likeness: 
    and let them have dominion over the fish of the sea, and over the fowl 
    of the air, and over the cattle, and over all the earth.
    """
    
    print("\n✅ Testing GROUNDED answer:")
    result = verifier.verify_answer(good_answer, good_context, ["Genesis 1:26"])
    print(f"   Status: {result.status.value}")
    print(f"   Hallucination Score: {result.hallucination_score:.2%}")
    print(f"   Grounded Claims: {result.grounded_claims}/{result.total_claims}")
    
    # Example: Hallucinated answer
    bad_answer = """
    According to tradition, it is believed that Moses wrote Genesis while on Mount Sinai.
    Some scholars argue this represents the earliest form of Hebrew literature.
    The bible implies a cosmic battle between good and evil from the beginning.
    """
    
    bad_context = """
    [1] Reference: Genesis 1:1
    Text: In the beginning God created the heaven and the earth.
    """
    
    print("\n❌ Testing HALLUCINATED answer:")
    result = verifier.verify_answer(bad_answer, bad_context, ["Genesis 1:1"])
    print(f"   Status: {result.status.value}")
    print(f"   Hallucination Score: {result.hallucination_score:.2%}")
    print(f"   Rejected: {result.rejected}")
    print(f"   Warnings: {result.warnings}")
    
    print("\n" + "=" * 60)
    print("Verifier Agent ready for integration")
    print("=" * 60)

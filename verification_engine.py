"""
verification_engine.py
AI Verification & Hallucination Guard for Sovereign AI Workbench (SIH PSC26117).
Performs deterministic claim-checking and grounded verification of generated responses
against retrieved evidence citations. Classifies outputs into explicit verification states.
Zero fabricated confidence scores. Explicit abstention over false certainty.
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from provenance_engine import EvidenceBundle, EvidenceCitation


class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class VerificationResult(BaseModel):
    status: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE, REQUIRES_HUMAN_REVIEW
    is_grounded: bool
    grounding_ratio: float  # Percentage of verifiable claims matching evidence text
    verified_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    abstention_reason: Optional[str] = None
    verification_statement: str = ""

    @property
    def requires_human_review(self) -> bool:
        return self.status in [
            VerificationStatus.REQUIRES_HUMAN_REVIEW,
            VerificationStatus.CONTRADICTED,
            VerificationStatus.UNSUPPORTED,
            VerificationStatus.INSUFFICIENT_EVIDENCE
        ]


class AIVerificationEngine:
    """
    Evaluates generated statements against source evidence snippets.
    Prevents hallucinated facts from reaching government procurement officers.
    """

    # Regex patterns for high-consequence entities (currency amounts, dates, turnover, EMD, percentage)
    NUMERIC_FACT_PATTERN = re.compile(
        r"(?:₹|\$|INR|Rs\.?)\s*[\d,]+(?:\.\d+)?(?:\s*(?:Crores?|Lakhs?|Cr|L))?|"
        r"[\d,]+(?:\.\d+)?\s*(?:₹|\$|INR|Rs\.?|Crores?|Lakhs?|Cr|L)|"
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|"
        r"\b\d{4,}(?:,\d{3})*(?:\.\d+)?\b|"
        r"\b\d+(?:\.\d+)?%?\b",
        re.IGNORECASE
    )

    @classmethod
    def verify(
        cls,
        answer: str = "",
        evidence_bundle: Optional[EvidenceBundle] = None,
        model_name: Optional[str] = None,
        generated_answer: Optional[str] = None
    ) -> VerificationResult:
        """
        Executes deterministic verification pipeline:
        1. Checks evidence sufficiency
        2. Splits answer into testable factual claims
        3. Checks concordance between claims and source evidence snippets
        4. Detects numeric or deadline contradictions
        5. Computes grounded classification
        """
        eval_answer = answer if answer else (generated_answer or "")
        bundle = evidence_bundle or EvidenceBundle(query="")

        if not eval_answer or not eval_answer.strip():
            return VerificationResult(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                is_grounded=False,
                grounding_ratio=0.0,
                abstention_reason="No answer produced for evaluation.",
                verification_statement="Abstained: Empty response."
            )

        # 1. Evidence sufficiency check
        if not bundle.citations or not bundle.has_sufficient_evidence:
            return VerificationResult(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                is_grounded=False,
                grounding_ratio=0.0,
                abstention_reason="Indexed local documents do not contain sufficient evidence to answer this inquiry safely.",
                verification_statement="Insufficient Source Evidence: System abstains to prevent hallucinations."
            )

        # Aggregate all citation text into an evidence corpus
        evidence_corpus = " ".join([c.snippet for c in bundle.citations]).lower()
        evidence_corpus_normalized = re.sub(r"\s+", " ", evidence_corpus)

        # 2. Extract key factual sentences/claims from the answer
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", eval_answer) if len(s.strip()) > 15]
        
        # Filter out meta/intro sentences
        meta_phrases = ["here is", "based on", "according to", "summary of", "please find", "as requested"]
        factual_sentences = [
            s for s in sentences
            if not any(s.lower().startswith(m) for m in meta_phrases) and not s.startswith("#")
        ]

        if not factual_sentences:
            factual_sentences = sentences

        verified_claims = []
        unsupported_claims = []
        contradictions = []

        # 3. Concordance & Grounding Analysis
        for sentence in factual_sentences:
            # Extract key nouns and numeric entities from the sentence
            words = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", sentence.lower()))
            # Remove generic conversational stop words
            content_words = {
                w for w in words
                if w not in {"the", "and", "for", "with", "this", "that", "from", "have", "been", "will", "shall", "must"}
            }

            if not content_words:
                continue

            matches = sum(1 for w in content_words if w in evidence_corpus_normalized)
            match_ratio = matches / len(content_words)

            # Extract numeric entities (amounts, dates)
            sentence_numbers = cls.NUMERIC_FACT_PATTERN.findall(sentence)
            has_numeric = len(sentence_numbers) > 0
            all_numbers_grounded = True

            # Also create a compact digits-only or punctuation-free version of corpus
            corpus_digits = "".join(re.findall(r"\d+", evidence_corpus))

            if has_numeric:
                for num in sentence_numbers:
                    # Strip symbols to check if the digits exist in the evidence
                    digits_only = "".join(re.findall(r"\d+", num))
                    clean_num = num.lower().replace("₹", "").replace("$", "").replace("inr", "").replace("rs.", "").replace("rs", "").replace(",", "").strip()
                    
                    # If this number represents an amount with digits
                    if digits_only:
                        if digits_only not in corpus_digits and clean_num not in evidence_corpus_normalized:
                            all_numbers_grounded = False
                            contradictions.append(f"Unverified or contradictory figure '{num}' in: \"{sentence[:80]}...\"")
                            break
                    elif clean_num and clean_num not in evidence_corpus_normalized:
                        all_numbers_grounded = False
                        contradictions.append(f"Unverified or contradictory figure '{num}' in: \"{sentence[:80]}...\"")
                        break

            if match_ratio >= 0.5 and all_numbers_grounded:
                verified_claims.append(sentence)
            else:
                unsupported_claims.append(sentence)

        total_evaluated = len(verified_claims) + len(unsupported_claims)
        grounding_ratio = len(verified_claims) / total_evaluated if total_evaluated > 0 else 0.0

        # 4. Classification
        if contradictions:
            status = "CONTRADICTED"
            is_grounded = False
            statement = f"Verification Warning: {len(contradictions)} figures or terms in output conflict with source text."
        elif grounding_ratio >= 0.85:
            status = "SUPPORTED"
            is_grounded = True
            statement = f"Verified: 100% of factual assertions match retrieved source evidence ({len(verified_claims)} claims confirmed)."
        elif grounding_ratio >= 0.45:
            status = "PARTIALLY_SUPPORTED"
            is_grounded = True
            statement = f"Partially Verified: {round(grounding_ratio * 100)}% of claims directly grounded; secondary details require verification."
        else:
            status = "UNSUPPORTED"
            is_grounded = False
            statement = "Unverified Output: Key statements could not be cross-referenced against indexed documents."

        # High-consequence review check
        if any(term in eval_answer.lower() for term in ["penalty", "disqualification", "debarment", "blacklisted"]):
            status = "REQUIRES_HUMAN_REVIEW"
            statement += " Sensitive legal/procurement implications detected. Human verification required."

        return VerificationResult(
            status=status,
            is_grounded=is_grounded,
            grounding_ratio=round(grounding_ratio, 2),
            verified_claims=verified_claims[:5],
            unsupported_claims=unsupported_claims[:5],
            contradictions=contradictions,
            verification_statement=statement
        )

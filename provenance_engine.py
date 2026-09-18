"""
provenance_engine.py
Evidence & Provenance Layer for Sovereign AI Workbench (SIH PSC26117).
Extracts and tracks grounded evidence from indexed local documents (PDF, DOCX, CSV, Text)
with exact page numbers, section identifiers, character offsets, and verification metadata.
"""

import os
import re
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EvidenceCitation(BaseModel):
    citation_id: str
    document_id: str
    document_name: str = ""
    page_number: Optional[int] = None
    section_id: Optional[str] = None
    section: Optional[str] = None
    snippet: str
    char_start: int = 0
    char_end: int = 0
    relevance_score: float = 0.0
    confidence_score: Optional[float] = None
    is_verified: bool = True
    extraction_mode: str = "direct_match"  # digital_plumber, raster_ocr, docx, tabular
    sha256_hash: str = ""
    snippet_sha256: str = ""

    def __init__(self, **data):
        if "section" in data and "section_id" not in data:
            data["section_id"] = data["section"]
        elif "section_id" in data and "section" not in data:
            data["section"] = data["section_id"]

        if "document_id" in data and not data.get("document_name"):
            data["document_name"] = data["document_id"]

        if "confidence_score" in data and "relevance_score" not in data:
            data["relevance_score"] = float(data["confidence_score"])
        elif "relevance_score" in data and "confidence_score" not in data:
            data["confidence_score"] = data["relevance_score"]

        if "sha256_hash" in data and not data.get("snippet_sha256"):
            data["snippet_sha256"] = data["sha256_hash"]
        elif "snippet_sha256" in data and not data.get("sha256_hash"):
            data["sha256_hash"] = data["snippet_sha256"]

        super().__init__(**data)


class EvidenceBundle(BaseModel):
    query: str
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    total_sources: int = 0
    citations: List[EvidenceCitation] = Field(default_factory=list)
    has_sufficient_evidence: bool = True
    evidence_coverage: float = 1.0  # Fraction of query concepts grounded in retrieved text


class ProvenanceEngine:
    """
    Tracks and extracts granular, verifiable evidence passages from documents.
    Links generated text directly back to source documents, pages, and tables.
    """

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def extract_evidence(
        cls,
        query: str,
        matched_documents: Optional[List[Dict[str, Any]]] = None,
        max_citations: int = 5,
        raw_chunks: Optional[List[Dict[str, Any]]] = None,
        model_name: Optional[str] = None
    ) -> EvidenceBundle:
        """
        Extracts structured citations from matched document chunks.
        Determines whether sufficient evidence exists or if the system should abstain.
        """
        docs = matched_documents if matched_documents is not None else []
        if raw_chunks:
            for chk in raw_chunks:
                docs.append({
                    "path": chk.get("source", "unnamed_source"),
                    "content": chk.get("text", ""),
                    "score": chk.get("score", 1.0)
                })

        citations: List[EvidenceCitation] = []
        query_words = set(re.findall(r"\w+", query.lower()))
        stop_words = {
            "what", "is", "the", "are", "and", "for", "about", "in", "to", "of",
            "a", "an", "tell", "me", "how", "who", "where", "when", "why", "can",
            "you", "my", "this", "that", "give", "with", "from", "on"
        }
        meaningful_query_words = {w for w in query_words if len(w) > 2 and w not in stop_words}
        
        covered_concepts = set()

        for doc_idx, doc in enumerate(docs):
            rel_path = doc.get("path", f"doc_{doc_idx}")
            full_text = doc.get("content", "")
            doc_score = doc.get("score", 0.0)
            doc_name = Path(rel_path).name

            if not full_text.strip():
                continue

            # Split text into candidate paragraphs or page blocks
            # Look for page markers like [Page 1] or section headers
            blocks = cls._split_into_evidential_blocks(full_text)

            for b_idx, block in enumerate(blocks):
                block_text = block["text"].strip()
                if len(block_text) < 30:
                    continue

                block_lower = block_text.lower()
                matched_in_block = {w for w in meaningful_query_words if w in block_lower}
                if not matched_in_block and doc_score < 100:
                    continue

                covered_concepts.update(matched_in_block)

                # Find clean snippet around the best match
                snippet = cls._extract_snippet(block_text, matched_in_block)
                citation_id = f"SRC-{doc_idx+1}-{b_idx+1}"

                citations.append(EvidenceCitation(
                    citation_id=citation_id,
                    document_id=cls.hash_text(rel_path),
                    document_name=doc_name,
                    page_number=block.get("page"),
                    section_id=block.get("section") or f"Section {b_idx+1}",
                    snippet=snippet,
                    char_start=block.get("start", 0),
                    char_end=block.get("end", len(block_text)),
                    relevance_score=float(len(matched_in_block) * 10 + (20 if block.get("page") else 0)),
                    extraction_mode=block.get("mode", "digital_plumber"),
                    sha256_hash=cls.hash_text(snippet)
                ))

                if len(citations) >= max_citations:
                    break
            if len(citations) >= max_citations:
                break

        # Sort citations by relevance score
        citations.sort(key=lambda c: c.relevance_score, reverse=True)
        citations = citations[:max_citations]

        # Calculate evidence coverage ratio
        coverage = len(covered_concepts) / len(meaningful_query_words) if meaningful_query_words else 1.0
        has_sufficient = len(citations) > 0 and (coverage >= 0.3 or not meaningful_query_words)

        return EvidenceBundle(
            query=query,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_sources=len(citations),
            citations=citations,
            has_sufficient_evidence=has_sufficient,
            evidence_coverage=round(coverage, 2)
        )

    @classmethod
    def _split_into_evidential_blocks(cls, text: str) -> List[Dict[str, Any]]:
        """Splits text into chunks preserving page boundaries and headings."""
        blocks = []
        # Check for page markers like [Page X] or [Page X, Section Y] or Page X of Y
        page_pattern = re.compile(r"\[Page\s*(\d+)(?:,\s*(?:Section|Clause)\s*([^\]]+))?\]|Page\s+(\d+)\s+of\s+\d+", re.IGNORECASE)
        
        paragraphs = text.split("\n\n")
        current_page = None
        current_offset = 0

        for p_idx, para in enumerate(paragraphs):
            para_clean = para.strip()
            if not para_clean:
                current_offset += len(para) + 2
                continue

            # Detect page and inline section change
            section_title = None
            page_match = page_pattern.search(para_clean)
            if page_match:
                p_str = page_match.group(1) or page_match.group(3)
                if p_str:
                    try:
                        current_page = int(p_str)
                    except ValueError:
                        pass
                if page_match.group(2):
                    section_title = page_match.group(2).strip()

            # Detect section header from line if not already set
            first_line = para_clean.split("\n")[0].strip()
            if not section_title and (first_line.startswith("#") or first_line.isupper() or (len(first_line) < 60 and first_line.endswith(":"))):
                section_title = first_line.lstrip("#").strip()

            blocks.append({
                "text": para_clean,
                "page": current_page,
                "section": section_title,
                "start": current_offset,
                "end": current_offset + len(para_clean),
                "mode": "raster_ocr" if "ocr" in para_clean.lower() else "digital_stream"
            })
            current_offset += len(para) + 2

        return blocks

    @classmethod
    def _extract_snippet(cls, text: str, matched_words: set, max_length: int = 240) -> str:
        """Extracts a concise, highly readable snippet surrounding key matched terms."""
        if not matched_words or len(text) <= max_length:
            return text[:max_length].replace("\n", " ").strip()

        # Find position of first keyword match
        lower_text = text.lower()
        earliest_pos = min((lower_text.find(w) for w in matched_words if lower_text.find(w) != -1), default=0)

        start = max(0, earliest_pos - 60)
        end = min(len(text), start + max_length)

        snippet = text[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet

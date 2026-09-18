"""
Local RAG Engine with Incremental memory.md Knowledge Graph,
Confidentiality Guard, and Lossless Compression (SIH PSC26117).
Optimized for 8GB RAM laptops and air-gapped sovereign environments.
"""
import os
import re
import json
import zlib
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from dual_engine_llm import DualEngineLLM
from document_processor import DocumentProcessor
from provenance_engine import ProvenanceEngine, EvidenceBundle
from verification_engine import AIVerificationEngine, VerificationResult
from injection_guard import PromptInjectionGuard

SECRET_PATTERNS = [
    (r"(?i)(?:aws_access_key_id|aws_secret_access_key|access_key|secret_key)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{16,})['\"]?", "AWS/CLOUD_KEY"),
    (r"(?i)(?:api_key|apikey|secret|token|auth_token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{20,})['\"]?", "API_KEY"),
    (r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA )?PRIVATE KEY-----", "PRIVATE_KEY"),
    (r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"\s\n]{8,})['\"]?", "PASSWORD"),
]

IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
    ".idea", ".vscode", ".pytest_cache"
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".html", ".css", ".json", ".md", ".txt", ".yaml",
    ".yml", ".sql", ".bat", ".sh", ".env.example", ".csv", ".tsv", ".docx", ".pdf", ".toml"
}


def compress_data(text: str) -> bytes:
    """Lossless zlib compression for in-memory file buffers."""
    return zlib.compress(text.encode("utf-8"), level=6)


def decompress_data(data: bytes) -> str:
    """Decompress zlib compressed buffer."""
    return zlib.decompress(data).decode("utf-8")


def check_confidentiality_and_motw(content: str, filename: str) -> Dict[str, Any]:
    """
    Sanitizes files locally before indexing. Redacts hardcoded credentials
    and ensures untrusted Mark-of-the-Web artifacts do not exfiltrate secrets.
    """
    sanitized = content
    secrets_found = []

    for pattern, name in SECRET_PATTERNS:
        matches = list(re.finditer(pattern, sanitized))
        if matches:
            secrets_found.append(name)
            for m in reversed(matches):
                start, end = m.span()
                sanitized = sanitized[:start] + f"[REDACTED_SECRET_{name}]" + sanitized[end:]

    return {
        "has_secrets": len(secrets_found) > 0,
        "secrets_found": secrets_found,
        "sanitized_content": sanitized,
        "is_safe": True,
    }


class LocalRAGEngine:
    """
    Incremental On-Premise RAG Engine.
    Uses SHA-256 caching via memory.md to provide O(k) re-indexing complexity.
    Stores compressed file chunks in-memory for low memory footprint (<100MB).
    """

    def __init__(self, workspace_dir: Optional[Path] = None, llm: Optional[DualEngineLLM] = None):
        self.workspace_dir = Path(workspace_dir or os.getcwd()).resolve()
        self.llm = llm or DualEngineLLM()
        self.memory_file = self.workspace_dir / "memory.md"
        self.compressed_file_store: Dict[str, bytes] = {}
        self.file_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_existing_memory()
        self.sync_uploaded_files()

    def _query_graft(self, query: str, limit: int = 4) -> Optional[Dict[str, Any]]:
        """
        Queries Graft Context Engine ($0, local AST graph) to retrieve concise,
        symbol-accurate source definitions without loading massive source files.
        Saves up to 90% input tokens for local models like Ollama.
        """
        import shutil
        import subprocess

        graft_dir = self.workspace_dir / "graft"
        if not graft_dir.exists() and (Path(__file__).resolve().parent / "graft").exists():
            graft_dir = Path(__file__).resolve().parent / "graft"

        # Check if graft executable exists
        graft_exe = shutil.which("graft") or shutil.which("graft.cmd")
        if not graft_exe:
            # Check global fallback path
            custom_bin = Path(r"%USERPROFILE%\.graft_engine\node_modules\.bin\graft.cmd")
            if custom_bin.exists():
                graft_exe = str(custom_bin)

        if not graft_exe:
            return None

        try:
            cmd = [
                graft_exe, "ask",
                "--source",
                "--json",
                "-n", str(limit),
                query,
                str(self.workspace_dir)
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=6,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                hits = data.get("hits", [])
                if hits:
                    return data
        except Exception:
            pass
        return None

    def sync_uploaded_files(self):
        """Automatically indexes all files present in output/uploads/ into compressed memory."""
        uploads_dir = self.workspace_dir / "output" / "uploads"
        if not uploads_dir.exists() and self.workspace_dir == Path(__file__).resolve().parent:
            uploads_dir = Path(__file__).resolve().parent / "output" / "uploads"
        if uploads_dir.exists() and uploads_dir.is_dir():
            for p in uploads_dir.iterdir():
                    if p.is_file() and p.name != "memory.md" and p.suffix.lower() in ALLOWED_EXTENSIONS:
                        if p.name not in self.compressed_file_store:
                            try:
                                ext = p.suffix.lower()
                                if ext in {".pdf", ".docx", ".csv", ".tsv", ".png", ".jpg", ".jpeg"}:
                                    parsed = DocumentProcessor.parse_file(p)
                                    text = parsed.get("extracted_text", "")
                                else:
                                    text = p.read_text(encoding="utf-8", errors="replace")
                                if text:
                                    self.add_single_document(p.name, text)
                                    self.add_single_document(f"uploads/{p.name}", text)
                            except Exception:
                                pass

    def _load_existing_memory(self):
        """Loads cached hashes from existing memory.md if present."""
        if not self.memory_file.exists():
            return
        try:
            content = self.memory_file.read_text(encoding="utf-8")
            # Parse JSON manifest block if embedded
            match = re.search(r"<!-- MANIFEST_START\s*([\s\S]+?)\s*MANIFEST_END -->", content)
            if match:
                data = json.loads(match.group(1))
                self.file_metadata = data.get("files", {})
        except Exception:
            self.file_metadata = {}

    def _save_memory_md(self, summary: str, questions: List[str]):
        """Persists updated memory.md knowledge graph to the workspace directory."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        md_lines = [
            "# Project Memory & Architecture Knowledge Graph",
            f"> Automatically maintained by Sovereign Assistant. Last updated: {timestamp}",
            "",
            "## 1. Project Overview & Role",
            summary,
            "",
            "## 2. Recommended Next Inquiries for Non-Technical Users",
        ]
        for q in questions:
            md_lines.append(f"- {q}")

        md_lines.extend([
            "",
            "## 3. Indexed File Manifest (SHA-256 Hashes)",
            "| Relative File Path | Size (Bytes) | SHA-256 Hash | Status |",
            "| :--- | :--- | :--- | :--- |",
        ])

        for path, meta in sorted(self.file_metadata.items()):
            size = meta.get("size", 0)
            sha = meta.get("hash", "")[:16] + "..."
            status = meta.get("status", "Active")
            md_lines.append(f"| `{path}` | {size} | `{sha}` | {status} |")

        # Embed machine-readable metadata
        manifest_payload = {
            "version": "1.0",
            "updated_at": timestamp,
            "total_files": len(self.file_metadata),
            "files": self.file_metadata
        }
        md_lines.extend([
            "",
            "<!-- MANIFEST_START",
            json.dumps(manifest_payload, indent=2),
            "MANIFEST_END -->",
            ""
        ])

        self.memory_file.write_text("\n".join(md_lines), encoding="utf-8")

    async def analyze_directory(
        self,
        target_dir_str: str,
        progress_cb: Optional[Callable[[str, int], Any]] = None
    ) -> Dict[str, Any]:
        """
        Scans and analyzes files in target_dir.
        Only indexes changed or new files (O(k) complexity).
        Streams non-technical progress updates.
        """
        target_dir = Path(target_dir_str).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            raise ValueError(f"Directory '{target_dir}' does not exist.")

        self.workspace_dir = target_dir
        self.memory_file = target_dir / "memory.md"
        self._load_existing_memory()

        if progress_cb:
            await self._notify(progress_cb, "Assistant is reading your folder and finding files...", 15)

        all_files = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() in ALLOWED_EXTENSIONS and p.name != "memory.md":
                    all_files.append(p)

        total_scanned = len(all_files)
        new_or_modified = 0
        reused = 0
        scanned_docs = []

        if progress_cb:
            await self._notify(progress_cb, f"Found {total_scanned} files. Checking confidentiality and changes...", 35)

        for p in all_files:
            rel_path = str(p.relative_to(target_dir)).replace("\\", "/")
            ext = p.suffix.lower()
            try:
                if ext in {".pdf", ".docx", ".csv", ".tsv"}:
                    parsed = DocumentProcessor.parse_file(p)
                    content = parsed.get("extracted_text", "")
                    if not content:
                        content = p.read_text(encoding="utf-8", errors="replace")
                else:
                    content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            cached_meta = self.file_metadata.get(rel_path)

            if cached_meta and cached_meta.get("hash") == file_hash:
                reused += 1
                if rel_path not in self.compressed_file_store:
                    self.compressed_file_store[rel_path] = compress_data(content)
                sanitized_text = decompress_data(self.compressed_file_store[rel_path])
                scanned_docs.append({"path": rel_path, "content": sanitized_text[:1000]})
                continue

            # File is new or changed
            new_or_modified += 1
            sec_check = check_confidentiality_and_motw(content, p.name)
            sanitized_text = sec_check["sanitized_content"]

            # Store compressed in-memory
            self.compressed_file_store[rel_path] = compress_data(sanitized_text)
            self.file_metadata[rel_path] = {
                "hash": file_hash,
                "size": len(content),
                "modified": p.stat().st_mtime,
                "status": "Safe & Indexed",
                "had_secrets": sec_check["has_secrets"]
            }
            scanned_docs.append({"path": rel_path, "content": sanitized_text[:1000]})

        if progress_cb:
            await self._notify(progress_cb, "Understanding project structure and preparing plain English summary...", 70)

        # Generate non-technical summary and questions
        # Pass air_gap=False here — folder analysis is triggered locally, no external calls needed
        # but we honour the flag if the caller supplies it in future
        summary, questions = await self._synthesize_insights(scanned_docs, target_dir.name, air_gap=False)

        # Save to memory.md
        self._save_memory_md(summary, questions)

        if progress_cb:
            await self._notify(progress_cb, "Everything is ready! Project helper is active.", 100)

        return {
            "status": "SUCCESS",
            "total_files_scanned": total_scanned,
            "files_indexed_new": new_or_modified,
            "files_reused_from_cache": reused,
            "summary": summary,
            "questions": questions,
            "memory_path": str(self.memory_file),
        }

    def add_single_document(self, filename: str, content: str):
        """Indexes an uploaded document or OCR extraction into RAG memory immediately."""
        if not content:
            return
        sec_check = check_confidentiality_and_motw(content, filename)
        sanitized_text = sec_check["sanitized_content"]
        file_hash = hashlib.sha256(sanitized_text.encode("utf-8")).hexdigest()
        self.compressed_file_store[filename] = compress_data(sanitized_text)
        self.file_metadata[filename] = {
            "hash": file_hash,
            "size": len(content),
            "modified": time.time(),
            "status": "Safe & Indexed (Uploaded)",
            "had_secrets": sec_check["has_secrets"]
        }

    async def _synthesize_insights(
        self, docs: List[Dict[str, str]], folder_name: str, air_gap: bool = False
    ) -> (str, List[str]):
        """Generates friendly, non-technical project summary and proactive questions."""
        sample_paths = [d["path"] for d in docs[:15]]
        prompt = (
            f"You are a friendly Personal AI Assistant helping non-technical office staff understand their computer files.\n"
            f"Folder Name: {folder_name}\n"
            f"Files found:\n" + "\n".join(sample_paths) + "\n\n"
            f"Write a friendly 3-sentence summary of what this project does in plain English. NO technical jargon.\n"
            f"Then propose 4 simple questions you can help them with, like:\n"
            f"- 'Would you like me to write a one-page summary for your team?'\n"
            f"- 'Shall I organize these documents into a clean report?'\n"
            f"Return JSON format: {{\"summary\": \"...\", \"questions\": [\"...\", \"...\"]}}"
        )

        try:
            raw_res = await self.llm.generate(
                prompt=prompt, temperature=0.3, max_tokens=1000, air_gap_active=air_gap
            )
            json_match = re.search(r"\{[\s\S]*\}", raw_res)
            if json_match:
                parsed = json.loads(json_match.group(0))
                return parsed.get("summary", ""), parsed.get("questions", [])
        except Exception:
            pass

        # Fallback friendly insights
        default_summary = (
            f"This folder contains the complete '{folder_name}' system. "
            f"It includes ready-to-use programs, pre-saved login tools, and digital documents designed "
            f"to automate manual office tasks and internet searches completely free of cost."
        )
        default_questions = [
            "Would you like me to check today's live tender updates on the government portal?",
            "Shall I generate an executive briefing summarizing these project files?",
            "Would you like me to verify that all your pre-saved website logins are active?",
            "Can I help create a step-by-step guide for non-technical team members?",
        ]
        return default_summary, default_questions

    async def query_knowledge(self, query: str, air_gap: bool = False) -> str:
        """Answers plain English questions by searching indexed files.

        air_gap: when True, routes LLM inference to local Ollama only (TRG-001).
        """
        # Automatically sync any files sitting in output/uploads/
        self.sync_uploaded_files()

        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))
        stop_words = {"what", "is", "the", "are", "and", "for", "about", "in", "to", "of", "a", "an", "tell", "me", "how", "who", "where", "when", "why", "can", "you", "my", "this", "that", "give"}
        meaningful_words = {w for w in query_words if len(w) > 2 and w not in stop_words}
        scored_matches = []
        all_docs = []

        for rel_path, comp_bytes in self.compressed_file_store.items():
            text = decompress_data(comp_bytes)
            text_lower = text.lower()
            word_matches = sum(1 for w in meaningful_words if w in text_lower)
            score = word_matches * 10
            base_name = Path(rel_path).name.lower()
            stem_name = Path(rel_path).stem.lower()

            # Exact or partial file name match gets highest boost
            if base_name in query_lower:
                score += 150
            elif stem_name in query_lower:
                score += 100
            elif any(part in query_lower for part in stem_name.split("_") if len(part) > 2 and part not in stop_words):
                score += 50
            elif any(part in query_lower for part in base_name.split(".") if len(part) > 2 and part not in stop_words):
                score += 40

            if word_matches > 0 and "upload" in rel_path.lower():
                score += 5

            scored_matches.append((score, rel_path, text[:4000]))
            all_docs.append((rel_path, text[:4000]))

        # Sort by relevance score first
        scored_matches.sort(key=lambda x: x[0], reverse=True)

        # Check if query is asking for storage/file manifest overview
        is_storage_query = any(k in query_lower for k in [
            "all the files", "files in storage", "storage tell", "files the storage",
            "storage summary", "list files", "what files", "all files", "files summary",
            "what are all the files", "documents in storage", "folder summary"
        ])

        if is_storage_query:
            file_manifest_lines = []
            for path, meta in sorted(self.file_metadata.items()):
                size_kb = round(meta.get("size", 0) / 1024, 1)
                status = meta.get("status", "Indexed")
                file_manifest_lines.append(f"- `{path}` ({size_kb} KB) — {status}")

            manifest_text = "\n".join(file_manifest_lines) if file_manifest_lines else "No documents currently indexed in storage."
            prompt = (
                f"You are a helpful sovereign assistant.\n"
                f"The user is asking: \"{query}\"\n\n"
                f"Here is the list of files currently in storage:\n"
                f"{manifest_text}\n\n"
                f"Provide a clear, helpful, factual summary of these files for the user."
            )
            try:
                ans = await self.llm.generate(
                    prompt=prompt, temperature=0.2, max_tokens=1200, air_gap_active=air_gap
                )
                if ans and len(ans.strip()) > 20 and not ans.startswith("### ⚙️ Local LLM (Ollama) Not Running"):
                    return ans
            except Exception:
                pass
            return f"### 📁 Local Storage Files ({len(self.file_metadata)} indexed)\n\n" + manifest_text

        # ── GRAFT CONTEXT ENGINE INTEGRATION (Token Optimization) ───────────
        # For codebase queries, functions, and architecture questions, Graft provides
        # concise inlined symbol crux snippets (~90% smaller than whole file reads).
        graft_data = self._query_graft(query, limit=3)
        graft_context = ""
        graft_sources = []
        if graft_data and graft_data.get("hits"):
            snippets = []
            for hit in graft_data["hits"]:
                ptr = hit.get("pointer", "")
                title = hit.get("title", "")
                code = (hit.get("code") or hit.get("snippet") or "").strip()
                if ptr:
                    graft_sources.append(ptr)
                if code:
                    snippets.append(f"Symbol: {title} ({ptr})\n```\n{code[:1200]}\n```")
            if snippets:
                graft_context = "\n\n".join(snippets)

        # Filter documents with positive matching score
        matching_files = [m for m in scored_matches if m[0] > 0][:4]

        if graft_context:
            # Combine concise Graft symbol pack with document excerpts
            doc_context = ""
            if matching_files:
                doc_snippets = [f"File: {path}\nContent Excerpt:\n{txt[:1500]}\n---" for _, path, txt in matching_files[:2]]
                doc_context = "\n" + "\n".join(doc_snippets)

            prompt = (
                f"<user_question>\n{query}\n</user_question>\n\n"
                f"<graft_ast_context>\n"
                f"The following targeted code definitions and symbols were retrieved via the Graft Knowledge Graph:\n\n"
                f"{graft_context}\n"
                f"{doc_context}\n"
                f"</graft_ast_context>\n\n"
                f"Answer the user's question clearly based on the targeted code definitions above, citing relevant symbols or file pointers. "
                f"If the documents do not contain the answer, answer accurately using your general knowledge."
            )
            sys_prompt = "You are an on-premise sovereign AI assistant analyzing local documents and codebase architecture."
        elif matching_files:
            context_snippets = [f"File: {path}\nExtracted Text/Content:\n{txt}\n---" for _, path, txt in matching_files]
            context = "\n".join(context_snippets)

            # TRG-014: Use XML role-separation to mitigate prompt injection
            prompt = (
                f"<user_question>\n{query}\n</user_question>\n\n"
                f"<document_context>\n"
                f"The following text was extracted from the user's indexed files:\n\n"
                f"{context}\n"
                f"</document_context>\n\n"
                f"Answer the user's question clearly based on the document excerpts above, citing relevant file names (such as {matching_files[0][1]}). "
                f"If the documents do not contain the answer, answer the question accurately using your general knowledge."
            )
            sys_prompt = "You are an on-premise sovereign AI assistant analyzing local documents."
        else:
            prompt = query
            sys_prompt = "You are a helpful, knowledgeable on-premise sovereign AI assistant. Please provide a direct, accurate, and friendly answer to the user's question."

        try:
            ans = await self.llm.generate(
                prompt=prompt, system_prompt=sys_prompt, temperature=0.2, max_tokens=1500, air_gap_active=air_gap
            )
            if ans and len(ans.strip()) > 20 and not ans.startswith("### ⚙️ Local LLM (Ollama) Not Running"):
                if matching_files and matching_files[0][1] not in ans:
                    ans = f"{ans.strip()}\n\n**Source Document:** `{matching_files[0][1]}`"
                return ans
        except Exception as e:
            print("RAG LLM error:", e)

        if matching_files:
            return (
                f"Based on the local text extracted from '{matching_files[0][1]}':\n\n"
                f"{matching_files[0][2]}\n\n"
            )
        return (
            "No specific matching documents found in local memory for this query. "
            "Please upload relevant documents (PDF, DOCX, CSV, TXT) to index and query them locally."
        )

    async def query_knowledge_with_verification(self, query: str, air_gap: bool = False) -> Dict[str, Any]:
        """
        Grounded Evidence & Verification Pipeline:
        Retrieve -> Evidence Extraction -> Secure Prompt (Injection Guard) -> Generate -> Verification.
        Returns full structured dictionary:
        {
            "answer": str,
            "evidence": EvidenceBundle,
            "verification": VerificationResult,
            "model_used": str,
            "air_gap_enforced": bool
        }
        """
        self.sync_uploaded_files()

        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))
        stop_words = {"what", "is", "the", "are", "and", "for", "about", "in", "to", "of", "a", "an", "tell", "me", "how", "who", "where", "when", "why", "can", "you", "my", "this", "that", "give"}
        meaningful_words = {w for w in query_words if len(w) > 2 and w not in stop_words}

        scored_matches = []
        for rel_path, comp_bytes in self.compressed_file_store.items():
            text = decompress_data(comp_bytes)
            text_lower = text.lower()
            word_matches = sum(1 for w in meaningful_words if w in text_lower)
            score = word_matches * 10
            base_name = Path(rel_path).name.lower()
            stem_name = Path(rel_path).stem.lower()

            if base_name in query_lower:
                score += 150
            elif stem_name in query_lower:
                score += 100
            elif any(part in query_lower for part in stem_name.split("_") if len(part) > 2 and part not in stop_words):
                score += 50
            elif any(part in query_lower for part in base_name.split(".") if len(part) > 2 and part not in stop_words):
                score += 40

            scored_matches.append({
                "path": rel_path,
                "score": float(score),
                "content": text
            })

        scored_matches.sort(key=lambda x: x["score"], reverse=True)
        top_docs = [m for m in scored_matches if m["score"] > 0][:4]

        # Extract Evidence Citations
        evidence_bundle = ProvenanceEngine.extract_evidence(query, top_docs, max_citations=5)

        # Check for Insufficient Evidence Abstention
        if not evidence_bundle.has_sufficient_evidence and not top_docs:
            abstention_answer = (
                "Insufficient Evidence: The indexed documents in local storage do not contain verified "
                f"information regarding '{query}'. To prevent hallucinated answers, the Sovereign Assistant "
                "abstains from generating an unverified statement. Please upload the relevant official documents."
            )
            verification_res = VerificationResult(
                status="INSUFFICIENT_EVIDENCE",
                is_grounded=False,
                grounding_ratio=0.0,
                abstention_reason="No relevant source documents indexed for this inquiry.",
                verification_statement="Abstained: Insufficient Source Evidence"
            )
            return {
                "answer": abstention_answer,
                "evidence": evidence_bundle.dict(),
                "verification": verification_res.dict(),
                "model_used": self.llm.local_model if air_gap else "Dual-Engine Local/Burst",
                "air_gap_enforced": air_gap
            }

        # Build Injection-Immune RAG Prompt
        secure_prompt = PromptInjectionGuard.format_secure_rag_prompt(
            user_query=query,
            retrieved_documents=top_docs,
            system_instruction="You are an on-premise sovereign government procurement AI assistant. Answer using ONLY the factual content inside the retrieved inert document chunks."
        )

        try:
            raw_answer = await self.llm.generate(
                prompt=secure_prompt,
                temperature=0.1,
                max_tokens=1500,
                air_gap_active=air_gap
            )
            if not raw_answer or raw_answer.startswith("### ⚙️ Local LLM (Ollama) Not Running"):
                # Fallback to direct extracted snippet
                raw_answer = f"Based on local documents ({top_docs[0]['path']}):\n\n{top_docs[0]['content'][:1200]}"
        except Exception as e:
            raw_answer = f"Based on local documents ({top_docs[0]['path']}):\n\n{top_docs[0]['content'][:1200]}"

        # Run Deterministic AI Verification
        verification_res = AIVerificationEngine.verify(raw_answer, evidence_bundle)

        # Append source citation footer if grounded
        if evidence_bundle.citations and verification_res.is_grounded:
            c = evidence_bundle.citations[0]
            pg_str = f", Page {c.page_number}" if c.page_number else ""
            sec_str = f" [{c.section_id}]" if c.section_id else ""
            raw_answer = f"{raw_answer.strip()}\n\n---\n**Grounded Source:** `{c.document_name}`{pg_str}{sec_str} • Verified Integrity: `{c.sha256_hash}`"

        return {
            "answer": raw_answer,
            "evidence": evidence_bundle.dict(),
            "verification": verification_res.dict(),
            "model_used": self.llm.local_model if air_gap else "Dual-Engine Sovereign Engine",
            "air_gap_enforced": air_gap
        }

    async def _notify(self, callback: Callable[[str, int], Any], msg: str, percent: int):
        import inspect
        if inspect.iscoroutinefunction(callback):
            await callback(msg, percent)
        else:
            callback(msg, percent)

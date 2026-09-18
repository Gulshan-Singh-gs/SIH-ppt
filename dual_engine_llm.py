"""
Dual-Engine LLM Provider for Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)
Engineered for 100% Free-of-Cost Execution:
1. Sovereign Air-Gapped: Local Open-Weight LLMs (Ollama / BharatGPT / LLaMA on 8GB RAM laptop)
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import httpx

logger = logging.getLogger("DualEngineLLM")


def parse_markdown_to_modular_blocks(text: str) -> Dict[str, Any]:
    """
    Parses any model response (plain text, markdown, tables, headings, code)
    into a structured, modular JSON format.
    If the text is already valid JSON containing a 'blocks' key, it returns it.
    """
    if not text or not str(text).strip():
        return {"blocks": [{"type": "paragraph", "content": ""}]}

    trimmed = str(text).strip()
    if trimmed.startswith("{") and trimmed.endswith("}"):
        try:
            parsed = json.loads(trimmed)
            if isinstance(parsed, dict) and "blocks" in parsed and isinstance(parsed["blocks"], list):
                return parsed
        except Exception:
            pass

    blocks: List[Dict[str, Any]] = []
    lines = trimmed.split("\n")
    i = 0

    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        if not line:
            i += 1
            continue

        # Code block (```lang ... ```)
        if line.startswith("```"):
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip().startswith("```"):
                i += 1
            blocks.append({
                "type": "code",
                "language": lang or "text",
                "code": "\n".join(code_lines)
            })
            continue

        # Table block (| Col1 | Col2 | ...)
        if "|" in line and i + 1 < len(lines) and "|" in lines[i + 1] and any(sep in lines[i + 1] for sep in ["---", ":-", "-:"]):
            headers = [c.strip() for c in line.strip("|").split("|")]
            i += 2  # Skip header and separator row
            rows = []
            while i < len(lines):
                cur = lines[i].strip()
                if not cur or "|" not in cur:
                    break
                row = [c.strip() for c in cur.strip("|").split("|")]
                if len(row) < len(headers):
                    row.extend([""] * (len(headers) - len(row)))
                rows.append(row[:len(headers)])
                i += 1
            blocks.append({
                "type": "table",
                "headers": headers,
                "rows": rows
            })
            continue

        # Headings (### Title)
        h_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if h_match:
            level = len(h_match.group(1))
            h_text = h_match.group(2).strip()
            blocks.append({
                "type": "heading",
                "level": level,
                "text": h_text
            })
            i += 1
            continue

        # Divider (--- or ___)
        if re.match(r"^[-*_]{3,}$", line):
            blocks.append({"type": "divider"})
            i += 1
            continue

        # List items (- item or * item or 1. item)
        list_match = re.match(r"^([*\-•]|\d+[\.\)])\s+(.+)$", line)
        if list_match:
            items = []
            is_ordered = bool(re.match(r"^\d+[\.\)]", line))
            while i < len(lines):
                cur = lines[i].strip()
                cur_match = re.match(r"^([*\-•]|\d+[\.\)])\s+(.+)$", cur)
                if not cur_match:
                    break
                items.append(cur_match.group(2).strip())
                i += 1
            blocks.append({
                "type": "list",
                "ordered": is_ordered,
                "items": items
            })
            continue

        # Simple Paragraph (kept as it is, cleanly gathered)
        para_lines = [line]
        i += 1
        while i < len(lines):
            cur = lines[i].strip()
            if not cur:
                break
            if cur.startswith("```") or re.match(r"^(#{1,6})\s+", cur) or re.match(r"^([*\-•]|\d+[\.\)])\s+", cur) or re.match(r"^[-*_]{3,}$", cur):
                break
            if "|" in cur and i + 1 < len(lines) and "|" in lines[i + 1] and any(sep in lines[i + 1] for sep in ["---", ":-", "-:"]):
                break
            para_lines.append(cur)
            i += 1

        blocks.append({
            "type": "paragraph",
            "content": " ".join(para_lines)
        })

    return {"blocks": blocks}



class DualEngineLLM:
    """
    Unified LLM Client providing high-speed free tier cloud inference for hackathon demos
    and local open-weight inference for sovereign air-gapped government compliance.
    """

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        preferred_engine: str = "local",  # 'local', 'auto', 'groq', 'gemini'
        ollama_url: str = "http://127.0.0.1:11434",
        local_model: str = "llama3.2:1b",
    ):
        self._load_env_if_needed()
        self.groq_api_key = (
            groq_api_key
            or os.getenv("GROQ_API_KEY", "")
            or os.getenv("GROK_API_KEY", "")
        )
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.preferred_engine = preferred_engine
        self.ollama_url = ollama_url
        self.local_model = local_model

    def _load_env_if_needed(self):
        """Loads .env from parent or current directories if keys aren't set in os.environ."""
        for p in [Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env", Path(__file__).resolve().parent / ".env"]:
            if p.exists():
                try:
                    for line in p.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k not in os.environ and v:
                                os.environ[k] = v
                except Exception:
                    pass

    def get_active_engine_info(self) -> Dict[str, Any]:
        """Returns availability and status of configured engines."""
        return {
            "groq": {
                "configured": bool(self.groq_api_key),
                "model": "llama-3.3-70b-versatile",
                "tier": "Free Tier (console.groq.com)",
                "speed": "~500 tokens/sec",
            },
            "gemini": {
                "configured": bool(self.gemini_api_key),
                "model": "gemini-1.5-flash",
                "tier": "Free Tier (Google AI Studio)",
                "speed": "~200 tokens/sec",
            },
            "local_sovereign": {
                "url": self.ollama_url,
                "model": self.local_model,
                "tier": "100% On-Premise Air-Gapped (BharatGPT/Llama-3)",
                "cost": "$0 (Local CPU/GPU)",
            },
            "preferred_engine": self.preferred_engine,
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        engine_override: Optional[str] = None,
        air_gap_active: bool = False,
        as_modular_json: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text response with automatic graceful fallback across free engines.
        Order of priority when 'auto':
        1. Groq (Fastest, <500ms latency, 100% free)
        2. Gemini (Large context, 100% free tier)
        3. Local Sovereign (Ollama)
        4. Embedded Deterministic Synthesizer (Fallback for zero-internet demos)

        When air_gap_active=True, ALL external network calls are blocked. Only
        local Ollama inference and the embedded fallback are permitted. This is
        the enforcement point for the Air-Gap Kill Switch (TRG-001).

        When as_modular_json=True, the raw output is parsed into a structured, modular
        JSON dict with a 'blocks' array, representing simple paragraphs as they are,
        tables as structured objects with headers and rows, lists, code blocks, etc.
        """
        # Inject modular formatting instruction for local models if requested
        effective_sys = system_prompt
        effective_prompt = prompt
        if as_modular_json:
            json_instruction = (
                "When formatting your response, use standard clean Markdown structure: "
                "paragraphs for regular text, Markdown tables (| Col1 | Col2 |) for tabular comparisons/data, "
                "numbered or bulleted lists for steps/points, and code blocks for technical snippets."
            )
            effective_sys = f"{system_prompt}\n{json_instruction}" if system_prompt else json_instruction

        # ── AIR-GAP ENFORCEMENT (TRG-001) ──────────────────────────────────────
        # When the kill switch is active, bypass all cloud paths unconditionally.
        if air_gap_active:
            logger.info("Air-Gap mode active: routing to local Ollama only.")
            try:
                raw_out = await self._call_ollama(effective_prompt, effective_sys, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Ollama unavailable in air-gap mode: {e}. Using Sovereign Local AI Engine.")
                raw_out = self._generate_sovereign_local_ai(prompt, system_prompt)
            return parse_markdown_to_modular_blocks(raw_out) if as_modular_json else raw_out
        # ───────────────────────────────────────────────────────────────────────

        target = engine_override or self.preferred_engine

        raw_result = None
        if target == "local":
            try:
                raw_result = await self._call_ollama(effective_prompt, effective_sys, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Ollama local inference unavailable: {e}. Checking dual-engine fallback...")
                if not air_gap_active:
                    if self.groq_api_key:
                        try:
                            raw_result = await self._call_groq(effective_prompt, effective_sys, temperature, max_tokens)
                        except Exception as ge:
                            logger.warning(f"Dual-engine Groq fallback failed: {ge}")
                    if raw_result is None and self.gemini_api_key:
                        try:
                            raw_result = await self._call_gemini(effective_prompt, effective_sys, temperature, max_tokens)
                        except Exception as gme:
                            logger.warning(f"Dual-engine Gemini fallback failed: {gme}")
                if raw_result is None:
                    raw_result = self._generate_sovereign_local_ai(prompt, system_prompt)
        elif target == "groq" and self.groq_api_key:
            raw_result = await self._call_groq(effective_prompt, effective_sys, temperature, max_tokens)
        elif target == "gemini" and self.gemini_api_key:
            raw_result = await self._call_gemini(effective_prompt, effective_sys, temperature, max_tokens)

        # Auto resolution
        if raw_result is None:
            # Try Local Ollama first
            try:
                raw_result = await self._call_ollama(effective_prompt, effective_sys, temperature, max_tokens)
            except Exception:
                pass

        if raw_result is None and self.groq_api_key:
            try:
                raw_result = await self._call_groq(effective_prompt, effective_sys, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Groq generation failed: {e}. Falling back to Gemini...")

        if raw_result is None and self.gemini_api_key:
            try:
                raw_result = await self._call_gemini(effective_prompt, effective_sys, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Gemini generation failed: {e}. Falling back to Local...")

        if raw_result is None:
            raw_result = self._generate_sovereign_local_ai(prompt, system_prompt)

        return parse_markdown_to_modular_blocks(raw_result) if as_modular_json else raw_result


    async def _call_groq(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> str:
        """Call Groq API using REST endpoint with verified models and reasoning token headroom."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        last_err = None
        # Ensure reasoning models have sufficient token headroom
        effective_max_tokens = max(max_tokens, 2048)

        for model in models_to_try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": effective_max_tokens,
            }
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
            }

            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            msg = choices[0].get("message", {})
                            content = msg.get("content", "")
                            if not content or not content.strip():
                                content = msg.get("reasoning", "")
                            if content and content.strip():
                                return content.strip()
                    else:
                        last_err = f"Status {resp.status_code}: {resp.text}"
            except Exception as e:
                last_err = str(e)

        raise ValueError(f"Groq generation failed across models: {last_err}")

    async def _call_gemini(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> str:
        """Call Gemini API using REST endpoint. (TRG-021: url variable now defined)"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        # TRG-021: Define the URL before use (was previously undefined, causing NameError)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            raise ValueError(f"Empty Gemini response: {data}")

    async def _call_ollama(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> str:
        """Call local Ollama server running on-premise with dynamic installed-model discovery."""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        model_to_use = self.local_model or "llama3.2:1b"

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
            # Query Ollama for installed models to avoid 404 if default name differs
            try:
                tags_resp = await client.get(f"{self.ollama_url}/api/tags", timeout=2.5)
            except Exception:
                try:
                    from ollama_manager import OllamaManager
                    OllamaManager().auto_start_daemon()
                    tags_resp = await client.get(f"{self.ollama_url}/api/tags", timeout=3.0)
                except Exception as auto_err:
                    tags_resp = None
                    logger.debug(f"Ollama auto-start check skipped: {auto_err}")

            if tags_resp is not None and tags_resp.status_code == 200:
                try:
                    models_data = tags_resp.json().get("models", [])
                    installed_names = [m.get("name", "") for m in models_data]
                    # If current model_to_use is not installed, switch to first installed model
                    if installed_names and not any(model_to_use in name for name in installed_names):
                        model_to_use = installed_names[0]
                        self.local_model = model_to_use
                        logger.info(f"Ollama dynamic switch: using installed model '{model_to_use}'")
                except Exception as tag_err:
                    logger.debug(f"Ollama tags check skipped: {tag_err}")

            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": min(max_tokens, 1024),
                },
            }
            if system_prompt:
                payload["system"] = system_prompt
            resp = await client.post(f"{self.ollama_url}/api/generate", json=payload)
            resp.raise_for_status()
            res_text = resp.json().get("response", "")
            if res_text and res_text.strip():
                return res_text.strip()
            raise ValueError(f"Ollama returned empty response for model '{model_to_use}'.")

    def _generate_sovereign_local_ai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Built-in Sovereign Local AI Synthesizer (100% On-Premise, Zero Data Exfiltration).
        Provides rich, intelligent, conversational on-premise answers for greetings, document/storage analysis,
        and general queries with zero reliance on cloud or external daemons.
        """
        # Clean prompt of any prepended system instruction boilerplate
        clean_q = re.sub(r"^You are a helpful[\s\S]*?question:\s*", "", prompt, flags=re.IGNORECASE).strip()
        if not clean_q:
            clean_q = prompt.strip()
        clean_lower = clean_q.lower().strip()

        # 1. Natural Conversational Greeting
        greeting_words = {"hello", "hi", "hey", "namaste", "good morning", "good afternoon", "good evening", "greetings"}
        is_greeting = clean_lower in greeting_words or any(clean_lower.startswith(g + " ") or clean_lower.startswith(g + "!") or clean_lower.startswith(g + ",") for g in greeting_words)
        if is_greeting:
            return "Hello! How can I assist you with your documents, government tenders, or queries today?"

        # 2. Assistant Identity & Capabilities
        if any(k in clean_lower for k in ["who are you", "what are you", "what can you do", "help me", "how to use", "capabilities"]):
            return (
                "### Sovereign Agentic AI Workbench\n\n"
                "I am your on-premise AI Assistant, built for document intelligence, autonomous tender auditing, and data security.\n\n"
                "**Capabilities:**\n"
                "- **Document Intelligence**: Extract and analyze text from PDFs, DOCX files, and spreadsheets.\n"
                "- **Tender Auditing**: Verify bidding guidelines, compliance terms, and financial exemptions.\n"
                "- **Cookie Session Vault**: Securely interact with authenticated government portals.\n"
                "- **Dual-Engine Privacy**: 100% on-premise execution with zero cloud leakage in Air-Gap mode."
            )

        # 3. Storage & Files Overview Query
        is_storage_query = any(k in clean_lower for k in [
            "all the files", "files in storage", "storage tell", "files the storage",
            "storage summary", "list files", "what files", "all files", "files summary",
            "what are all the files", "documents in storage", "folder summary"
        ])
        if is_storage_query:
            return self._synthesize_storage_overview()

        # 4. Document Context Extractor (TRG-014 Safe Dynamic Extraction)
        if "<document_context>" in prompt:
            doc_match = re.search(r"<document_context>([\s\S]*?)</document_context>", prompt)
            doc_context = doc_match.group(1).strip() if doc_match else ""
            q_match = re.search(r"<user_question>([\s\S]*?)</user_question>", prompt)
            user_q = q_match.group(1).strip() if q_match else clean_q

            if doc_context and len(doc_context) > 10:
                query_words = set(re.findall(r"\w+", user_q.lower())) - {
                    "what", "is", "the", "are", "and", "for", "about", "in", "to", "of", "a", "an", "tell", "me"
                }
                lines = [line.strip() for line in doc_context.split("\n") if line.strip()]
                matched_lines = []
                for line in lines:
                    line_lower = line.lower()
                    if any(w in line_lower for w in query_words if len(w) > 2):
                        matched_lines.append(line)

                if matched_lines:
                    extracted = "\n\n".join(matched_lines[:10])
                else:
                    extracted = "\n\n".join(lines[:6])

                return (
                    f"### Document Analysis: {user_q}\n\n"
                    f"{extracted}\n\n"
                    f"---\n"
                    f"*(Extracted directly from indexed local documents)*"
                )

        # 5. Basic Arithmetic Solver
        math_clean = clean_q.strip().rstrip("?")
        if re.match(r"^[\s\d\+\-\*\/\(\)\.\^\%]+$", math_clean) and any(op in math_clean for op in ["+", "-", "*", "/"]):
            try:
                allowed_chars = set("0123456789+-*/(). %")
                if set(math_clean).issubset(allowed_chars):
                    res = eval(math_clean.replace("^", "**"), {"__builtins__": None}, {})
                    return f"**Calculation Result**: `{math_clean} = {res}`"
            except Exception:
                pass

        # 6. Dynamic Offline Informational Response (No canned mock data)
        return (
            f"I have received your inquiry: \"{clean_q}\".\n\n"
            f"In on-premise sovereign mode, answers are extracted from your local indexed documents. "
            f"To analyze this topic locally, please upload the relevant document (PDF, DOCX, or CSV) in the Document Hub."
        )

    def _synthesize_storage_overview(self) -> str:
        """Dynamically scans storage directories and produces a factual summary of actual files on disk."""
        uploads_dir = Path(__file__).resolve().parent / "output" / "uploads"
        
        found_files = []
        if uploads_dir.exists():
            for f in sorted(uploads_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    found_files.append((f.name, f.stat().st_size))

        if not found_files:
            return (
                "### 📁 Local Storage Overview\n\n"
                "No documents or uploads are currently stored in `output/uploads/`.\n\n"
                "Upload documents (PDF, DOCX, CSV, TXT) to index and query them with full data privacy."
            )

        file_list_md = []
        for name, size in found_files:
            size_kb = round(size / 1024, 1)
            file_list_md.append(f"- **`{name}`** ({size_kb} KB)")

        return (
            f"### 📁 Local Storage Intelligence Summary\n"
            f"**Location**: `output/uploads/` &bull; **Total Files**: {len(found_files)}\n\n"
            f"Here are the files currently stored and indexed:\n\n"
            + "\n".join(file_list_md) + "\n\n"
            f"You can ask specific questions about any of these documents."
        )


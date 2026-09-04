"""
Unit & Integration Tests for LocalRAGEngine with memory.md, SHA-256 caching,
and Confidentiality Guard (SIH PSC26117 Sovereign Workbench)
"""
import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path

from local_rag_engine import LocalRAGEngine, check_confidentiality_and_motw, compress_data, decompress_data


class TestLocalRAGEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="sovereign_test_repo_"))
        # Create mock project files
        (self.test_dir / "main.py").write_text("def hello():\n    return 'Namaste Sovereign AI'\n", encoding="utf-8")
        (self.test_dir / "config.json").write_text('{"app": "TenderAgent", "version": "1.0"}', encoding="utf-8")
        (self.test_dir / "notes.txt").write_text("Government tender requirements and ISO compliance.", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_confidentiality_redaction(self):
        """Ensure sensitive credentials (.env, AWS keys, private RSA keys) are safely redacted."""
        sensitive_text = """
        AWS_ACCESS_KEY_ID = AKIAIOSFODNN7EXAMPLE
        AWS_SECRET_ACCESS_KEY = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
        GEMINI_API_KEY = "AIzaSyDUMMY_KEY_FOR_TESTING_PURPOSES_ONLY_123"
        Regular public code line here
        """
        result = check_confidentiality_and_motw(sensitive_text, ".env")
        self.assertTrue(result["has_secrets"])
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", result["sanitized_content"])
        self.assertIn("[REDACTED_SECRET", result["sanitized_content"])
        self.assertIn("Regular public code line here", result["sanitized_content"])

    def test_02_compression_roundtrip(self):
        """Ensure zlib compression reduces size and decompresses losslessly."""
        raw_text = "Sovereign AI On-Premise Government Workbench " * 200
        compressed = compress_data(raw_text)
        self.assertLess(len(compressed), len(raw_text.encode("utf-8")))
        decompressed = decompress_data(compressed)
        self.assertEqual(decompressed, raw_text)

    def test_03_incremental_memory_indexing(self):
        """Ensure memory.md is generated and subsequent scans skip unchanged files (O(k))."""
        rag = LocalRAGEngine(workspace_dir=self.test_dir)
        
        # First scan: all 3 files are newly indexed
        res1 = asyncio.run(rag.analyze_directory(str(self.test_dir)))
        self.assertEqual(res1["total_files_scanned"], 3)
        self.assertEqual(res1["files_indexed_new"], 3)
        self.assertEqual(res1["files_reused_from_cache"], 0)

        # Check that memory.md was written
        memory_file = self.test_dir / "memory.md"
        self.assertTrue(memory_file.exists())
        memory_content = memory_file.read_text(encoding="utf-8")
        self.assertIn("main.py", memory_content)
        self.assertIn("SHA-256", memory_content)

        # Second scan: nothing changed -> all 3 files reused from cache
        rag2 = LocalRAGEngine(workspace_dir=self.test_dir)
        res2 = asyncio.run(rag2.analyze_directory(str(self.test_dir)))
        self.assertEqual(res2["total_files_scanned"], 3)
        self.assertEqual(res2["files_indexed_new"], 0)
        self.assertEqual(res2["files_reused_from_cache"], 3)

        # Modify one file and re-scan: exactly 1 file indexed new, 2 reused
        (self.test_dir / "main.py").write_text("def hello():\n    return 'Updated Namaste'\n", encoding="utf-8")
        rag3 = LocalRAGEngine(workspace_dir=self.test_dir)
        res3 = asyncio.run(rag3.analyze_directory(str(self.test_dir)))
        self.assertEqual(res3["files_indexed_new"], 1)
        self.assertEqual(res3["files_reused_from_cache"], 2)

    def test_04_query_knowledge(self):
        """Ensure natural language queries return relevant content from indexed files."""
        rag = LocalRAGEngine(workspace_dir=self.test_dir)
        asyncio.run(rag.analyze_directory(str(self.test_dir)))
        answer = asyncio.run(rag.query_knowledge("What is the ISO compliance about?"))
        self.assertIn("government tender", answer.lower())
        self.assertIn("notes.txt", answer)


if __name__ == "__main__":
    unittest.main()

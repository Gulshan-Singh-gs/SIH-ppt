"""
Unit tests for DocumentProcessor (CSV, DOCX, Image OCR)
SIH PSC26117 — Sovereign AI Workbench
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from document_processor import DocumentProcessor, preprocess_image_for_ocr


class TestDocumentProcessor(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_csv_processing(self):
        """Verify CSV parsing, header detection, and budget calculation."""
        csv_file = self.test_dir / "tenders.csv"
        csv_file.write_text(
            "Tender_ID,Title,Department,Estimated_INR\n"
            "GeM/01,Edge Servers,MeitY,15000000\n"
            "GeM/02,Security Appliance,MHA,28500000\n"
            "GeM/03,Maintenance,DARPG,4800000\n",
            encoding="utf-8"
        )
        res = DocumentProcessor.process_csv(csv_file)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["total_records"], 3)
        self.assertIn("Estimated_INR", res["numeric_stats"])
        self.assertEqual(res["numeric_stats"]["Estimated_INR"]["sum"], 48300000.0)

    def test_02_image_preprocessing(self):
        """Verify image enhancement and binarization for OCR accuracy."""
        img = Image.new("RGB", (100, 100), color="white")
        processed = preprocess_image_for_ocr(img)
        self.assertEqual(processed.mode, "L")
        self.assertEqual(processed.size, (100, 100))

    def test_03_file_dispatcher(self):
        """Verify parse_file correctly delegates CSV and text files."""
        csv_file = self.test_dir / "rates.csv"
        csv_file.write_text("Item,Rate\nLaptop,50000\n", encoding="utf-8")
        res = DocumentProcessor.parse_file(csv_file)
        self.assertEqual(res["type"], "tabular")


if __name__ == "__main__":
    unittest.main()

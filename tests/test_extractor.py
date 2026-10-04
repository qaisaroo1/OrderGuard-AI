import unittest
import shutil
from unittest.mock import patch
from pathlib import Path

import pymupdf
import pytesseract

from core.extractor import (
    DocumentExtractor,
    ExtractionError,
    _mask_arabic_blocks,
    _strip_repeated,
)


def make_pdf(text=None, *, encrypted=False):
    document = pymupdf.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    if encrypted:
        content = document.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="owner-password",
            user_pw="user-password",
        )
    else:
        content = document.tobytes()
    document.close()
    return content


class DocumentExtractorTests(unittest.TestCase):
    def test_extracts_direct_text_with_page_boundaries(self):
        result = DocumentExtractor.extract_from_pdf(
            make_pdf("Court order with sufficient text for direct extraction.")
        )

        self.assertEqual(result["total_pages"], 1)
        self.assertEqual(result["pages"][0]["method"], "direct")
        self.assertIn("Court order", result["full_text_with_pages"])
        self.assertIn("[PAGE 1 START]", result["full_text_with_pages"])
        self.assertIn("[PAGE 1 END]", result["full_text_with_pages"])

    @patch("core.extractor._ocr_page", return_value=("Recognized order text", 92.0, 0))
    def test_uses_ocr_for_scanned_page(self, mock_ocr):
        result = DocumentExtractor.extract_from_pdf(make_pdf())

        mock_ocr.assert_called_once()
        self.assertEqual(result["pages"][0]["method"], "ocr")
        self.assertEqual(result["pages"][0]["ocr_confidence"], 92.0)
        self.assertIn("Recognized order text", result["full_text_with_pages"])
        self.assertTrue(any("OCR used" in warning for warning in result["warnings"]))

    @patch(
        "core.extractor._ocr_page",
        return_value=("Recognized order text", 42.0, 1),
    )
    def test_reports_low_confidence_without_noisy_dropped_line_notice(self, _mock_ocr):
        result = DocumentExtractor.extract_from_pdf(make_pdf())

        self.assertTrue(any("low OCR confidence" in warning for warning in result["warnings"]))
        self.assertFalse(any("dropped" in warning for warning in result["warnings"]))

    @patch(
        "core.extractor._ocr_page",
        side_effect=pytesseract.TesseractNotFoundError(),
    )
    def test_reports_missing_tesseract_and_empty_page(self, _mock_ocr):
        result = DocumentExtractor.extract_from_pdf(make_pdf())

        self.assertTrue(any("TESSERACT_CMD" in warning for warning in result["warnings"]))
        self.assertTrue(any("very little text" in warning for warning in result["warnings"]))

    def test_rejects_invalid_pdf(self):
        with self.assertRaisesRegex(ExtractionError, "Could not open"):
            DocumentExtractor.extract_from_pdf(b"not a PDF")

    def test_rejects_password_protected_pdf(self):
        with self.assertRaisesRegex(ExtractionError, "password-protected"):
            DocumentExtractor.extract_from_pdf(make_pdf(encrypted=True))

    def test_preserves_case_specific_headers(self):
        cleaned, removed = _strip_repeated([
            "Case No. R.F.A. 58/2025 1\nFirst page text",
            "Case No. R.F.A. 58/2025 2\nSecond page text",
        ])

        self.assertIn("Case No. R.F.A. 58/2025 1", cleaned[0])
        self.assertIn("Case No. R.F.A. 58/2025 2", cleaned[1])
        self.assertEqual(removed, [])

    def test_masks_unreadable_urdu_and_keeps_dates(self):
        text = "یہ عدالت کا حکم ہے 16.04.2025\nEnglish line"

        result = _mask_arabic_blocks(text)

        self.assertIn("[Urdu text unreadable", result)
        self.assertIn("16.04.2025", result)
        self.assertIn("English line", result)


class SuppliedJudgmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = Path(__file__).resolve().parents[1].parent / "samples"

    def test_preserves_page_specific_docket_headers(self):
        result = DocumentExtractor.extract_from_pdf(
            (self.samples / "case_3.pdf").read_bytes()
        )

        page_two = " ".join(result["pages"][1]["text"].split())
        page_eight = " ".join(result["pages"][7]["text"].split())
        self.assertIn("R.F.A. No.58 of 2025/BWP 2", page_two)
        self.assertIn("R.F.A. No.58 of 2025/BWP 8", page_eight)

    def test_flags_urdu_passages_for_manual_review(self):
        result = DocumentExtractor.extract_from_pdf(
            (self.samples / "case_6.pdf").read_bytes()
        )

        review_pages = [
            page["page"] for page in result["pages"]
            if page["raw_text"] or page["urdu_ocr_text"]
        ]
        self.assertEqual(review_pages, [5, 11])
        self.assertTrue(
            any("Urdu/Arabic-script text masked" in warning for warning in result["warnings"])
        )

    @unittest.skipUnless(
        shutil.which("tesseract")
        or Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe").is_file(),
        "Tesseract is not installed",
    )
    def test_extracts_scanned_judgment_with_ocr(self):
        result = DocumentExtractor.extract_from_pdf(
            (self.samples / "case_5.pdf").read_bytes()
        )

        self.assertEqual(result["total_pages"], 4)
        self.assertTrue(all(page["method"] == "ocr" for page in result["pages"]))
        self.assertTrue(
            any("OCR used on pages [1, 2, 3, 4]" in warning for warning in result["warnings"])
        )
        self.assertFalse(any("dropped" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()

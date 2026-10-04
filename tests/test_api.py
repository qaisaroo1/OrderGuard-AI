import io
import unittest
from unittest.mock import patch

import pymupdf
from fastapi import HTTPException, UploadFile

import api


def make_pdf(text=None):
    document = pymupdf.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def make_upload(filename, content):
    return UploadFile(filename=filename, file=io.BytesIO(content))


class ExtractEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_pdf_returns_page_metadata_and_preserves_agent_schema(self):
        upload = make_upload(
            "order.pdf",
            make_pdf("A fictional court order containing enough text for extraction."),
        )
        expected = api.pipeline._get_mock_action_map()

        with patch("api.LegalExtractionPipeline") as pipeline_class:
            pipeline_class.return_value.analyze_order.return_value = expected
            result = await api.extract_court_order(
                file=upload,
                model_name="gemini-3.5-flash-lite",
                use_mock_fallback=False,
            )

        pipeline_class.assert_called_once_with(model_name="gemini-3.5-flash-lite")
        analyze = pipeline_class.return_value.analyze_order
        analyze.assert_called_once()
        self.assertIn("[PAGE 1 START]", analyze.call_args.args[0])
        self.assertEqual(result.extraction_pages[0].page_number, 1)
        self.assertEqual(result.extraction_pages[0].method, "direct")
        self.assertEqual(result.total_obligations, len(result.actions))
        self.assertEqual(result.agent_traces, expected.agent_traces)

    @patch(
        "core.extractor._ocr_page",
        return_value=("OCR recognized enough fictional order text", 91.0, 0),
    )
    async def test_scanned_pdf_uses_ocr_and_returns_warning(self, _mock_ocr):
        upload = make_upload("scan.pdf", make_pdf())
        expected = api.pipeline._get_mock_action_map()

        with patch("api.LegalExtractionPipeline") as pipeline_class:
            pipeline_class.return_value.analyze_order.return_value = expected
            result = await api.extract_court_order(file=upload)

        self.assertEqual(result.extraction_pages[0].method, "ocr")
        self.assertEqual(result.extraction_pages[0].ocr_confidence, 91.0)
        self.assertTrue(any("OCR used" in warning for warning in result.extraction_warnings))

    async def test_text_upload_is_passed_to_analysis(self):
        text = "A fictional order supplied as a UTF-8 text document."
        upload = make_upload("order.txt", text.encode("utf-8"))

        with patch("api.LegalExtractionPipeline") as pipeline_class:
            pipeline_class.return_value.analyze_order.return_value = (
                api.pipeline._get_mock_action_map()
            )
            await api.extract_court_order(file=upload)

        analyze = pipeline_class.return_value.analyze_order
        self.assertEqual(analyze.call_args.args[0], text)

    async def test_rejects_unsupported_file_type(self):
        with self.assertRaises(HTTPException) as raised:
            await api.extract_court_order(
                file=make_upload("order.docx", b"not a supported document")
            )

        self.assertEqual(raised.exception.status_code, 400)

    async def test_rejects_upload_over_limit(self):
        upload = make_upload("order.pdf", b"0123456789")
        with patch.object(api, "MAX_UPLOAD_BYTES", 4):
            with self.assertRaises(HTTPException) as raised:
                await api.extract_court_order(file=upload)

        self.assertEqual(raised.exception.status_code, 413)

    async def test_rejects_invalid_pdf(self):
        with self.assertRaises(HTTPException) as raised:
            await api.extract_court_order(file=make_upload("order.pdf", b"not a PDF"))

        self.assertEqual(raised.exception.status_code, 422)

    @patch("core.extractor._ocr_page", return_value=("", 0.0, 0))
    async def test_rejects_pdf_with_no_readable_text(self, _mock_ocr):
        with self.assertRaises(HTTPException) as raised:
            await api.extract_court_order(file=make_upload("blank.pdf", make_pdf()))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("No readable text", raised.exception.detail)

    async def test_empty_ai_extraction_returns_review_warning_and_pdf_metadata(self):
        upload = make_upload(
            "order.pdf",
            make_pdf("The respondent shall file a reply within fourteen days."),
        )
        with patch("api.LegalExtractionPipeline") as pipeline_class:
            pipeline_class.return_value.analyze_order.return_value = (
                api.pipeline._get_mock_action_map().model_copy(
                    update={"actions": [], "total_obligations": 0}
                )
            )
            result = await api.extract_court_order(file=upload)

        self.assertEqual(result.actions, [])
        self.assertEqual(result.total_obligations, 0)
        self.assertTrue(any("No obligations were created" in warning for warning in result.analysis_warnings))
        self.assertEqual(result.extraction_pages[0].method, "direct")
        self.assertIn(
            "The respondent shall file a reply",
            result.extraction_pages[0].text_preview,
        )


if __name__ == "__main__":
    unittest.main()

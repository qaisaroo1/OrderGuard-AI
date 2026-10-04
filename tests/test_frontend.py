import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import api
from core.extractor import DocumentExtractor
from core.schemas import CaseMetadata, LegalActionResponse


class _FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class StreamlitAnalysisFlowTests(unittest.TestCase):
    def test_analyze_click_submits_text_and_displays_empty_result_warning(self):
        payload = api.pipeline._get_mock_action_map().model_dump()
        payload.update({
            "actions": [],
            "total_obligations": 0,
            "critical_risks_count": 0,
            "agent_traces": [],
            "analysis_warnings": [
                "No actions were detected. Review the order manually."
            ],
            "extraction_warnings": [],
            "extraction_pages": [{
                "page_number": 1,
                "method": "direct",
                "char_count": 68,
                "ocr_confidence": None,
                "text_preview": "Fictional order: the respondent shall file a reply within 14 days.",
                "raw_text": None,
                "urdu_ocr_text": None,
            }],
        })
        app_path = Path(__file__).resolve().parents[1] / "app.py"

        with patch("requests.post", return_value=_FakeResponse(payload)) as post:
            app = AppTest.from_file(str(app_path), default_timeout=60).run()
            app.text_area[0].set_value(
                "Fictional order: the respondent shall file a reply within 14 days."
            ).run()
            analyze_button = next(
                button for button in app.button
                if "Analyze Judgment" in button.label
            )
            analyze_button.click().run()

        self.assertEqual(post.call_count, 1)
        self.assertEqual(
            post.call_args.kwargs["data"]["raw_text"],
            "Fictional order: the respondent shall file a reply within 14 days.",
        )
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual(app.session_state["action_map"].actions, [])
        self.assertTrue(
            any("No actions were detected" in item.value for item in app.warning)
        )
        self.assertTrue(
            any("Fictional order" in item.value for item in app.text_area)
        )
        self.assertTrue(
            any(
                "Analysis completed. This judgment does not order a future task"
                in item.value
                for item in app.info
            )
        )
        self.assertFalse(
            any("No action items match the selected filters" in item.value for item in app.info)
        )
        self.assertTrue(
            any("Extracted page text is expanded above" in item.value for item in app.caption)
        )
        self.assertTrue(
            any("DECISION IN THIS JUDGMENT" in item.value for item in app.markdown)
        )
        self.assertFalse(any("0 action(s) shown" in item.value for item in app.caption))
        self.assertFalse(any("All Parties" == item.value for item in app.selectbox))
        self.assertFalse(
            any("Future Obligations" in item.value for item in app.markdown)
        )
        self.assertFalse(
            any("Tracked Deadlines" in item.value for item in app.markdown)
        )

    def test_scanned_pdf_upload_shows_outcome_and_ocr_text_without_ai(self):
        sample_path = Path(__file__).resolve().parents[2] / "samples" / "case_5.pdf"
        if not sample_path.is_file():
            self.skipTest("case_5.pdf not present in repository")
        pdf_bytes = sample_path.read_bytes()
        extracted = DocumentExtractor.extract_from_pdf(pdf_bytes)
        pages = [
            {
                "page_number": page["page"],
                "method": page["method"],
                "char_count": page["char_count"],
                "ocr_confidence": page["ocr_confidence"],
                "text_preview": page["text"][:1000],
                "raw_text": page["raw_text"],
                "urdu_ocr_text": page["urdu_ocr_text"],
            }
            for page in extracted["pages"]
        ]
        response = LegalActionResponse(
            metadata=CaseMetadata(
                case_title="Constitution Petition No. D-5714 of 2024",
                case_number="Constitution Petition No. D-5714 of 2024",
                court_name="High Court of Sindh, at Karachi",
                judge_names="Mr. Justice Omar Sial, Mr. Justice Muhammad Hasan (Akber)",
                order_date="05.05.2025",
                brief_summary=(
                    "The petition was dismissed, along with pending applications; "
                    "the order states no future party deadline."
                ),
            ),
            actions=[],
            total_obligations=0,
            critical_risks_count=0,
            agent_traces=[],
            analysis_warnings=[
                "No future obligations were identified; verify the order manually."
            ],
            extraction_warnings=extracted["warnings"],
            extraction_pages=pages,
        )
        app_path = Path(__file__).resolve().parents[1] / "app.py"

        with patch("requests.post", return_value=_FakeResponse(response.model_dump())) as post:
            app = AppTest.from_file(str(app_path), default_timeout=90).run()
            app.file_uploader[0].set_value(
                ("case_5.pdf", pdf_bytes, "application/pdf")
            ).run()
            analyze_button = next(
                button for button in app.button
                if "Analyze Judgment" in button.label
            )
            analyze_button.click().run()

        self.assertEqual(post.call_count, 1)
        self.assertEqual(
            post.call_args.kwargs["files"]["file"][0], "case_5.pdf"
        )
        self.assertEqual(
            post.call_args.kwargs["files"]["file"][1], pdf_bytes
        )
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual(app.session_state["action_map"].actions, [])
        self.assertTrue(
            any("dismissed, along with pending applications" in item.value for item in app.markdown)
        )
        self.assertTrue(
            any("petition is therefore, dismissed" in item.value.casefold() for item in app.text_area)
        )


if __name__ == "__main__":
    unittest.main()

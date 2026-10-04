import unittest
from unittest.mock import Mock, patch

import requests

import api
from core.api_client import submit_analysis
from core.schemas import LegalActionResponse


class ApiClientTests(unittest.TestCase):
    def setUp(self):
        self.valid_response = LegalActionResponse(
            **{
                **api.pipeline._get_mock_action_map().model_dump(),
                "extraction_warnings": [],
                "extraction_pages": [],
            }
        )
        self.http_response = Mock(
            ok=True,
            status_code=200,
        )
        self.http_response.json.return_value = self.valid_response.model_dump()

    @patch("core.api_client.requests.post")
    def test_posts_pdf_to_fastapi_and_validates_response(self, post):
        post.return_value = self.http_response

        result = submit_analysis(
            file_name="judgment.pdf",
            file_bytes=b"pdf-content",
            model_name="gemini-3.5-flash-lite",
            use_mock_fallback=False,
        )

        self.assertIsInstance(result, LegalActionResponse)
        self.assertEqual(result.total_obligations, self.valid_response.total_obligations)
        kwargs = post.call_args.kwargs
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:8000/api/extract")
        self.assertEqual(kwargs["files"]["file"], (
            "judgment.pdf",
            b"pdf-content",
            "application/pdf",
        ))
        self.assertEqual(kwargs["data"]["model_name"], "gemini-3.5-flash-lite")
        self.assertEqual(kwargs["data"]["use_mock_fallback"], "false")
        self.assertEqual(kwargs["timeout"], (10, 600))

    @patch("core.api_client.requests.post")
    def test_posts_pasted_text_to_fastapi(self, post):
        post.return_value = self.http_response

        submit_analysis(
            raw_text="Fictional order text",
            model_name="gemini-3.5-flash-lite",
            use_mock_fallback=True,
        )

        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["data"]["raw_text"], "Fictional order text")
        self.assertIsNone(kwargs["files"])
        self.assertEqual(kwargs["data"]["use_mock_fallback"], "true")

    @patch("core.api_client.requests.post", side_effect=requests.ConnectionError("offline"))
    def test_reports_when_backend_is_not_running(self, _post):
        with self.assertRaisesRegex(RuntimeError, "Start the FastAPI backend"):
            submit_analysis(
                raw_text="Fictional text",
                model_name="gemini-3.5-flash-lite",
                use_mock_fallback=False,
            )

    @patch("core.api_client.requests.post")
    def test_surfaces_api_error_detail(self, post):
        response = Mock(ok=False, status_code=500, text="server error")
        response.json.return_value = {"detail": "Gemini request failed"}
        post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "Gemini request failed"):
            submit_analysis(
                raw_text="Fictional text",
                model_name="gemini-3.5-flash-lite",
                use_mock_fallback=False,
            )

    @patch("core.api_client.requests.post")
    def test_rejects_invalid_api_response_schema(self, post):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {"not": "a LegalActionMap"}
        post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "invalid Legal Action Map"):
            submit_analysis(
                raw_text="Fictional text",
                model_name="gemini-3.5-flash-lite",
                use_mock_fallback=False,
            )

    def test_rejects_missing_input_before_http_request(self):
        with patch("core.api_client.requests.post") as post:
            with self.assertRaisesRegex(ValueError, "Upload a PDF/TXT"):
                submit_analysis(
                    model_name="gemini-3.5-flash-lite",
                    use_mock_fallback=False,
                )
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()

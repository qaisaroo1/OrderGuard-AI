"""HTTP client used by the Streamlit frontend to call the local FastAPI service."""
import os
from typing import Optional

import requests
from pydantic import ValidationError

from core.schemas import LegalActionResponse

API_BASE_URL = os.getenv("ORDERGUARD_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_TIMEOUT = (10, 600)


def submit_analysis(
    *,
    model_name: str,
    use_mock_fallback: bool,
    file_name: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    raw_text: Optional[str] = None,
) -> LegalActionResponse:
    """Submit a document to FastAPI and validate the structured response."""
    data = {
        "model_name": model_name,
        "use_mock_fallback": str(use_mock_fallback).lower(),
    }
    files = None
    if file_name is not None and file_bytes is not None:
        content_type = (
            "application/pdf"
            if file_name.lower().endswith(".pdf")
            else "text/plain"
        )
        files = {"file": (file_name, file_bytes, content_type)}
    elif raw_text and raw_text.strip():
        data["raw_text"] = raw_text
    else:
        raise ValueError("Upload a PDF/TXT file or paste judgment text first.")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/extract",
            data=data,
            files=files,
            timeout=API_TIMEOUT,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not connect to the OrderGuard API at {API_BASE_URL}. "
            "Start the FastAPI backend and try again."
        ) from error

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"API returned HTTP {response.status_code}: {detail}")

    try:
        return LegalActionResponse.model_validate(response.json())
    except (ValueError, ValidationError) as error:
        raise RuntimeError("The API returned an invalid Legal Action Map response.") from error

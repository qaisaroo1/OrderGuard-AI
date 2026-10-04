# OrderGuard AI ⚖️
### Autonomous Legal Action Mapping & Execution Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red.svg)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://deepmind.google/technologies/gemini/)

Court orders and judgments are notoriously long, dense, and complex. Missing a single hidden deadline or conditional obligation can lead to legal penalties, contempt of court, or case dismissal. 

**OrderGuard AI** transforms passive legal document reading into an active, execution-ready workflow. By combining Generative AI (Google Gemini), structured Pydantic schemas, and citation grounding, it automatically parses court judgments to generate an interactive **Legal Action Map** tracking who must do what, by when, under what conditions, and with what consequences.

---

## 🚀 Key Features

* **Agentic Legal Extraction:** Isolates obligations, absolute/relative deadlines, conditional contingencies, and required evidence from unstructured legal text.
* **Risk & Consequence Mapping:** Explicitly details the legal fallout or penalties (e.g. *Contempt of Court*, *Vacation of Stay*, *Attachment of Assets*) if an action is missed.
* **Anti-Hallucination Citation Grounding:** Every extracted task references the exact page number and verbatim excerpt from the judgment.
* **Perspective Switcher (Multi-Party View):** Filter tasks by party (e.g., Petitioner Counsel vs. Respondent Defense Counsel) to spot obligations or enforce opposing counsel deadlines.
* **Smart Relative Date Resolution:** Automatically translates relative clauses (*"within 14 days of receipt"*) into concrete calendar actions based on service date.
* **Developer Contract & Export:** 1-Click download of structured JSON (for frontend developers) and `.ics` Calendar sync.

---

## 🏗️ Architecture

```
orderguard-ai/
│
├── core/
│   ├── schemas.py          # Pydantic data contract (LegalActionMap, ActionItem, Citations)
│   ├── extractor.py        # PDF text extractor with page boundary tracking
│   └── pipeline.py         # Google Gemini extraction engine with mock fallback
│
├── samples/
│   ├── generate_sample_order.py   # Realistic High Court sample order generator
│   ├── make_pdf.py                # Standalone PDF generator
│   ├── sample_court_order.txt     # Test judgment
│   └── sample_court_order.pdf     # Test PDF
│
├── app.py                  # Full-featured Streamlit interactive dashboard
├── api.py                  # FastAPI REST endpoints for frontend integration
├── requirements.txt        # Project dependencies
└── .env.example            # Environment variables template
```

---

## ⚡ Quickstart

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-repo/orderguard-ai.git
cd orderguard-ai
pip install -r requirements.txt
```

### 2. Install OCR Engine (for scanned PDFs)

PyMuPDF extracts text directly from digital PDFs. Pages with fewer than 50
extractable characters are rendered and processed with Tesseract OCR. Install
the Tesseract application separately from the Python packages, including the
`eng` language data. For Urdu OCR attempts, also install the `urd` language
data. If Tesseract is not on `PATH`, set `TESSERACT_CMD` to its executable path.

On Windows, a standard installation in `C:\Program Files\Tesseract-OCR` is
detected automatically. OCR confidence and Urdu text are not guaranteed to be
correct; the dashboard and API provide extraction warnings and preserve Urdu
text candidates for manual checking against the original PDF.

### 3. Configure Environment
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
Demo fallback is opt-in in the dashboard. The API defaults to real extraction
and reports errors if Gemini is unavailable; clients may explicitly set
`use_mock_fallback=true` to request demo data.

### 4. Start the FastAPI backend

In the first terminal:

```powershell
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

The backend reads `GEMINI_API_KEY` from `.env` and runs PDF extraction/OCR
before sending extracted text to Gemini. Set `ORDERGUARD_API_URL` only if the
backend is listening somewhere other than `http://127.0.0.1:8000`.

### 5. Run the Streamlit Dashboard

In a second terminal, from the project root:

```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

The dashboard submits uploads and pasted text to the FastAPI backend. Gemini is
called by the backend using the configured key. Keep the backend running while
using the dashboard. API documentation is at `http://127.0.0.1:8000/docs`.

### 6. Run extraction, API, and frontend-client tests

```bash
python -m unittest discover -s tests -v
```

The tests cover text extraction, scanned-page OCR, Urdu review metadata, API
upload validation, and the supplied judgment samples. Gemini analysis is
mocked in API tests; Tesseract-dependent sample tests are skipped if Tesseract
is unavailable.

---

## 📡 API Contract (For Frontend / Team Integration)

### `POST /api/extract`
Uploads a court order PDF and returns the validated `LegalActionMap`:

The response also includes `extraction_warnings` and `extraction_pages`.
These report OCR/manual-review issues and per-page OCR confidence. When Urdu
text is detected, `extraction_pages` includes the original text and a separate
unverified `urdu_ocr_text` candidate.

Gemini is called once per Analyze click to avoid hidden repeat usage. If it
returns no obligations, the API returns an empty action list with an explicit
manual-review warning and per-page extracted-text previews; it never substitutes
unrelated demo obligations.

```json
{
  "metadata": {
    "case_title": "M/s Orient Textiles Ltd. vs. Province of Sindh & Others",
    "case_number": "C.P. No. D-2849 of 2026",
    "court_name": "High Court of Sindh, Karachi",
    "order_date": "2026-09-28"
  },
  "actions": [
    {
      "id": "ACT-01",
      "obligated_party": "Petitioner (M/s Orient Textiles)",
      "action_required": "Deposit 15% of disputed demand (PKR 4.5M) with Nazir of Court",
      "deadline_type": "Relative",
      "deadline_text": "Within 10 days from today",
      "days_offset": 10,
      "condition": "Prerequisite to maintain stay order",
      "consequence_risk": "Stay order automatically vacated and recovery resumes",
      "risk_severity": "CRITICAL",
      "source_citation": {
        "page_number": 3,
        "paragraph_reference": "Para 7",
        "verbatim_quote": "The petitioner shall deposit 15% ... within ten (10) days..."
      }
    }
  ]
}
```

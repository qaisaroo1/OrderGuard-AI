"""
PDF text and OCR extraction with page tracking for legal citation grounding.
"""
import io
import os
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Dict, Union

import pymupdf
import pytesseract
from PIL import Image

MIN_CHARS = 50
OCR_DPI = 300
OCR_LANG = "eng"
URDU_OCR_LANG = "eng+urd"
OCR_MIN_CONF = 70
JUNK_LINE_CONF = 50
JUNK_LINE_MAX_LEN = 20
PROTECT_WORD_LEN = 5
PROTECT_WORD_CONF = 85
ARABIC_RE = re.compile(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]")
DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")


class ExtractionError(Exception):
    """Raised when a PDF cannot be safely processed."""


def _configure_tesseract():
    configured_path = os.environ.get("TESSERACT_CMD")
    if configured_path:
        pytesseract.pytesseract.tesseract_cmd = configured_path
        return

    discovered_path = shutil.which("tesseract")
    if discovered_path:
        pytesseract.pytesseract.tesseract_cmd = discovered_path
        return

    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        installed_path = program_files / "Tesseract-OCR" / "tesseract.exe"
        if installed_path.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(installed_path)


_configure_tesseract()


def _is_junk_line(words) -> bool:
    text = " ".join(word for word, _ in words)
    confidences = [confidence for _, confidence in words if confidence >= 0]
    average = sum(confidences) / len(confidences) if confidences else 0.0
    if len(text) > JUNK_LINE_MAX_LEN or average >= JUNK_LINE_CONF:
        return False
    return not any(
        len(re.sub(r"[^A-Za-z]", "", word)) >= PROTECT_WORD_LEN
        and confidence >= PROTECT_WORD_CONF
        for word, confidence in words
    )


def _ocr_page(page, lang=OCR_LANG):
    """Return extracted text, mean word confidence, and dropped-line count."""
    pixmap = page.get_pixmap(dpi=OCR_DPI)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    data = pytesseract.image_to_data(
        image, lang=lang, output_type=pytesseract.Output.DICT
    )

    lines, order = {}, []
    for index, word in enumerate(data["text"]):
        if not str(word).strip():
            continue
        key = (
            data["block_num"][index],
            data["par_num"][index],
            data["line_num"][index],
        )
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append((str(word), float(data["conf"][index])))

    output, confidences, dropped, previous_paragraph = [], [], 0, None
    for key in order:
        words = lines[key]
        if _is_junk_line(words):
            dropped += 1
            continue
        paragraph = key[:2]
        if previous_paragraph is not None and paragraph != previous_paragraph:
            output.append("")
        output.append(" ".join(word for word, _ in words))
        confidences.extend(confidence for _, confidence in words if confidence >= 0)
        previous_paragraph = paragraph

    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return "\n".join(output), mean_confidence, dropped


def _arabic_count(text: str) -> int:
    return len(ARABIC_RE.findall(text))


def _arabic_ratio(line: str) -> float:
    letters = sum(1 for char in line if char.isalpha())
    return _arabic_count(line) / letters if letters else 0.0


def _mask_arabic_blocks(text: str) -> str:
    """Replace runs of Arabic-script lines with placeholders while retaining dates."""
    output, block = [], []

    def flush():
        if not block:
            return
        dates = list(dict.fromkeys(DATE_RE.findall(" ".join(block))))
        message = "[Urdu text unreadable in PDF text layer"
        if dates:
            message += "; dates seen: " + ", ".join(dates)
        output.append(message + "]")
        block.clear()

    for line in text.split("\n"):
        if line.strip() and _arabic_count(line) >= 5 and _arabic_ratio(line) >= 0.5:
            block.append(line)
        else:
            flush()
            output.append(line)
    flush()
    return "\n".join(output)


def _tidy_spacing(text: str) -> str:
    lines = text.split("\n")
    blanks = sum(1 for line in lines if not line.strip())
    filled = len(lines) - blanks
    if filled > 10 and blanks >= 0.8 * filled:
        text = re.sub(r"\n\s*\n", "\n", text)
        text = re.sub(r"\n(?=\d{1,3}\.\s)", "\n\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _strip_repeated(texts: list[str]):
    """Remove exact repeated header/footer lines, preserving page-specific labels."""

    def normalize(line: str) -> str:
        return re.sub(r"\s+", " ", line).strip().casefold()

    repeated = set()
    if len(texts) >= 2:
        counts = Counter()
        for text in texts:
            counts.update({normalize(line) for line in text.splitlines() if line.strip()})
        needed = max(2, 0.6 * len(texts))
        repeated = {line for line, count in counts.items() if count >= needed}

    page_number = re.compile(
        r"^(page\s*)?(?:\d+|\[\d+\])(\s*(of|/)\s*\d+)?$", re.I
    )
    cleaned, removed = [], set()
    for index, text in enumerate(texts):
        kept = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                kept.append("")
            elif page_number.match(stripped):
                continue
            elif index > 0 and normalize(stripped) in repeated:
                removed.add(re.sub(r"\s+", " ", stripped))
            else:
                kept.append(re.sub(r"[ \t]{2,}", "  ", line))
        cleaned.append(_tidy_spacing("\n".join(kept)))
    return cleaned, sorted(removed)


class DocumentExtractor:
    @staticmethod
    def extract_from_pdf(source: Union[str, bytes, io.BytesIO]) -> Dict:
        """
        Extract text from a PDF, OCRing pages with fewer than 50 text characters.

        The return value preserves the page-tagged text contract and adds
        per-page extraction metadata plus warnings for manual review.
        """
        try:
            if isinstance(source, bytes):
                document = pymupdf.open(stream=source, filetype="pdf")
            elif isinstance(source, str):
                document = pymupdf.open(source)
            else:
                document = pymupdf.open(stream=source.getvalue(), filetype="pdf")
        except Exception as error:
            raise ExtractionError("Could not open file as a PDF") from error

        try:
            if document.needs_pass:
                raise ExtractionError("PDF is password-protected")
            if len(document) == 0:
                raise ExtractionError("PDF has no pages")

            warnings, texts, methods, confidences = [], [], [], []
            for page_number, page in enumerate(document, 1):
                text = page.get_text(sort=True).strip()
                method, confidence = "direct", None
                if len(text) < MIN_CHARS:
                    try:
                        text, confidence, dropped = _ocr_page(page)
                        text = text.strip()
                        method = "ocr"
                        if dropped:
                            warnings.append(
                                f"Page {page_number}: dropped {dropped} short "
                                "low-confidence OCR line(s) (likely stamps/signatures/noise)"
                            )
                    except Exception as error:
                        detail = str(error).strip()
                        if isinstance(error, pytesseract.TesseractNotFoundError):
                            warnings.append(
                                f"Page {page_number}: Tesseract was not found; install it "
                                "and its language data, add it to PATH, or set TESSERACT_CMD"
                            )
                        else:
                            warning = (
                                f"Page {page_number}: OCR failed ({type(error).__name__})"
                            )
                            if detail:
                                warning += f": {detail}"
                            warnings.append(warning)

                if len(text) < MIN_CHARS:
                    warnings.append(
                        f"Page {page_number}: very little text extracted, check manually"
                    )
                if method == "ocr" and confidence is not None and confidence < OCR_MIN_CONF:
                    warnings.append(
                        f"Page {page_number}: low OCR confidence ({confidence:.0f}%), "
                        "verify names, dates and amounts"
                    )
                texts.append(text)
                methods.append(method)
                confidences.append(confidence)

            cleaned, removed = _strip_repeated(texts)
            if removed:
                warnings.append(f"Removed repeated header/footer lines: {removed}")

            ocr_pages = [
                index for index, method in enumerate(methods, 1) if method == "ocr"
            ]
            if ocr_pages:
                warnings.append(
                    f"OCR used on pages {ocr_pages}: verify names, dates and amounts manually"
                )

            pages_data = []
            for page_number, (text, method, confidence) in enumerate(
                zip(cleaned, methods, confidences), 1
            ):
                raw_text = urdu_ocr_text = None
                if _arabic_count(text) >= 20:
                    masked = _mask_arabic_blocks(text)
                    if masked != text:
                        raw_text, text = text, masked
                        try:
                            urdu_ocr_text = _ocr_page(
                                document[page_number - 1], lang=URDU_OCR_LANG
                            )[0].strip()
                        except Exception as error:
                            warnings.append(
                                f"Page {page_number}: Urdu OCR attempt failed "
                                f"({type(error).__name__})"
                            )
                        warnings.append(
                            f"Page {page_number}: Urdu/Arabic-script text masked in "
                            "`text`; original is in `raw_text`, and an unverified OCR "
                            "attempt is in `urdu_ocr_text`. Verify manually"
                        )
                    else:
                        warnings.append(
                            f"Page {page_number}: contains Urdu/Arabic-script text; "
                            "it may be scrambled, verify manually"
                        )

                pages_data.append({
                    "page": page_number,
                    "text": text,
                    "method": method,
                    "char_count": len(text),
                    "ocr_confidence": confidence,
                    "raw_text": raw_text,
                    "urdu_ocr_text": urdu_ocr_text,
                })

            combined_text = "\n\n".join(
                f"--- [PAGE {page['page']} START] ---\n{page['text']}\n"
                f"--- [PAGE {page['page']} END] ---"
                for page in pages_data
            )
            return {
                "total_pages": len(pages_data),
                "pages": pages_data,
                "full_text_with_pages": combined_text,
                "warnings": warnings,
            }
        finally:
            document.close()

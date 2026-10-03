"""
PDF text extraction engine with page tracking for legal citation grounding.
"""
from io import BytesIO
from typing import Dict, List, Union
import pypdf


class DocumentExtractor:
    @staticmethod
    def extract_from_pdf(source: Union[str, bytes, BytesIO]) -> Dict:
        """
        Extracts text from a PDF document, preserving page numbers for legal citations.
        
        Args:
            source: File path (str), raw bytes, or BytesIO buffer.
            
        Returns:
            dict containing:
                - full_text_with_pages: String with page separators
                - pages: List of dicts with {"page": int, "text": str}
                - total_pages: Total number of pages
        """
        if isinstance(source, bytes):
            stream = BytesIO(source)
        elif isinstance(source, str):
            stream = open(source, "rb")
        else:
            stream = source

        reader = pypdf.PdfReader(stream)
        total_pages = len(reader.pages)
        pages_data = []
        combined_text_parts = []

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = page.extract_text() or ""
            cleaned_text = raw_text.strip()
            
            pages_data.append({
                "page": page_num,
                "text": cleaned_text
            })
            
            combined_text_parts.append(f"--- [PAGE {page_num} START] ---\n{cleaned_text}\n--- [PAGE {page_num} END] ---")

        if isinstance(source, str):
            stream.close()

        return {
            "total_pages": total_pages,
            "pages": pages_data,
            "full_text_with_pages": "\n\n".join(combined_text_parts)
        }

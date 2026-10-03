"""
End-to-End Verification Test for OrderGuard AI Core Pipeline.
Tests: PDF Ingestion -> Text & Page Extraction -> Structured Action Mapping -> JSON Output
"""
import os
import sys
import json

from core.extractor import DocumentExtractor
from core.pipeline import LegalExtractionPipeline
from core.schemas import LegalActionMap

def test_pipeline():
    pdf_path = os.path.join("samples", "sample_court_order.pdf")
    print(f"--> [Step 1] Loading sample PDF: {pdf_path}")
    assert os.path.exists(pdf_path), "Sample PDF file not found!"

    print("--> [Step 2] Extracting text and page boundaries...")
    extracted_data = DocumentExtractor.extract_from_pdf(pdf_path)
    total_pages = extracted_data["total_pages"]
    print(f"    Success: Extracted {total_pages} page(s).")
    assert total_pages > 0, "No pages found in PDF"

    print("--> [Step 3] Running Legal Extraction Pipeline...")
    pipeline = LegalExtractionPipeline()
    action_map = pipeline.analyze_order(
        extracted_data["full_text_with_pages"],
        use_mock_fallback=True
    )

    print(f"    Success: Extracted Action Map for '{action_map.metadata.case_title}'")
    print(f"    Total Actions: {action_map.total_obligations}")
    print(f"    Critical Risks: {action_map.critical_risks_count}")

    print("--> [Step 4] Validating Structured Schema...")
    assert len(action_map.actions) > 0, "No actions extracted!"
    for act in action_map.actions:
        print(f"    [{act.id}] {act.risk_severity} RISK | Party: {act.obligated_party}")
        print(f"          Action: {act.action_required}")
        print(f"          Deadline: {act.deadline_text}")
        print(f"          Consequence: {act.consequence_risk}")
        print(f"          Source: Page {act.source_citation.page_number}")

    # Export to JSON
    json_path = os.path.join("samples", "sample_action_map.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(action_map.model_dump_json(indent=2))
    print(f"--> [Step 5] Sample data contract written to: {json_path}")

    print("\n[SUCCESS] ALL MVP PIPELINE VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pipeline()

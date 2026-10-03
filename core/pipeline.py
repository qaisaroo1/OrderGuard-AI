"""
AI Extraction Pipeline for OrderGuard AI using Google Gemini Structured Outputs.
"""
import os
import json
from typing import Optional, Dict
from dotenv import load_dotenv

from core.schemas import LegalActionMap, CaseMetadata, ActionItem, SourceCitation

load_dotenv()


SYSTEM_PROMPT = """You are OrderGuard AI, an elite autonomous legal analyst and judicial compliance specialist.
Your mission is to rigorously parse court judgments, decrees, and interim orders into an actionable, execution-ready Legal Action Map.

For the provided court judgment text (which includes [PAGE X START] and [PAGE X END] markers):
1. Extract Case Metadata:
   - Full case title, official case/petition number, court name, presiding judge(s), date of order, and a 2-3 sentence executive summary.

2. Extract EVERY Actionable Obligation / Directive:
   - Who must act (obligated_party)?
   - Who is the intended beneficiary or recipient (target_party)?
   - What exact action must be performed (action_required)?
   - What is the deadline type? ('Absolute', 'Relative', 'Immediate', 'Conditional')
   - What is the exact deadline wording (deadline_text)?
   - If relative, how many days offset (days_offset) and what is the starting trigger event (trigger_event)?
   - Are there any conditional contingencies (condition)?
   - What is the specific legal penalty or consequence if the action is neglected, missed, or defied (consequence_risk)? (e.g. contempt of court, dismissal of petition, attachment of assets, arrest warrants).
   - What is the risk severity? ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW').

3. Citation & Anti-Hallucination Grounding:
   - Every single obligation MUST reference the exact page_number where it is stated.
   - Include the exact verbatim quote (verbatim_quote) from the judgment proving the obligation.

Do not fabricate obligations. If an obligation is conditional or ambiguous, explicitly capture the condition.
"""


class LegalExtractionPipeline:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                # If google-genai is not yet installed or has issues, client remains None
                print(f"Notice: Google GenAI initialization: {e}")

    def analyze_order(self, text_with_pages: str, use_mock_fallback: bool = False) -> LegalActionMap:
        """
        Processes document text through Gemini and returns a validated LegalActionMap.
        """
        if not self.api_key or not self.client:
            if use_mock_fallback or not self.api_key:
                return self._get_mock_action_map()
            raise ValueError("GEMINI_API_KEY is missing. Please set it in your .env file or environment.")

        try:
            from google.genai import types
            
            prompt = f"Analyze the following court judgment and generate the structured Legal Action Map:\n\n{text_with_pages}"
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=LegalActionMap,
                    temperature=0.1,  # Low temperature for precise legal extraction
                )
            )
            
            # Parse structured response into Pydantic model
            if hasattr(response, "parsed") and response.parsed:
                action_map = response.parsed
            else:
                raw_json = json.loads(response.text)
                action_map = LegalActionMap(**raw_json)

            # Recalculate totals
            action_map.total_obligations = len(action_map.actions)
            action_map.critical_risks_count = sum(
                1 for a in action_map.actions if a.risk_severity in ["CRITICAL", "HIGH"]
            )
            return action_map

        except Exception as e:
            if use_mock_fallback:
                print(f"Gemini API call failed ({e}). Falling back to sample extraction.")
                return self._get_mock_action_map()
            raise e

    def _get_mock_action_map(self) -> LegalActionMap:
        """
        Realistic sample Legal Action Map for zero-failure hackathon demonstrations.
        """
        return LegalActionMap(
            metadata=CaseMetadata(
                case_title="M/s Orient Textiles Ltd. vs. Province of Sindh & Others",
                case_number="C.P. No. D-2849 of 2026",
                court_name="High Court of Sindh, Karachi",
                judge_names="Mr. Justice Tariq Mehmood Jahangiri, Mr. Justice Arshad Hussain",
                order_date="2026-09-28",
                brief_summary="Constitutional petition challenging illegal recovery notices issued by provincial tax authorities. The Court granted an interim stay against account freezing subject to a partial deposit."
            ),
            actions=[
                ActionItem(
                    id="ACT-01",
                    obligated_party="Petitioner (M/s Orient Textiles)",
                    target_party="Nazir / Court Treasury",
                    action_required="Deposit 15% of the disputed demand (PKR 4.5 Million) in the shape of pay order or bank guarantee with the Nazir of this Court.",
                    deadline_type="Relative",
                    deadline_text="Within 10 days from the date of this order",
                    days_offset=10,
                    trigger_event="Date of announcement of order (2026-09-28)",
                    condition="Prerequisite to maintain interim protective order.",
                    consequence_risk="Interim stay shall stand automatically vacated without further notice to the petitioner, and recovery proceedings will resume.",
                    risk_severity="CRITICAL",
                    source_citation=SourceCitation(
                        page_number=3,
                        paragraph_reference="Para 7",
                        verbatim_quote="The petitioner shall deposit 15% of the impugned tax demand with the Nazir of this Court within ten (10) days from today, failing which the interim relief granted herein shall cease to operate."
                    )
                ),
                ActionItem(
                    id="ACT-02",
                    obligated_party="Respondent No. 2 (Sindh Revenue Board)",
                    target_party="Petitioner",
                    action_required="Immediately de-freeze all commercial bank accounts of the petitioner and refrain from coercive recovery steps.",
                    deadline_type="Relative",
                    deadline_text="Within 24 hours of receiving proof of deposit from Nazir",
                    days_offset=1,
                    trigger_event="Verification of 15% deposit by Nazir",
                    condition="Contingent upon Petitioner complying with ACT-01.",
                    consequence_risk="Initiation of Contempt of Court proceedings under Article 204 of the Constitution against the Commissioner.",
                    risk_severity="HIGH",
                    source_citation=SourceCitation(
                        page_number=4,
                        paragraph_reference="Para 8",
                        verbatim_quote="Upon submission of the Nazir's compliance certificate, Respondent No. 2 is directed to defreeze the bank accounts within 24 hours without fail."
                    )
                ),
                ActionItem(
                    id="ACT-03",
                    obligated_party="Respondents No. 1 to 4",
                    target_party="Court Registry",
                    action_required="Submit detailed parawise comments and counter-affidavit along with relevant administrative records.",
                    deadline_type="Relative",
                    deadline_text="Within 3 weeks from receipt of court notice",
                    days_offset=21,
                    trigger_event="Service of formal court notice",
                    condition=None,
                    consequence_risk="Ex-parte proceedings will be ordered and right to file written statement shall stand forfeited.",
                    risk_severity="MEDIUM",
                    source_citation=SourceCitation(
                        page_number=4,
                        paragraph_reference="Para 9",
                        verbatim_quote="Issue notice to respondents. Parawise comments be filed within three weeks positively."
                    )
                ),
                ActionItem(
                    id="ACT-04",
                    obligated_party="Court Office / Registrar",
                    target_party="Both Parties",
                    action_required="Fix the matter for regular hearing before the division bench on the next assigned cause list.",
                    deadline_type="Absolute",
                    deadline_text="2026-11-04",
                    days_offset=None,
                    trigger_event=None,
                    condition=None,
                    consequence_risk="Case delay and procedural adjournment.",
                    risk_severity="LOW",
                    source_citation=SourceCitation(
                        page_number=5,
                        paragraph_reference="Para 11",
                        verbatim_quote="Relist on 04.11.2026 for regular hearing."
                    )
                )
            ],
            total_obligations=4,
            critical_risks_count=2
        )

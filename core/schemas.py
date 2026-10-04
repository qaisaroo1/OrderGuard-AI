from typing import List, Optional
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    page_number: int = Field(
        ..., description="Exact page number in the court document where this obligation appears"
    )
    paragraph_reference: Optional[str] = Field(
        default=None, description="Paragraph number or section heading if identified (e.g. 'Para 12')"
    )
    verbatim_quote: str = Field(
        ..., description="Exact sentence or verbatim excerpt from the judgment creating this obligation"
    )


class ActionItem(BaseModel):
    id: str = Field(
        ..., description="Unique identifier for the action, e.g. 'ACT-01', 'ACT-02'"
    )
    obligated_party: str = Field(
        ..., description="The party bound to perform the action (e.g. 'Petitioner', 'Respondent / FBR', 'Registry')"
    )
    target_party: Optional[str] = Field(
        default=None, description="The recipient or beneficiary party (e.g. 'Petitioner', 'Court')"
    )
    action_required: str = Field(
        ..., description="Concise, plain-English summary of what must be done"
    )
    deadline_type: str = Field(
        ..., description="Type of deadline: 'Absolute' (specific date), 'Relative' (e.g. within X days), 'Immediate', or 'Conditional'"
    )
    deadline_text: str = Field(
        ..., description="Exact deadline wording as stated in order (e.g. 'Within 14 days of receipt of order', 'On or before 25th October 2026')"
    )
    days_offset: Optional[int] = Field(
        default=None, description="Extracted numerical days for relative deadlines (e.g. 14 for 'within 14 days')"
    )
    trigger_event: Optional[str] = Field(
        default=None, description="Event that starts the clock for relative deadlines (e.g. 'Service of certified copy', 'Deposit of fee')"
    )
    condition: Optional[str] = Field(
        default=None, description="Prerequisite conditions before this action is triggered (e.g. 'Subject to deposit of 10% penalty')"
    )
    consequence_risk: str = Field(
        ..., description="Specific legal penalty, risk, or fallout if this action is missed or delayed (e.g. 'Contempt of court', 'Attachment of property', 'Dismissal of petition')"
    )
    risk_severity: str = Field(
        ..., description="Severity level: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'"
    )
    source_citation: SourceCitation = Field(
        ..., description="Citations grounding this obligation to the source text"
    )


class CaseMetadata(BaseModel):
    case_title: str = Field(
        ..., description="Full title of the case (e.g. 'M/s Falcon Enterprises vs. Federation of Pakistan')"
    )
    case_number: str = Field(
        ..., description="Official case / suit / petition number (e.g. 'W.P. No. 4521/2026')"
    )
    court_name: str = Field(
        ..., description="Name of the court (e.g. 'High Court of Sindh', 'Supreme Court', 'Civil Court')"
    )
    judge_names: Optional[str] = Field(
        default=None, description="Name(s) of presiding Judge(s) / Bench"
    )
    order_date: str = Field(
        ..., description="Date on which the judgment/order was announced or signed"
    )
    brief_summary: str = Field(
        ..., description="2-3 sentence executive summary of the order and the core dispute"
    )


class AgentTraceStep(BaseModel):
    agent_name: str = Field(
        ..., description="Name of the specialized agent (e.g. 'ClauseExtractorAgent')"
    )
    role: str = Field(
        ..., description="Specialty of the agent"
    )
    status: str = Field(
        default="Completed", description="Execution status of the agent"
    )
    findings_summary: str = Field(
        ..., description="Summary of insights, dependencies, or validations found by this agent"
    )


class LegalActionMap(BaseModel):
    metadata: CaseMetadata
    actions: List[ActionItem] = Field(
        default_factory=list, description="List of all extracted obligations and actionable directives"
    )
    total_obligations: int = Field(
        default=0, description="Total count of actionable obligations extracted"
    )
    critical_risks_count: int = Field(
        default=0, description="Count of obligations with CRITICAL or HIGH risk severity"
    )
    agent_traces: List[AgentTraceStep] = Field(
        default_factory=list, description="Multi-agent audit trace detailing each agent's execution"
    )

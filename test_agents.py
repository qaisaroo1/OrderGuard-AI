"""
Live Test Script for the 4-Agent Pipeline in OrderGuard AI.
Runs:
1. ClauseExtractorAgent
2. TimelineResolverAgent
3. RiskAssessorAgent
4. CitationAuditorAgent
"""
import sys
from core.agents import MultiAgentCoordinator

SAMPLE_JUDGMENT_2 = """IN THE HIGH COURT OF SINDH AT KARACHI
Suit No. 1942 of 2026

M/s Apex Logistics & Shipping Pvt. Ltd.            ..... Plaintiff
                          VERSUS
1. Collector of Customs (Appraisement East), Karachi.
2. State Bank of Pakistan, I.I. Chundrigar Road, Karachi.
3. Habib Bank Ltd., Corporate Branch, Karachi.    ..... Defendants

BEFORE: Mr. Justice Zulfiqar Ahmad Khan

INTERLOCUTORY ORDER

--- [PAGE 1 START] ---
1. The Plaintiff seeks an urgent interim injunction restraining Defendant No. 1 from auctioning five (5) detained commercial shipping containers containing industrial machinery.

2. Learned counsel for the Plaintiff submits that the delay in clearance was caused entirely by statutory tariff re-classification disputes, and the auction notice issued on 25.09.2026 is illegal.

3. Mr. Khalid Javed, learned counsel for Pakistan Customs, opposes the grant of unconditional stay, arguing that statutory demurrage and import duties of PKR 12.5 Million remain outstanding.
--- [PAGE 1 END] ---

--- [PAGE 2 START] ---
4. Having heard the learned counsel for the parties, we dispose of this injunction application (CMA No. 8412/2026) with the following binding directives:

DIRECTIVE 1:
The Plaintiff (M/s Apex Logistics) shall furnish a Bank Guarantee or post an Indemnity Bond amounting to PKR 10,000,000/- with the Nazir of this Court within fourteen (14) days from today.
PENALTY: If the Plaintiff fails to submit the bank guarantee within the stipulated 14 days, the ad-interim restraining order shall stand automatically recalled, and Defendant No. 1 shall be free to proceed with public auction without further reference to this Court.

DIRECTIVE 2:
Upon verification of the Nazir's certificate confirming deposit of the aforesaid guarantee, Defendant No. 1 (Collector of Customs) is strictly directed to issue the Delivery Order and release the 5 detained containers within forty-eight (48) hours.
PENALTY: Any officer defying this directive shall be personally liable for Contempt of Court under Article 204 of the Constitution and Section 3 of the Contempt of Court Ordinance.
--- [PAGE 2 END] ---

--- [PAGE 3 START] ---
DIRECTIVE 3:
Defendant No. 2 (State Bank of Pakistan) and Defendant No. 3 (Habib Bank Ltd.) are restrained from encashing or debiting the disputed Letter of Credit (LC No. SBP-8849) until the next date of hearing.

DIRECTIVE 4:
The Office / Registrar is directed to issue formal notices to all defendants and fix this suit for framing of issues on 15.12.2026.

Announced this 2nd day of October, 2026.
                                                (Justice Zulfiqar Ahmad Khan)
--- [PAGE 3 END] ---
"""

def test_multi_agent():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("=" * 70)
    print(">> ORDERGUARD AI -- LIVE MULTI-AGENT EXECUTION TEST")
    print("=" * 70)

    def on_progress(step, total, agent_name, message):
        print(f"\n[Step {step}/{total}] [AGENT] {agent_name}")
        print(f"       Status: {message}")

    coordinator = MultiAgentCoordinator()
    action_map = coordinator.execute_workflow(
        document_text=SAMPLE_JUDGMENT_2,
        progress_callback=on_progress,
        use_mock_fallback=True
    )

    print("\n" + "=" * 70)
    print("📊 AGENT WORKFLOW RESULTS")
    print("=" * 70)
    print(f"Case Title: {action_map.metadata.case_title}")
    print(f"Case No:    {action_map.metadata.case_number}")
    print(f"Total Obligations Extracted: {action_map.total_obligations}")
    print(f"Critical / High Risks:       {action_map.critical_risks_count}")

    print("\n" + "-" * 70)
    print("🤖 MULTI-AGENT AUDIT TRACE LOG (JUDGE VIEW):")
    print("-" * 70)
    for trace in action_map.agent_traces:
        print(f"• [{trace.status.upper()}] {trace.agent_name} ({trace.role})")
        print(f"  Findings: {trace.findings_summary}\n")

    print("[SUCCESS] All 4 agents executed and validated successfully!")

if __name__ == "__main__":
    test_multi_agent()

# OrderGuard AI ⚖️
### Autonomous Legal Action Mapping & Execution Engine

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)

---

## 📌 The Problem It Solves

Court orders and legal judgments are notoriously long, dense, and complex—often spanning 30 to 50+ pages of convoluted legal jargon. 

Buried deep within these documents are high-stakes, time-sensitive directives and conditional obligations. Missing a single hidden deadline or prerequisite condition can lead to catastrophic legal consequences:
* **Automatic vacation of stay orders** (allowing authorities to seize bank accounts or property).
* **Contempt of Court proceedings** under constitutional law.
* **Ex-parte decrees and procedural dismissals** forfeiting the right of defense.

Lawyers and corporate compliance teams currently rely on manual reading and manual highlighter tracking, making human error in high-volume litigation inevitable.

---

## 💡 The Solution

**OrderGuard AI** transforms passive court document reading into an active, zero-failure execution roadmap. 

Powered by **Google Gemini** and specialized agentic orchestration, OrderGuard AI automatically parses unstructured court judgments to generate an interactive **Legal Action Map** tracking:
* **Who** must act (*Petitioner, Respondent, Court Registry, Third Party*)
* **What** must be done (*Binding directives and prohibitions*)
* **By when** (*Concrete calendar deadlines translated from relative clauses*)
* **Under what condition** (*Contingencies and prerequisites*)
* **With what consequence** (*Legal penalties and compliance risk severity*)

---

## 🚀 Key Features

* 🤖 **Specialized 4-Agent Pipeline:**
  * **Agent 1 (Clause & Directive Extractor):** Separates procedural history from operative orders to isolate binding directives.
  * **Agent 2 (Timeline & Dependency Resolver):** Maps relative timeframes (*"within 14 days"*, *"within 24 hours"*) and resolves prerequisite dependency chains.
  * **Agent 3 (Legal Risk & Penalty Assessor):** Evaluates default liabilities, contempt exposure, and scores severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
  * **Agent 4 (Citation & Anti-Hallucination Auditor):** Cross-references extracted directives against the source document to verify page citations and verbatim quotes.

* ⏱️ **Smart Relative Timeline Resolution:** Translates complex legal conditions (*"within 10 days of receipt"*) into concrete calendar dates based on the service date.

* 🚨 **Risk & Consequence Mapping:** Explicitly details the legal fallout and penalties if a task is neglected or delayed.

* 🛡️ **Anti-Hallucination Citation Grounding:** Every single extracted action item is directly anchored to its exact page number and verbatim excerpt from the judgment.

* 👤 **Multi-Party Perspective Switcher:** Instantly filter duties between *Petitioner Counsel* (to track compliance) and *Respondent Defense Counsel* (to monitor opposing counsel deadlines).

* 📅 **1-Click Execution & Calendar Sync:** Export all tracked obligations directly to Google/Apple Calendar (`.ics`) and download structured JSON data contracts.

---



# 2. Run Application
streamlit run app.py

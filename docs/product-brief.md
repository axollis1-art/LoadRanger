# Project Handoff: Automated Credit Underwriting & Covenant Monitoring Platform

## Project Context

This is a portfolio/CV software engineering project intended to demonstrate the design and construction of a realistic financial technology application.

The product is an **Automated Credit Underwriting & Covenant Monitoring Platform** for corporate/commercial lending.

The working project name has not been finalized. Names considered include **Credit Canary**, **RiskRadar**, **CovenantIQ**, **CreditSentry**, and **CovenantGuard**.

The project should be sophisticated enough to demonstrate strong software engineering, financial-domain understanding, API/backend development, data modelling, testing, and appropriate use of AI, while remaining achievable by an individual developer.

The objective is **not** to recreate a production banking platform. It is to build a focused, technically credible MVP that demonstrates how such a system could work.

---

# 1. Product Concept

The application performs two related functions:

### Credit Underwriting

Given financial information about a corporate borrower, the system should:

* Standardise the financial information.
* Calculate relevant credit metrics.
* Apply configurable underwriting rules.
* Produce a credit/risk assessment.
* Explain the factors contributing to the assessment.

### Covenant Monitoring

For loans already issued, the system should:

* Store the financial covenants associated with a loan.
* Calculate the metrics required to test those covenants.
* Determine whether each covenant is compliant.
* Calculate covenant headroom.
* Identify borrowers approaching covenant limits.
* Detect actual covenant breaches.
* Maintain historical covenant-test results.
* Generate appropriate warnings/alerts.

The overall conceptual workflow is:

```text
Borrower
    │
    ↓
Financial Information
    │
    ↓
Financial Metrics Engine
    │
    ├──────────────→ Underwriting Engine
    │                     │
    │                     ↓
    │                Credit Assessment
    │
    └──────────────→ Covenant Engine
                          │
                          ↓
                   Pass / Warning / Breach
                          │
                          ↓
                     Alerts / History
```

---

# 2. Intended User

The conceptual end user is a:

* Commercial lender
* Credit analyst
* Portfolio manager
* Credit officer

However, this is a demonstration/portfolio application rather than a production system intended for real lending decisions.

The UI and terminology should therefore resemble a professional credit-risk application without pretending that the application's demonstration scoring model represents a real bank's lending policy.

---

# 3. Core Domain Model

The central entity is a **Borrower**.

A borrower can have:

* Multiple periods of financial information.
* One or more loans/facilities.
* Credit assessments.
* Alerts.

A loan/facility can have:

* Loan terms.
* Multiple covenants.
* Historical covenant-test results.

Conceptually:

```text
Borrower
│
├── Financial Periods
│
├── Credit Assessments
│
├── Loans / Facilities
│      │
│      └── Covenants
│              │
│              └── Covenant Test History
│
└── Alerts
```

The coding agent should determine an appropriate persistence model and relationships based on these requirements.

---

# 4. Financial Information

The initial application should support enough financial information to calculate meaningful commercial-credit metrics.

Representative inputs include:

* Revenue
* EBITDA
* Cash
* Total debt
* Interest expense
* Current assets
* Current liabilities
* Capital expenditure
* Tax
* Depreciation/amortisation

The system should support multiple financial periods so deterioration/improvement can eventually be analysed over time.

Synthetic demonstration data should be used rather than real confidential borrower information.

---

# 5. Financial Metrics

The financial calculation layer should be deterministic, reproducible, and testable.

Initial metrics should include at least:

### Net Debt

Net Debt = Total Debt − Cash

### Debt / EBITDA

Debt / EBITDA = Total Debt ÷ EBITDA

### Net Debt / EBITDA

Net Debt / EBITDA = Net Debt ÷ EBITDA

### Interest Coverage

Interest Coverage = EBITDA ÷ Interest Expense

### Current Ratio

Current Ratio = Current Assets ÷ Current Liabilities

### EBITDA Margin

EBITDA Margin = EBITDA ÷ Revenue

### Simplified Free Cash Flow

An appropriate simplified formula can be used for the MVP, with its assumptions clearly documented.

The coding agent may recommend additional metrics if they materially improve the demonstration.

Special attention should be given to financial edge cases such as:

* Zero EBITDA.
* Negative EBITDA.
* Missing financial information.
* Zero interest expense.
* Missing values versus genuine zero values.
* Appropriate numerical precision.

The system should not silently produce misleading ratios where the calculation is financially meaningless.

---

# 6. Underwriting Engine

The application should contain a **demonstration rules-based underwriting engine**.

Its purpose is not to reproduce a real financial institution's proprietary credit model.

Instead, it should demonstrate how:

```text
Financial Information
        ↓
Financial Metrics
        ↓
Underwriting Rules
        ↓
Credit Score / Grade
        ↓
Decision / Review Recommendation
        ↓
Explanation
```

The engine might consider factors such as:

* Leverage.
* Interest coverage.
* Liquidity.
* Profitability.
* Potentially financial trends.

The output should include more than a numerical score.

A useful assessment should contain:

* Credit score.
* Risk grade.
* Indicative decision/recommendation.
* Positive factors.
* Risk factors.
* Metrics supporting those conclusions.

Explainability is a key design requirement.

A user should be able to understand **why** the system produced a particular assessment.

The coding agent should recommend an appropriate way of representing configurable underwriting policies rather than unnecessarily hard-coding every rule.

---

# 7. Covenant Engine

The covenant-monitoring engine is one of the project's most important components.

A covenant should conceptually contain:

* Name.
* Financial metric being tested.
* Comparison/operator.
* Threshold.
* Testing frequency.
* Optional warning threshold.
* Source/provenance information where applicable.

Example:

```text
Maximum Net Leverage

Metric:
Net Debt / EBITDA

Requirement:
<= 4.50x

Warning:
>= 4.00x

Frequency:
Quarterly
```

The system should be capable of evaluating generic rules such as:

```text
Net Debt / EBITDA <= 4.50x

Interest Coverage >= 2.50x

Minimum Liquidity >= £2,000,000
```

The preferred conceptual output is:

```text
PASS
WARNING
BREACH
```

The engine should also calculate meaningful **headroom** between the current value and covenant threshold.

The design should avoid requiring a completely separate implementation for every possible financial covenant where a reusable rule/evaluation model would suffice.

---

# 8. Historical Monitoring

Covenant testing should create historical records rather than simply overwriting the previous result.

This should eventually allow the application to show behaviour such as:

```text
Q1     3.1x     PASS
Q2     3.4x     PASS
Q3     4.1x     WARNING
Q4     4.7x     BREACH
```

This historical information can later support early-warning analytics.

---

# 9. Early-Warning Concept

A desirable extension is to identify deterioration **before an actual covenant breach occurs**.

For example:

```text
Net Debt / EBITDA

Q1    3.1x
Q2    3.4x
Q3    3.8x
Q4    4.2x

Covenant limit: 4.5x
```

The application could identify that:

* Leverage is deteriorating.
* Covenant headroom is shrinking.
* The borrower should be placed on a watchlist.

For the MVP this does not need sophisticated machine learning.

Simple, transparent trend-based logic is preferable to an unjustified predictive model.

---

# 10. Alerts

The system should support alerts generated from meaningful credit events.

Examples include:

* Covenant approaching threshold.
* Covenant breached.
* Significant deterioration in leverage.
* Interest coverage deterioration.
* Liquidity approaching minimum requirement.

Alerts should have appropriate severity and lifecycle/status concepts.

The coding agent should recommend an appropriately simple architecture for this rather than over-engineering an event system for the initial portfolio version.

---

# 11. API / Application Behaviour

The application should expose the domain functionality through a well-designed API.

The exact API structure should be determined by the coding agent, but it should support workflows around:

* Borrower management.
* Financial-period management.
* Financial analysis.
* Loan/facility management.
* Covenant management.
* Running covenant tests.
* Running underwriting assessments.
* Retrieving historical covenant results.
* Retrieving alerts.
* Retrieving a consolidated borrower/credit summary.

The API should follow sensible REST/API design principles and provide useful validation and error handling.

Automatic API documentation would be desirable.

---

# 12. User Interface

Backend engineering is the primary focus of the project.

However, a small frontend/dashboard is desirable because it makes the project significantly easier to demonstrate to recruiters/interviewers.

The dashboard does not need to be visually elaborate.

A borrower page should ideally communicate something resembling:

```text
ABC Manufacturing Ltd

CREDIT ASSESSMENT
Risk Grade: B
Score: 76 / 100
Status: Review

FINANCIAL METRICS
Revenue                 £25.0m
EBITDA                   £4.0m
Net Debt                £12.0m
Net Debt / EBITDA         3.0x
Interest Coverage         4.0x
Current Ratio             1.14x

COVENANTS
Maximum Leverage          PASS
Interest Coverage         PASS
Minimum Liquidity         WARNING

ALERTS
Liquidity approaching covenant threshold.
```

Historical metrics/covenant status would be useful to visualise where practical.

The coding agent should recommend a frontend approach proportionate to a portfolio project.

---

# 13. AI / Document Extraction Extension

AI should be treated as an enhancement rather than the foundation of the application.

Once the deterministic credit and covenant engines work, the project should ideally support:

```text
Loan Agreement PDF
        ↓
Document Processing
        ↓
LLM
        ↓
Covenant Extraction
        ↓
Structured Proposed Covenant
        ↓
Human Verification
        ↓
Covenant Engine
```

For example, given contractual language stating that a borrower must maintain a consolidated leverage ratio below a specified threshold, the AI component should attempt to extract structured information such as:

```text
Covenant:
Maximum Consolidated Net Leverage

Metric:
Net Debt / EBITDA

Operator:
<=

Threshold:
4.50

Frequency:
Quarterly

Source:
Document/page/section
```

A human should be able to verify/correct the extraction before it becomes an active covenant.

---

# 14. Important AI Design Principle

The project should explicitly distinguish between:

### Deterministic financial logic

Used for:

* Arithmetic.
* Financial ratios.
* Covenant testing.
* Threshold comparisons.
* Credit-policy rules.
* Dates.
* Headroom calculations.

### LLM/AI functionality

Used for:

* Understanding unstructured loan documents.
* Identifying covenant clauses.
* Extracting structured information.
* Summarising risk factors.
* Potentially generating human-readable explanations.

The LLM should **not** be treated as a trusted financial calculator or final covenant-compliance decision maker.

Conceptually:

```text
AI extracts information
        ↓
Structured data
        ↓
Deterministic engine
        ↓
Decision
```

This separation is an important part of the project's engineering story.

---

# 15. Auditability

Auditability and explainability should influence the design.

For an important result, the system should conceptually be capable of showing:

```text
Source financial information
        ↓
Calculated metric
        ↓
Rule/covenant applied
        ↓
Threshold
        ↓
Result
        ↓
Explanation
```

For AI-extracted covenants, provenance should ideally include the originating document and location/page/section.

The project does not need production-grade banking compliance infrastructure, but the architecture should demonstrate awareness that credit decisions need to be reproducible and explainable.

---

# 16. Testing Expectations

Testing is an important part of the portfolio value of the project.

Particular emphasis should be placed on unit-testing:

* Financial calculations.
* Financial edge cases.
* Underwriting rules.
* Covenant evaluation.
* Warning/breach boundaries.
* Headroom calculations.

Integration/API tests should cover the main end-to-end workflows.

The goal is to demonstrate that financial/business logic is reliable rather than merely producing plausible-looking dashboard results.

---

# 17. Demonstration Scenario

The finished project should contain synthetic borrowers designed to demonstrate different risk conditions.

For example:

### Healthy borrower

* Strong EBITDA.
* Moderate leverage.
* Good liquidity.
* Comfortable covenant headroom.

### Watchlist borrower

* Increasing leverage.
* Declining EBITDA.
* Covenant headroom shrinking.

### Distressed borrower

* High leverage.
* Weak coverage.
* Covenant breach.

A particularly useful demonstration workflow would be:

```text
Borrower begins with:

Net Debt = £12m
EBITDA = £4m

Net Debt / EBITDA = 3.0x

Covenant:
<= 4.5x

Result:
PASS
```

Then introduce a new financial period:

```text
Net Debt = £12m
EBITDA = £2.5m

Net Debt / EBITDA = 4.8x

Result:
BREACH
```

The application should visibly demonstrate the transition from healthy → warning → breach.

---

# 18. Scope Constraints

This is a portfolio project, so avoid unnecessary enterprise complexity.

Do not initially prioritise:

* Real bank integrations.
* Real credit-bureau integrations.
* Production regulatory compliance.
* Complex machine-learning default models.
* Kubernetes.
* Microservices purely for architectural sophistication.
* Large event-driven architectures.
* Dozens of covenant types.
* Complex identity/access-management systems.
* Perfect reproduction of IFRS/GAAP accounting.

Prefer a well-engineered modular application over distributed-system complexity.

---

# 19. Desired Engineering Characteristics

The coding agent should reinterpret the requirements and recommend the most appropriate current technologies/frameworks rather than blindly following earlier implementation suggestions.

The resulting system should ideally demonstrate:

* Clean architecture/separation of concerns.
* Strong domain modelling.
* Deterministic financial calculations.
* Configurable business rules.
* Relational data modelling.
* Good API design.
* Input validation.
* Appropriate error handling.
* Automated tests.
* Database migrations.
* Reproducible local development.
* Good documentation.
* Sensible use of containers where beneficial.
* Appropriate use of AI rather than AI for its own sake.
* A simple but effective demonstration UI.
* Clear auditability/explainability.

Do not over-engineer the system merely to include more technologies.

---

# 20. Portfolio/CV Objective

The finished project should allow the developer to credibly describe it approximately as:

> Designed and developed an automated commercial-credit underwriting and covenant-monitoring platform that evaluates borrower financials using configurable credit policies, calculates financial ratios, monitors loan covenants and generates early-warning alerts. Built an auditable rules engine for deterministic credit decisions and integrated AI-assisted extraction of covenant terms from unstructured loan agreements.

The project should demonstrate a combination of:

**Software Engineering + Backend Development + Financial Domain Knowledge + Data Modelling + Applied AI**

rather than simply being an "AI wrapper."

---

# 21. Requested Next Action From Coding Agent

Before implementation, review the requirements above and propose the best architecture for the project.

Specifically:

1. Recommend the technology stack and explain the major choices.
2. Propose the high-level architecture and module boundaries.
3. Propose the core domain/data model.
4. Define what belongs in MVP v1 versus later extensions.
5. Recommend the implementation sequence.
6. Identify any weaknesses, unnecessary complexity, or missing concepts in this specification.
7. Suggest improvements that would make the project more impressive to a technical recruiter while remaining realistic for a solo portfolio project.
8. Only after the architecture has been agreed should implementation begin.

Do not treat previous framework suggestions as mandatory. Select technologies based on what best fits the project and its portfolio objective.

# StoryGuard — Phase 2: Populate the Knowledge Base
## Building the RAG Context Layer

**Goal:** Give the pipeline real reference material so Steps 2 and 3 produce richer output.  
**Time:** ~2 hours  
**Prerequisite:** Phase 1 complete (you've seen what the pipeline produces without RAG context)

---

## Why this matters

Every prompt in Steps 2–3 has a `{{rag_context}}` variable. Right now it's empty.
Without it, the pipeline enriches stories in a vacuum — it can't reference your
organization's standards, past precedents, or domain-specific NFR patterns.

A populated knowledge base means:
- Step 2 (intake parser) flags vagueness against known standards, not just common sense
- Step 3 (enrichment) pulls in proven personas and patterns from past stories
- Step 4 (NFR probe) matches compliance requirements to your actual regulatory exposure

The knowledge base doesn't need to be large. 10–15 well-structured documents will
produce meaningfully better output than zero.

---

## What to put in the knowledge base

### Category 1 — Past story templates (3–5 files)

Well-formed requirements documents from past projects. These become the positive
examples the pipeline draws on when structuring new stories.

**What makes a good example:**
- Clear user story with a named role (not "user")
- At least 4 functional requirements using "The system shall" language
- NFRs defined for at least 3 categories
- Given/When/Then acceptance criteria

**If you don't have real past stories:** Create synthetic ones using the pipeline
itself — run 2–3 test cases to completion, then use the output as knowledge base entries.

**File naming:** `knowledge_base/past_stories/STORY-001-portfolio-performance.md`

---

### Category 2 — NFR standards (2–3 files)

Domain-specific performance, security, and compliance thresholds that apply
across all stories in this environment.

**Wealth management NFR baseline to document:**

```markdown
# Wealth Management NFR Standards

## Performance
- Dashboard/report load: < 3 seconds under normal load (< 500 concurrent users)
- Batch report generation: < 60 seconds for standard portfolio (< 500 holdings)
- API response time: < 500ms at p95

## Security
- All client data: encrypted at rest (AES-256) and in transit (TLS 1.2+)
- Authentication: MFA required for all advisor-facing features
- Session timeout: 30 minutes idle for advisor portal, 15 minutes for client portal
- Data access: role-based, logged, auditable

## Auditability (required for all stories touching client data)
- Log: who accessed what, when, from where
- Retention: 7 years minimum (FINRA Rule 4511)
- Log storage: tamper-evident, separate from application database
- Access to logs: restricted to compliance/operations roles

## Compliance
- FINRA Rule 4511: Books and records retention
- SEC Rule 17a-4: Electronic record storage
- SOC 2 Type II: applicable to all platform features
```

**File:** `knowledge_base/standards/nfr-wealth-management.md`

---

### Category 3 — Persona library (1 file)

Named roles that appear across your domain. The enrichment prompt will pull
these rather than inventing new role names each run.

```markdown
# Wealth Management Persona Library

## Portfolio Manager
Primary user of performance reporting, rebalancing, and trade execution features.
Needs pre-market data, client portfolio summaries, and exception alerts.

## Client Service Associate (CSA)
Handles client onboarding, account maintenance, and document requests.
Needs access to client profile, account history, and document management.

## Compliance Officer
Reviews flagged activity, generates regulatory reports, and approves exceptions.
Needs audit logs, flagged transaction reports, and exception queues.

## Wealth Management Client
End client accessing the client portal for statements, performance, and messaging.
Needs simplified views, mobile access, and clear data presentation.

## Operations Analyst
Handles back-office processing, reconciliation, and data quality.
Needs reconciliation reports, exception queues, and custodian feed status.

## System Administrator
Manages user access, permissions, and system configuration.
Needs user management, role assignment, and audit log access.
```

**File:** `knowledge_base/personas/wealth-management-personas.md`

---

### Category 4 — Compliance reference (1 file)

Quick reference for the regulations the pipeline should flag when relevant.
This helps the NFR probe (Step 4) cite specific rules rather than generic statements.

```markdown
# Regulatory Quick Reference — Wealth Management

## FINRA
- Rule 4511: General requirements for books and records — 3-year minimum retention
- Rule 4512: Customer account information — must be current and accurate
- Rule 3110: Supervision — written supervisory procedures required

## SEC
- Rule 17a-4: Specifies electronic record retention requirements (non-erasable, non-rewritable)
- Regulation S-P: Privacy of consumer financial information — annual privacy notice
- Regulation S-ID: Identity theft red flags

## SOC 2 (Type II)
- Trust Service Criteria: Security, Availability, Processing Integrity, Confidentiality, Privacy
- Applicable to all SaaS platform features handling client data

## Flagging guidance
- Any story touching client PII → flag Regulation S-P
- Any story that creates or modifies records → flag FINRA 4511, SEC 17a-4
- Any story involving advisor-client communication → flag FINRA 4512
- Any story involving financial calculations or reporting → flag Processing Integrity (SOC 2)
```

**File:** `knowledge_base/compliance/regulatory-reference.md`

---

## How to create the files

### Option A — Claude Code (recommended, ~1 hour)

```
Create the StoryGuard knowledge base files. Use the structure and content
defined in docs/PHASE2_KNOWLEDGE_BASE.md.

Create these files:
1. knowledge_base/standards/nfr-wealth-management.md — NFR thresholds
2. knowledge_base/personas/wealth-management-personas.md — persona library
3. knowledge_base/compliance/regulatory-reference.md — compliance quick reference
4. knowledge_base/past_stories/STORY-EXAMPLE-001.md — one synthetic example
   story based on TEST-001's completed output in outputs/TEST-001-complete.json

For STORY-EXAMPLE-001: format it as a readable markdown document showing
the user story, functional requirements, NFRs, and acceptance criteria
as a reference template — not raw JSON.
```

### Option B — Manual (~2 hours)

Create the directory structure and write each file yourself using the
content above as a starting point, customizing for your actual environment.

```bash
mkdir -p knowledge_base/standards knowledge_base/personas \
         knowledge_base/compliance knowledge_base/past_stories
```

---

## Integrating the knowledge base into the pipeline

The knowledge base feeds into n8n as `{{rag_context}}`. For now, you have
two practical options:

**Option A — Static context injection (fastest to build)**  
Concatenate the relevant knowledge base files and paste them directly into
the n8n prompt as a fixed string. No retrieval logic needed — just include
the full NFR standards + persona library in every call to Steps 2–3.

This works well when the knowledge base is small (< 10KB total). It costs
slightly more in tokens but eliminates RAG infrastructure.

In n8n, set `{{rag_context}}` to a static "Set" node that contains
the concatenated content of your standards + persona files.

**Option B — File-based retrieval (more scalable)**  
Add a "Read Binary File" node in n8n before Steps 2–3 that reads the
relevant knowledge base file based on the domain field from Step 1.

Map domain → file:
```
wealth_management  → knowledge_base/standards/nfr-wealth-management.md
compliance         → knowledge_base/compliance/regulatory-reference.md
client_portal      → knowledge_base/personas/wealth-management-personas.md
```

For Phase 3 (n8n wiring), start with Option A. You can add retrieval logic later.

---

## Validating the improvement

After populating the knowledge base, re-run TEST-001 Steps 2–3 with the
RAG context now populated and compare:

1. Are more personas named and domain-specific (vs generic "user")?
2. Are NFRs in Step 4 citing specific regulations?
3. Did the vagueness_flags in Step 2 catch more gaps?
4. Did the total quality score improve vs the Phase 1 run?

```
Re-run Steps 2 and 3 of the pipeline for TEST-001, this time including
the knowledge base content as {{rag_context}}.

Read:
- knowledge_base/standards/nfr-wealth-management.md
- knowledge_base/personas/wealth-management-personas.md

Include their content as the rag_context input to PROMPT_02_INTAKE_PARSER
and PROMPT_03_ENRICHMENT from prompts/pipeline_prompts.txt.

Compare the output quality to outputs/TEST-001-day2-enrichment.json.
Note any meaningful improvements.
```

---

## When this phase is done

- [ ] `knowledge_base/standards/nfr-wealth-management.md` created
- [ ] `knowledge_base/personas/wealth-management-personas.md` created
- [ ] `knowledge_base/compliance/regulatory-reference.md` created
- [ ] At least 1 past story example in `knowledge_base/past_stories/`
- [ ] Re-run of TEST-001 Steps 2–3 shows measurably richer output
- [ ] Ready to move to Phase 3 (n8n wiring)

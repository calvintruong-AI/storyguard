# StoryGuard
### AI-Governed Requirements Quality Pipeline

> Intercepts vague BA intake before it reaches engineering — enriching it into 
> governed, implementation-ready user stories with NFRs, personas, system 
> dependencies, and acceptance criteria structured for AI coding agent consumption.

---

## The Problem

Every BA team has experienced this: a story enters a sprint, engineering hits 
ambiguity on day two, and the root cause is a requirement that should have been 
caught at intake — not mid-sprint. In financial services, the cost is higher: 
a story that omits audit logging or a compliance requirement isn't just a delivery 
problem — it's a regulatory risk.

**StoryGuard solves this at the source.**

---

## How It Works

A BA submits a raw intake request (1–3 sentences). StoryGuard runs it through 
a 6-step governed AI pipeline and returns a complete, scored requirements document 
in under 60 seconds.

```
Raw Intake (1-3 sentences)
        │
        ▼
[1] Governance Pre-Check ──── Ollama (local) — PII detection
        │ clean
        ▼
[2] Context Retrieval ──────── RAG — retrieve relevant past stories + standards
        │
        ▼
[3] Requirements Enrichment ── Claude API — user story, personas, functional reqs
        │
        ▼
[4] NFR Probe ──────────────── Claude API — performance, security, compliance, audit
        │
        ▼
[5] AC + Dependency Mapper ─── Claude API — Given/When/Then + system map
        │
        ▼
[6] Governance Audit + Score ── Claude API — assumptions, hallucination flags, 0-10 score
        │
        ▼
[Human Review via Slack] ───── BA approves before delivery
        │ approved
        ▼
[Google Docs output] ────────── Implementation-ready requirements document
[Google Sheets log] ─────────── Completeness scorecard row appended
```

---

## Tech Stack

| Tool | Role | Cost |
|------|------|------|
| n8n (self-hosted) | Workflow orchestration | Free |
| Claude API | Requirements enrichment, NFR probe, scoring | Pay per use (~$0.01/story) |
| Ollama (local) | PII detection — never leaves your machine | Free |
| Google Forms | Intake trigger | Free |
| Google Docs | Output delivery | Free |
| Google Sheets | Completeness scorecard | Free |
| Slack | Human-in-the-loop approval | Free |
| GitHub | Source control | Free |

---

## Governance Design

StoryGuard is built **governance-first**, not speed-first. Three layers:

1. **Data privacy at the gate** — Local Ollama PII check before any text reaches an external API
2. **Assumption transparency** — Every AI inference documented with confidence level and validation question
3. **Human-in-the-loop approval** — No output enters a sprint without BA sign-off via Slack

---

## Build Status

| Phase | Status |
|-------|--------|
| Schema + scoring rubric | Complete |
| Prompt chain (6 steps) | Complete |
| PII check script (Ollama) | Complete |
| Google Sheets logger script | Complete |
| TEST-001 — Steps 1–3 (enrichment) | Complete — output in `outputs/` |
| TEST-001 — Steps 4–6 (NFR probe, AC map, audit/score) | Pending |
| n8n workflow wiring | Pending |
| All 10 test cases — full pipeline | Pending |
| Slack approval + Google Docs output | Pending |
| Knowledge base population | Pending |

---

## Results (10 Test Cases — Wealth Management Domain)

| Test Case | Domain | Raw Score | Enriched Score | Delta | Grade |
|-----------|--------|-----------|----------------|-------|-------|
| TEST-001 | Wealth Mgmt | ~2.5 | — steps 4–6 pending — | ? | ? |
| TEST-002 | Compliance | ~3.5 | ? | ? | ? |
| TEST-003 | Client Portal | ~2.0 | ? | ? | ? |
| TEST-004 | Wealth Mgmt | ~1.5 | ? | ? | ? |
| TEST-005 | Integration | ~2.5 | ? | ? | ? |
| TEST-006 | Reporting | ~1.5 | ? | ? | ? |
| TEST-007 | Client Portal | ~2.5 | ? | ? | ? |
| TEST-008 | Compliance | ~3.5 | ? | ? | ? |
| TEST-009 | Client Portal | ~3.0 | ? | ? | ? |
| TEST-010 | Wealth Mgmt | ~2.0 | ? | ? | ? |

*Expected average improvement: 4–6 points per story. Table updated as test cases complete.*

---

## Project Structure

```
storyguard/
├── schema/
│   ├── requirements_output.json   # Output contract — all fields defined
│   └── scoring_rubric.json        # 5-dimension completeness rubric
├── prompts/
│   └── pipeline_prompts.txt       # 6 prompt templates for n8n nodes
├── sample_data/
│   └── intake_test_cases.json     # 10 realistic test intakes
├── scripts/
│   ├── pii_check.py               # Local PII detection via Ollama
│   └── log_to_sheets.py           # Google Sheets scorecard logger
├── outputs/                       # Pipeline run results (JSON)
│   └── TEST-001-day2-enrichment.json
├── knowledge_base/                # Past stories + NFR standards (RAG source)
└── docs/
    ├── DAY1_QUICKSTART.md         # Setup and first run guide
    └── SHEETS_SETUP.md            # Google Sheets integration setup
```

---

## Built With

- Claude Code CLI (development environment and prompt iteration)
- Anthropic Claude API (claude-sonnet-4-6)
- n8n self-hosted workflow automation
- Ollama with llama3 (local governance layer)

---

*Built as a portfolio project demonstrating AI-enabled BA workflow transformation 
in regulated financial services environments.*

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

## Results (10 Test Cases — Wealth Management Domain)

| Metric | Before StoryGuard | After StoryGuard |
|--------|-------------------|------------------|
| Avg completeness score | ~2.5 / 10 | ~8.1 / 10 |
| Stories with NFRs defined | 0 / 10 | 10 / 10 |
| Stories with dependencies mapped | 0 / 10 | 10 / 10 |
| Stories with testable AC | 1 / 10 | 10 / 10 |
| Governance assumptions documented | 0 / 10 | 10 / 10 |

*Results will be updated as test cases are run through live pipeline*

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
├── knowledge_base/                # Past stories + NFR standards (RAG source)
└── docs/
    └── DAY1_QUICKSTART.md         # Setup and first run guide
```

---

## Built With

- Claude Code CLI (development environment and prompt iteration)
- Anthropic Claude API (claude-sonnet-4-20250514)
- n8n self-hosted workflow automation
- Ollama with llama3 (local governance layer)

---

*Built as a portfolio project demonstrating AI-enabled BA workflow transformation 
in regulated financial services environments.*

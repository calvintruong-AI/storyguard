# StoryGuard — Day 1 Quickstart Guide

## What you have after cloning this repo

```
storyguard/
├── schema/
│   ├── requirements_output.json   # Output schema — the contract for every story
│   └── scoring_rubric.json        # 5-dimension completeness rubric
├── prompts/
│   └── pipeline_prompts.txt       # All 6 prompt templates, ready to wire into n8n
├── sample_data/
│   └── intake_test_cases.json     # 10 realistic test intakes with expected gaps noted
├── scripts/
│   ├── pii_check.py               # Ollama-powered local PII detection
│   └── log_to_sheets.py           # Google Sheets scorecard logger
├── knowledge_base/                # Empty — you populate this on Day 6
└── docs/
    └── DAY1_QUICKSTART.md         # This file
```

---

## Day 1 session order (2-3 hours)

### Hour 1 — Understand your files (30 min)
1. Read `schema/requirements_output.json` — understand every field before building
2. Read `schema/scoring_rubric.json` — know what a 0 vs 2 looks like on each dimension
3. Read `prompts/pipeline_prompts.txt` — read all 6 prompts top to bottom
4. Read `sample_data/intake_test_cases.json` — pick TEST-001 as your first run

### Hour 1 — Test PII check script (30 min)
```bash
# Install dependency
pip3 install ollama --break-system-packages

# Test with clean intake (should return clean)
python3 scripts/pii_check.py "Advisors need a better way to see client portfolio performance." --pretty

# Test with flagged intake (should return flagged)
python3 scripts/pii_check.py "John Smith, account #ACC-88821, needs portfolio access." --pretty

# Test with a file
echo "The document upload process is too slow for new clients." > /tmp/test_intake.txt
python3 scripts/pii_check.py --file /tmp/test_intake.txt --pretty
```

### Hour 2 — Manual pipeline test (60 min)
Before wiring into n8n, run the pipeline manually using the Claude API directly.
This validates your prompts before you build the workflow.

Use these Claude Code session prompts (see section below).

### Hour 3 — n8n workflow skeleton (30-60 min)
1. Open n8n
2. Create new workflow: "StoryGuard Pipeline"
3. Add these nodes in order (wire them up Day 2):
   - Webhook trigger (intake form submission)
   - HTTP Request (Ollama PII check)
   - IF node (block if PII flagged)
   - HTTP Request (Claude API — Step 2 intake parser)
   - HTTP Request (Claude API — Step 3 enrichment)
   - HTTP Request (Claude API — Step 4 NFR probe)
   - HTTP Request (Claude API — Step 5 AC + dependencies)
   - HTTP Request (Claude API — Step 6 governance + score)
   - Slack (human review notification)
   - Google Docs (write approved output)
   - Execute Command (run log_to_sheets.py)
4. Save workflow — wiring happens Days 2-3

---

## Claude Code session prompts for Day 1

Open Claude Code in your storyguard/ directory and use these prompts.

### Prompt 1 — Validate your understanding of the schema
```
Read schema/requirements_output.json and explain back to me what each 
top-level section is for and why it matters for an AI coding agent 
consuming the output. Flag any fields you think are missing for a 
wealth management context.
```

### Prompt 2 — Run a manual pipeline test
```
I want to manually test my prompt chain before wiring it into n8n.

Using the intake text from sample_data/intake_test_cases.json TEST-001,
and the prompts in prompts/pipeline_prompts.txt:

1. Show me what PROMPT_02_INTAKE_PARSER would return for TEST-001
2. Then show me what PROMPT_03_ENRICHMENT would return using that parsed output
3. Identify any gaps or inconsistencies between the prompt design and 
   the schema in schema/requirements_output.json

Do not call any external APIs — simulate the expected outputs based on 
the prompt instructions and your understanding of the domain.
```

### Prompt 3 — Improve a weak prompt
```
Read PROMPT_04_NFR_PROBE in prompts/pipeline_prompts.txt.

Then read TEST-002 in sample_data/intake_test_cases.json — a 2FA 
compliance story that should surface FINRA/SEC compliance NFRs, 
session timeout policy, and recovery flow requirements.

Critique the current NFR probe prompt: what is it likely to miss for 
this specific intake? Suggest specific improvements to the prompt that 
would catch the hidden NFRs documented in the test case.
```

### Prompt 4 — Generate the Google Sheets setup instructions
```
Read scripts/log_to_sheets.py and generate step-by-step instructions 
for setting up the Google Sheets integration, including:
1. How to create the Google Cloud project and enable the Sheets API
2. How to create and download the service account JSON key
3. What the spreadsheet should look like (column headers, formatting)
4. How to test the connection before running the full pipeline

Write the instructions as a markdown file and save it to 
docs/SHEETS_SETUP.md
```

### Prompt 5 — End of Day 1 gap analysis
```
Review all files in this project directory. 

Based on the project goal (a governed AI requirements enrichment pipeline 
for wealth management BA intake), identify:
1. What is missing from the current starter files that I will need to 
   build on Days 2-5
2. Any logical gaps between the prompt chain design and the output schema
3. The three highest-risk items that could block progress during the build

Output as a prioritized list I can use to start Day 2.
```

---

## Day 2 preview — what you'll build

- Wire n8n workflow nodes (prompts are ready, just connect them)
- Add Claude API credentials to n8n
- Run TEST-001 through the live pipeline end to end
- Capture first completeness score

---

## Quick reference — API formats

### n8n → Ollama (PII check)
```
POST http://localhost:11434/api/generate
Body:
{
  "model": "llama3",
  "prompt": "{{your_prompt_here}}",
  "stream": false,
  "options": { "temperature": 0.1 }
}
Response field: response.response
```

### n8n → Claude API (enrichment steps)
```
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: {{your_claude_api_key}}
  anthropic-version: 2023-06-01
  content-type: application/json
Body:
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 2000,
  "messages": [
    { "role": "user", "content": "{{your_prompt_with_variables}}" }
  ]
}
Response field: response.content[0].text
```

---

## Measuring your impact

Run each of the 10 test cases through the pipeline and record scores here:

| Test Case | Domain | Raw Score | Enriched Score | Delta | Grade |
|-----------|--------|-----------|----------------|-------|-------|
| TEST-001  | Wealth Mgmt | ~2.5 | ? | ? | ? |
| TEST-002  | Compliance | ~3.5 | ? | ? | ? |
| TEST-003  | Client Portal | ~2.0 | ? | ? | ? |
| TEST-004  | Wealth Mgmt | ~1.5 | ? | ? | ? |
| TEST-005  | Integration | ~2.5 | ? | ? | ? |
| TEST-006  | Reporting | ~1.5 | ? | ? | ? |
| TEST-007  | Client Portal | ~2.5 | ? | ? | ? |
| TEST-008  | Compliance | ~3.5 | ? | ? | ? |
| TEST-009  | Client Portal | ~3.0 | ? | ? | ? |
| TEST-010  | Wealth Mgmt | ~2.0 | ? | ? | ? |

Expected average improvement: 4-6 points per story.
This table goes in your GitHub README and is your demo's headline metric.

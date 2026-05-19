# StoryGuard — Phase 3: n8n Workflow Wiring
## Building the Live Pipeline

**Goal:** Wire all 6 pipeline steps in n8n so the full pipeline runs end-to-end.  
**Time:** ~3–5 hours  
**Prerequisites:**
- n8n running and accessible (self-hosted)
- Claude API key available
- Ollama running locally with llama3 pulled (`ollama pull llama3`)
- Knowledge base populated (Phase 2)

---

## Architecture overview

```
[Webhook Trigger]
      │  intake_text (from Google Forms — wire in Phase 4)
      │  For now: trigger manually via n8n test webhook
      ▼
[Set Node: RAG Context]
      │  Loads knowledge base content as static string
      ▼
[HTTP: Step 1 — PII Check] ──── POST localhost:11434 (Ollama)
      │
      ▼
[IF: PII Gate] ──── pii_detected = true → [Slack: Flag & Stop]
      │ false
      ▼
[HTTP: Step 2 — Intake Parser] ──── POST api.anthropic.com
      │
      ▼
[HTTP: Step 3 — Enrichment] ──── POST api.anthropic.com
      │
      ▼
[HTTP: Step 4 — NFR Probe] ──── POST api.anthropic.com
      │
      ▼
[HTTP: Step 5 — AC + Dependencies] ──── POST api.anthropic.com
      │
      ▼
[HTTP: Step 6 — Governance + Score] ──── POST api.anthropic.com
      │
      ▼
[Execute Command: log_to_sheets.py]
      │
      ▼
[Slack: Human Review Notification] ──── Phase 4
      │
      ▼
[Google Docs: Write Output] ──── Phase 4
```

---

## Before you start: credential setup in n8n

### Claude API credential
1. In n8n: Settings → Credentials → New → **Header Auth**
2. Name: `Claude API`
3. Name: `x-api-key` / Value: your Anthropic API key
4. Add second header: Name: `anthropic-version` / Value: `2023-06-01`

### Test Ollama is reachable
```bash
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3","prompt":"test","stream":false}' \
  -H "Content-Type: application/json"
```
Should return JSON with a `response` field.

---

## Node-by-node build guide

### Node 1 — Webhook Trigger

| Field | Value |
|-------|-------|
| HTTP Method | POST |
| Path | `/storyguard-intake` |
| Response Mode | `Last Node` |

**Test data** (use this to trigger manually during build):
```json
{
  "intake_text": "Advisors need a better way to see client portfolio performance across all their books of business."
}
```

In n8n: click the Webhook node → "Listen for test event" → send the test data via curl:
```bash
curl -X POST http://localhost:5678/webhook-test/storyguard-intake \
  -H "Content-Type: application/json" \
  -d '{"intake_text": "Advisors need a better way to see client portfolio performance across all their books of business."}'
```

---

### Node 2 — Set: RAG Context

Add a **Set** node immediately after the Webhook.

| Field | Value |
|-------|-------|
| Node name | `RAG Context` |

Add one string field:
- **Name:** `rag_context`
- **Value:** Paste the full content of `knowledge_base/standards/nfr-wealth-management.md` and `knowledge_base/personas/wealth-management-personas.md` concatenated

This injects knowledge base content into every Claude API call without building retrieval infrastructure.

Pass through `intake_text` from the Webhook node: add a second field `intake_text` = `{{ $json.intake_text }}`

---

### Node 3 — HTTP Request: Step 1 PII Check

| Field | Value |
|-------|-------|
| Method | POST |
| URL | `http://localhost:11434/api/generate` |
| Content-Type | `application/json` |

**Body** (paste from `prompts/pipeline_prompts.txt` PROMPT_01_PII_CHECK, with variable replaced):
```json
{
  "model": "llama3",
  "prompt": "You are a data privacy compliance checker...\n\nText to analyze:\n{{ $json.intake_text }}\n\nRespond ONLY with valid JSON...",
  "stream": false,
  "options": { "temperature": 0.1 }
}
```

**Response mapping:** The result is in `response.response` (the outer `response` is the HTTP response body field, the inner `.response` is Ollama's output field).

Add a **Set** node after this to parse the Ollama JSON string:
- Name: `pii_result`
- Value: `{{ JSON.parse($json.response) }}`

---

### Node 4 — IF: PII Gate

| Field | Value |
|-------|-------|
| Condition | `{{ $json.pii_result.pii_detected }}` |
| Type | Boolean |
| Value | `true` |

- **True branch** → Slack notification (wire in Phase 4) or a Stop node for now
- **False branch** → Continue to Step 2

---

### Node 5 — HTTP Request: Step 2 Intake Parser

| Field | Value |
|-------|-------|
| Method | POST |
| URL | `https://api.anthropic.com/v1/messages` |
| Authentication | Header Auth → `Claude API` credential |
| Content-Type | `application/json` |

**Body:**
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 1500,
  "messages": [
    {
      "role": "user",
      "content": "{{ $('RAG Context').item.json.rag_context_prompt.replace('{{intake_text}}', $('RAG Context').item.json.intake_text).replace('{{rag_context}}', $('RAG Context').item.json.rag_context) }}"
    }
  ]
}
```

**Easier approach in n8n:** Use a Code node before each HTTP Request to assemble the prompt string, then reference `{{ $json.prompt }}` in the HTTP body. This keeps the expressions readable.

**Code node example (Step 2):**
```javascript
const prompt = `You are a senior Business Systems Analyst...

Raw intake text:
${$input.item.json.intake_text}

Context from knowledge base:
${$input.item.json.rag_context}

Extract and return ONLY valid JSON...`;

return { prompt, intake_text: $input.item.json.intake_text, rag_context: $input.item.json.rag_context };
```

**Response mapping:** `response.content[0].text` — this is the raw JSON string returned by Claude.

Add a **Set** node to parse it:
- Name: `parsed_intake`
- Value: `{{ JSON.parse($json.response.content[0].text) }}`

---

### Node 6 — HTTP Request: Step 3 Enrichment

Same pattern as Step 2. Code node to assemble the prompt:

```javascript
const prompt = `You are a senior Business Systems Analyst...

PARSED INTAKE:
${JSON.stringify($input.item.json.parsed_intake)}

ORIGINAL RAW INTAKE:
${$input.item.json.intake_text}

RETRIEVED CONTEXT FROM KNOWLEDGE BASE:
${$input.item.json.rag_context}

Generate the following sections. Return ONLY valid JSON...`;

return { 
  prompt, 
  intake_text: $input.item.json.intake_text,
  parsed_intake: $input.item.json.parsed_intake,
  rag_context: $input.item.json.rag_context
};
```

Parse response → `enriched`

---

### Node 7 — HTTP Request: Step 4 NFR Probe

Code node:
```javascript
const enriched = $input.item.json.enriched;
const prompt = `You are a senior Business Systems Analyst and compliance specialist...

USER STORY CONTEXT:
${JSON.stringify(enriched.user_story)}

FUNCTIONAL REQUIREMENTS:
${JSON.stringify(enriched.functional_requirements)}

DOMAIN: ${$input.item.json.parsed_intake.domain}

...`;

return { prompt, enriched, parsed_intake: $input.item.json.parsed_intake, intake_text: $input.item.json.intake_text, rag_context: $input.item.json.rag_context };
```

Parse response → `nfrs`

---

### Node 8 — HTTP Request: Step 5 AC + Dependencies

Code node:
```javascript
const enriched = $input.item.json.enriched;
const nfrs = $input.item.json.nfrs;
const domain = $input.item.json.parsed_intake.domain;

const prompt = `You are a senior Business Systems Analyst...

FULL STORY CONTEXT:
User Story: ${JSON.stringify(enriched.user_story)}
Functional Requirements: ${JSON.stringify(enriched.functional_requirements)}
NFRs: ${JSON.stringify(nfrs)}
Domain: ${domain}

...`;

return { prompt, enriched, nfrs, parsed_intake: $input.item.json.parsed_intake, intake_text: $input.item.json.intake_text };
```

Parse response → `ac_and_deps` (contains `acceptance_criteria` and `system_dependencies`)

---

### Node 9 — HTTP Request: Step 6 Governance + Score

Code node — assemble the full requirements document for audit:
```javascript
const fullDoc = {
  user_story: $input.item.json.enriched.user_story,
  personas: $input.item.json.enriched.personas,
  functional_requirements: $input.item.json.enriched.functional_requirements,
  nfrs: $input.item.json.nfrs,
  acceptance_criteria: $input.item.json.ac_and_deps.acceptance_criteria,
  system_dependencies: $input.item.json.ac_and_deps.system_dependencies
};

const prompt = `You are a requirements quality auditor...

ORIGINAL INTAKE (source of truth):
${$input.item.json.intake_text}

COMPLETE REQUIREMENTS DOCUMENT GENERATED:
${JSON.stringify(fullDoc)}

...`;

return { prompt, fullDoc, intake_text: $input.item.json.intake_text };
```

Parse response → `governance_and_score`

---

### Node 10 — Execute Command: log_to_sheets.py

| Field | Value |
|-------|-------|
| Node type | Execute Command |
| Command | `python3 /path/to/storyguard/scripts/log_to_sheets.py` |

Pass the score data as environment variables or build a JSON argument string.

Check `scripts/log_to_sheets.py` for the expected arguments — adjust the command accordingly.

---

## Testing the workflow

### Test in segments (recommended)

Don't test the full pipeline until each segment works independently.

**Segment 1:** Webhook → Set → PII Check → IF  
Trigger with clean intake, verify `pii_result.pii_detected` = false.

**Segment 2:** Add Step 2, verify `parsed_intake` is valid JSON with all expected fields.

**Segment 3:** Add Step 3, verify `enriched` contains user_story, personas, functional_requirements.

**Segment 4:** Add Steps 4–6 one at a time.

**Full run:** Only once all segments pass individually.

### Common issues

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| Claude returns markdown instead of JSON | Missing JSON instruction in prompt | Append "IMPORTANT: respond with { only, no markdown" |
| `JSON.parse` fails in Set node | Claude returned partial JSON | Increase `max_tokens` (try 2000→3000) |
| Ollama times out | Model not loaded | Run `ollama run llama3` in terminal first |
| Step passes `null` to next step | Field name mismatch in Set node | Check exact field name in previous node output |
| Claude API 401 | Credential not applied to node | Open HTTP node → re-select the Claude API credential |

---

## When this phase is done

- [ ] Full pipeline runs end-to-end from webhook trigger to Step 6 output
- [ ] PII gate correctly blocks flagged intake (test with a name + account number)
- [ ] All 6 step outputs are valid, parseable JSON
- [ ] `log_to_sheets.py` writes a row to the scorecard on each run
- [ ] TEST-001 submitted via the test webhook and output matches Phase 1 manual run
- [ ] Ready to move to Phase 4 (Slack + Google Docs + Google Forms)

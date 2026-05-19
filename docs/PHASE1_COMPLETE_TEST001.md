# StoryGuard — Phase 1: Complete TEST-001 Pipeline
## Steps 4–6: NFR Probe, AC + Dependency Map, Governance Audit

**Goal:** Validate the full 6-step prompt chain before wiring into n8n.  
**Time:** ~1 hour  
**Prerequisite:** `outputs/TEST-001-day2-enrichment.json` exists (Steps 1–3 complete)

---

## What you're doing

Steps 1–3 produced an enriched requirements document for TEST-001. Before building the n8n
workflow, manually run Steps 4–6 so you know the prompts produce valid, useful output.
This catches prompt problems cheaply — fixing a prompt in a text file is faster than
debugging a broken n8n node.

---

## Step 1 — Extract inputs from the existing output

Open `outputs/TEST-001-day2-enrichment.json` and identify these fields — you'll
paste them into the prompts below:

- `enriched.user_story` → used in Steps 4 and 5 as `{{user_story}}`
- `enriched.functional_requirements` → used in Steps 4 and 5 as `{{functional_requirements}}`
- `enriched.personas` → context for Step 5
- `parsed.domain` → used in Steps 4 and 5 as `{{domain}}`
- Original intake text from `sample_data/intake_test_cases.json` TEST-001 → used in Step 6

```bash
# View the existing output
cat outputs/TEST-001-day2-enrichment.json | python3 -m json.tool | head -60
```

---

## Step 2 — Run Step 4: NFR Probe

Open Claude Code in your storyguard/ directory and use this prompt:

```
Read outputs/TEST-001-day2-enrichment.json.
Read prompts/pipeline_prompts.txt — specifically PROMPT_04_NFR_PROBE.

Fill in the prompt variables using the TEST-001 enrichment output:
- {{user_story}} = the user_story object from the enriched section
- {{functional_requirements}} = the functional_requirements array
- {{domain}} = the domain field from the parsed section

Execute PROMPT_04_NFR_PROBE against the TEST-001 data and return the result
as valid JSON matching the expected output schema.

Do not invent requirements — mark anything not derivable from the intake
as "missing" with a specific stakeholder question.
```

**Expected output structure:**
```json
{
  "non_functional_requirements": {
    "performance": { "status": "...", "requirement": "...", "source": "..." },
    "security": { "status": "...", "requirement": "...", "source": "..." },
    "compliance": { "status": "...", "requirement": "...", "regulations_flagged": [], "source": "..." },
    "reliability": { "status": "...", "requirement": "...", "source": "..." },
    "auditability": { "status": "...", "requirement": "...", "source": "..." }
  }
}
```

Save this output — you'll need it for Step 5.

---

## Step 3 — Run Step 5: AC + Dependency Mapper

```
Read outputs/TEST-001-day2-enrichment.json.
Read prompts/pipeline_prompts.txt — specifically PROMPT_05_AC_AND_DEPENDENCIES.

Fill in the prompt variables:
- {{user_story}} = user_story from the enriched section
- {{functional_requirements}} = functional_requirements array
- {{nfrs}} = the NFR JSON output you just generated in Step 4
- {{domain}} = domain from parsed section

Execute PROMPT_05_AC_AND_DEPENDENCIES and return valid JSON.

Rules:
- Minimum 4 acceptance criteria: 2 happy path, 1 edge case, 1 compliance
- Every "then" statement must be specific and binary — it passes or it fails
- Map at minimum 2 upstream and 1 downstream system dependency
```

**Expected output structure:**
```json
{
  "acceptance_criteria": [
    { "id": "AC-001", "given": "...", "when": "...", "then": "...", "test_type": "...", "negative_test": "..." }
  ],
  "system_dependencies": {
    "upstream": [...],
    "downstream": [...],
    "external_integrations": [...],
    "data_sources": [...]
  }
}
```

Save this output — you'll need it for Step 6.

---

## Step 4 — Run Step 6: Governance Audit + Quality Score

```
Read outputs/TEST-001-day2-enrichment.json.
Read prompts/pipeline_prompts.txt — specifically PROMPT_06_GOVERNANCE_AND_SCORE.
Read sample_data/intake_test_cases.json — get the original intake text for TEST-001.

Fill in the prompt variables:
- {{intake_text}} = the original raw intake text from TEST-001
- {{full_requirements_document}} = the complete assembled document:
    - parsed intake (from enrichment output)
    - enriched user story, personas, functional requirements
    - NFR output from Step 4
    - Acceptance criteria + dependencies from Step 5

Execute PROMPT_06_GOVERNANCE_AND_SCORE.

Be strict on scoring. Use the rubric thresholds exactly.
A "needs_review" score on a first run is expected and useful.
```

**Expected output structure:**
```json
{
  "governance": {
    "assumptions": [...],
    "hallucination_flags": [...],
    "missing_information": [...],
    "human_review_required": true
  },
  "quality_score": {
    "dimension_scores": {
      "story_clarity": 0,
      "nfr_coverage": 0,
      "dependency_identification": 0,
      "acceptance_criteria_testability": 0,
      "assumption_transparency": 0
    },
    "total_score": 0,
    "max_score": 10,
    "grade": "sprint_ready | needs_review | incomplete | blocked",
    "ready_for_sprint": false,
    "improvement_suggestions": [...]
  }
}
```

---

## Step 5 — Assemble complete output file

```
I have all 6 steps of output for TEST-001. Assemble them into a single JSON file
with this structure:

{
  "test_case_id": "TEST-001",
  "pipeline_version": "1.0.0",
  "run_date": "YYYY-MM-DD",
  "original_intake": "...",
  "parsed": { ... },           // Step 2 output
  "enriched": { ... },         // Step 3 output
  "nfrs": { ... },             // Step 4 output
  "acceptance_criteria": [...], // Step 5 output
  "system_dependencies": { ... }, // Step 5 output
  "governance": { ... },       // Step 6 output
  "quality_score": { ... }     // Step 6 output
}

Save the assembled file to outputs/TEST-001-complete.json
```

---

## Step 6 — Record the score

Once you have `quality_score.total_score` from Step 6:

1. Update the Results table in `README.md` — fill in TEST-001's Enriched Score and Delta
2. Note any `improvement_suggestions` for future prompt iteration

```bash
# Verify the output file exists and is valid JSON
cat outputs/TEST-001-complete.json | python3 -m json.tool > /dev/null && echo "Valid JSON"
```

---

## What a good result looks like

| Signal | What it means |
|--------|--------------|
| Total score 6–8 | First run is normal — prompts are working, polish needed |
| `hallucination_flags` present | Expected — this is the governance layer doing its job |
| `missing_information` list has items | Good — these become the BA's stakeholder questions |
| `grade: needs_review` | Expected for a well-scoped story on first pass |
| JSON parse errors | Prompt needs adjustment — add "return ONLY valid JSON" reinforcement |

---

## Troubleshooting

**Prompt returns markdown instead of JSON**  
Add to the end of the failing prompt: `IMPORTANT: Your response must begin with { and end with }. No other text.`

**NFR probe misses compliance requirements**  
The domain is wealth_management — explicitly add to the prompt: "This story is in a FINRA/SEC regulated environment. Compliance and auditability NFRs are required unless explicitly not applicable."

**Score seems inflated**  
Re-run Step 6 and add: "Score conservatively. If you are unsure between two scores, choose the lower one."

---

## When this phase is done

- [ ] `outputs/TEST-001-complete.json` saved and valid
- [ ] Total score recorded in README Results table
- [ ] No JSON parse errors in any step output
- [ ] At least one `improvement_suggestion` noted for future prompt iteration
- [ ] Ready to move to Phase 2 (knowledge base) or Phase 3 (n8n wiring)

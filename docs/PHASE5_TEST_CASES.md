# StoryGuard — Phase 5: Running All 10 Test Cases
## Generating the Demo Scorecard

**Goal:** Run all 10 test cases through the live pipeline and populate the README results table.  
**Time:** ~3–4 hours  
**Prerequisite:** Phase 3 complete (pipeline runs end-to-end). Phase 4 optional but recommended.

---

## Why this phase matters for the portfolio

The headline metric for StoryGuard is the before/after quality score across 10 realistic
wealth management stories. Without this table populated, the project demonstrates
infrastructure — with it, it demonstrates measurable impact.

The target: average enriched score of 7–9/10 across all cases vs. raw scores of 1.5–3.5.
That delta (4–6 points per story) is the portfolio story.

---

## Preparation

### Review the test cases

Open `sample_data/intake_test_cases.json` and read all 10 cases before starting.
Each has a raw intake and noted expected gaps. Note which cases you expect to score
highest and lowest — this is useful context when reviewing results.

### Set up a results log

Create a local scratch file to track results as you go:

```bash
touch outputs/test_run_log.md
```

Format:
```markdown
# Test Run Log

| Test Case | Domain | Raw Score | Enriched Score | Total Score | Grade | Notes |
|-----------|--------|-----------|----------------|-------------|-------|-------|
| TEST-001 | Wealth Mgmt | ~2.5 | ? | ? | ? | |
```

### Decide: manual or live pipeline

**Manual (Steps via Claude Code):** Faster to run, easier to debug prompt issues.
Recommended if n8n is still being tuned.

**Live pipeline (n8n):** The real end-to-end test. Use this once n8n is stable.

For this phase, run at least TEST-002 through TEST-005 live. The rest can be manual
if time is short.

---

## Running each test case

### Via n8n (live pipeline)

Submit each test case intake text to the intake webhook:

```bash
# TEST-002
curl -X POST http://localhost:5678/webhook/storyguard-intake \
  -H "Content-Type: application/json" \
  -d '{
    "intake_text": "[paste intake_text from sample_data/intake_test_cases.json for TEST-002]",
    "test_case_id": "TEST-002"
  }'
```

Capture the Step 6 output JSON and save to `outputs/TEST-00X-complete.json`.

### Via Claude Code (manual)

```
Read sample_data/intake_test_cases.json — get the intake_text for TEST-002.
Read outputs/TEST-001-complete.json as a reference for the expected output structure.
Read prompts/pipeline_prompts.txt.

Run TEST-002 through the full 6-step pipeline:
1. PROMPT_01: PII check (skip if intake is clearly clean — note if skipped)
2. PROMPT_02: Intake parser (use knowledge base content as rag_context)
3. PROMPT_03: Enrichment
4. PROMPT_04: NFR probe
5. PROMPT_05: AC + dependencies
6. PROMPT_06: Governance audit + score

Use the knowledge base files in knowledge_base/ as rag_context for Steps 2–3.

Save the assembled output to outputs/TEST-002-complete.json.
Report the total_score, grade, and dimension_scores.
```

---

## Test case run order and what to watch for

Run in this order — easier cases first, then harder ones.

### TEST-001 — Wealth Mgmt: Portfolio Performance Reporting
Already partially complete. If Phase 1 is done, this is your baseline.
- Watch for: performance NFRs (report timing), auditability (who viewed which report)

### TEST-002 — Compliance: Two-Factor Authentication
Higher raw score (~3.5) because the intake has more specificity. Good test for compliance NFRs.
- Watch for: FINRA/SEC compliance flags, session timeout requirements, recovery flow

### TEST-003 — Client Portal: Document Upload
Lower raw score (~2.0). Vague intake. Good test for vagueness detection.
- Watch for: file size/type restrictions, virus scanning, access controls

### TEST-004 — Wealth Mgmt: Low-Specificity Story
Intentionally weak intake (~1.5 raw). The pipeline's enrichment lift should be highest here.
- Watch for: how many assumptions are flagged, whether grade comes back "needs_review"

### TEST-005 — Integration: Custodian Data Feed
Integration story — tests system dependency mapping (Step 5).
- Watch for: upstream/downstream dependency count, data reconciliation NFRs

### TEST-006 — Reporting: Portfolio Statement Generation
Regulatory output story — tests compliance and reliability NFRs.
- Watch for: SEC 17a-4 flags, statement formatting requirements, scheduled delivery

### TEST-007 — Client Portal: Secure Messaging
Communication story — tests Regulation S-P privacy flags.
- Watch for: message retention policy, encryption requirements, access controls

### TEST-008 — Compliance: Trade Surveillance
Compliance-heavy story (~3.5 raw). Tests whether Step 4 catches FINRA supervisory requirements.
- Watch for: FINRA Rule 3110 flags, alert threshold definitions, escalation workflow

### TEST-009 — Client Portal: Account Opening Workflow
Multi-step workflow story. Tests AC coverage (Step 5) — happy path, edge cases, error handling.
- Watch for: AC count (should be 5+), edge cases for incomplete submissions

### TEST-010 — Wealth Mgmt: Rebalancing Request
Transaction story — tests reliability and auditability NFRs for financial operations.
- Watch for: audit trail for the rebalancing action, rollback requirements

---

## Scoring and recording results

After each test case, extract from the Step 6 output:

```bash
# Quick score extraction
cat outputs/TEST-00X-complete.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
score = data['quality_score']
print(f\"Total: {score['total_score']}/10 | Grade: {score['grade']}\")
print(f\"  Story Clarity: {score['dimension_scores']['story_clarity']}/2\")
print(f\"  NFR Coverage: {score['dimension_scores']['nfr_coverage']}/2\")
print(f\"  Dependencies: {score['dimension_scores']['dependency_identification']}/2\")
print(f\"  AC Testability: {score['dimension_scores']['acceptance_criteria_testability']}/2\")
print(f\"  Assumption Transparency: {score['dimension_scores']['assumption_transparency']}/2\")
"
```

Record in `outputs/test_run_log.md` after each run.

---

## Prompt iteration mid-run

If you see consistent patterns across multiple cases, fix the prompt before continuing.

**Common patterns and fixes:**

| Pattern | Likely cause | Fix |
|---------|-------------|-----|
| NFR coverage consistently 1/2 | Step 4 not covering all 5 NFR categories | Add explicit instruction: "All 5 NFR categories must have a status, even if not_applicable" |
| AC testability consistently 1/2 | "Then" statements too vague | Add to Step 5: "Every 'then' must name a specific, measurable outcome. Reject generic statements like 'the system responds correctly'." |
| Assumption transparency 0/2 | Step 6 not extracting assumptions | Check that full_requirements_document is being passed correctly — truncation will cause this |
| Scores seem inflated | Step 6 scoring generously | Add to Step 6: "If you are uncertain between two scores, choose the lower one. Err toward strictness." |
| JSON parse errors | Claude returning markdown | Add to failing prompt: "Your response MUST start with { and end with }. No markdown, no explanation." |

Commit prompt changes to `prompts/pipeline_prompts.txt` with a note on which test case triggered the change.

---

## Updating the README

Once all 10 cases are complete, update the Results table in `README.md`:

```
Read outputs/test_run_log.md.
Update the Results table in README.md with the actual scores for all 10 test cases.
Calculate the average raw score and average enriched score.
Add a summary line below the table: "Average improvement: X.X points per story"
Also update the Build Status table — mark "All 10 test cases — full pipeline" as Complete.
```

---

## What a strong demo result looks like

| Metric | Target |
|--------|--------|
| Average enriched score | 7.0+ / 10 |
| Average raw score | ~2.5 / 10 |
| Average delta | 4.5+ points |
| Cases graded "sprint_ready" | 2+ |
| Cases graded "needs_review" | 5–7 |
| Cases graded "incomplete" | 0–2 (only the weakest intakes) |

If your enriched scores are clustering below 6, the most common fix is NFR coverage —
Step 4 is often the weakest link because financial services NFRs require specific
regulatory knowledge that the prompt needs to explicitly prompt for.

---

## Final checklist

- [ ] All 10 test cases run (live pipeline or manual)
- [ ] All outputs saved to `outputs/TEST-00X-complete.json`
- [ ] README Results table fully populated with actual scores
- [ ] `log_to_sheets.py` has written all 10 rows to the scorecard
- [ ] Average improvement calculated and noted in README
- [ ] Build Status table updated to reflect complete pipeline
- [ ] Any prompt improvements committed to `prompts/pipeline_prompts.txt`
- [ ] Project is demo-ready

# StoryGuard — Phase 4: Slack, Google Docs, and Google Forms
## Completing the Human-in-the-Loop and Output Layer

**Goal:** Wire the approval workflow and output delivery so the pipeline is fully operational.  
**Time:** ~2–3 hours  
**Prerequisite:** Phase 3 complete — full pipeline runs end-to-end in n8n through Step 6

---

## What you're adding

Three integrations that complete the production loop:

1. **Slack** — Human review notification after Step 6. BA approves or rejects via Slack.
2. **Google Docs** — Write the approved requirements document to a formatted Docs file.
3. **Google Forms** — Replace the manual webhook trigger with a real intake form.

Do them in this order. Slack first — it's the simplest and it closes the loop.

---

## Part 1 — Slack Integration (~45 minutes)

### What it does
After Step 6 scores the document, n8n sends a Slack message to the BA review channel
with the key details and an Approve/Reject prompt. Only approved stories proceed to
Google Docs output.

### Step 1.1 — Create a Slack app

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → "Create New App" → "From scratch"
2. Name: `StoryGuard` / Workspace: your workspace
3. Under **OAuth & Permissions** → **Scopes** → Bot Token Scopes, add:
   - `chat:write`
   - `chat:write.public`
4. Click "Install to Workspace" → copy the **Bot User OAuth Token** (`xoxb-...`)

### Step 1.2 — Add Slack credential in n8n

1. n8n → Settings → Credentials → New → **Slack API**
2. Name: `StoryGuard Slack`
3. Access Token: paste the `xoxb-...` token

### Step 1.3 — Create the review channel

In Slack, create a channel `#storyguard-review` (or use an existing review channel).
Invite the StoryGuard bot: `/invite @StoryGuard`

### Step 1.4 — Add Slack node in n8n

After the `log_to_sheets.py` Execute Command node, add a **Slack** node:

| Field | Value |
|-------|-------|
| Credential | StoryGuard Slack |
| Resource | Message |
| Operation | Post |
| Channel | `#storyguard-review` |

**Message text** (Code node to assemble, then reference `{{ $json.slack_message }}`):

```javascript
const score = $input.item.json.governance_and_score.quality_score;
const story = $input.item.json.fullDoc.user_story;
const grade = score.grade.toUpperCase().replace('_', ' ');

const message = `*StoryGuard — New Story Ready for Review*

*Story:* ${story.as_a} | ${story.i_want}
*Domain:* ${$input.item.json.parsed_intake?.domain || 'unknown'}

*Quality Score:* ${score.total_score}/10 — ${grade}
*Dimensions:*
  • Story Clarity: ${score.dimension_scores.story_clarity}/2
  • NFR Coverage: ${score.dimension_scores.nfr_coverage}/2
  • Dependencies: ${score.dimension_scores.dependency_identification}/2
  • AC Testability: ${score.dimension_scores.acceptance_criteria_testability}/2
  • Assumption Transparency: ${score.dimension_scores.assumption_transparency}/2

*Open questions for stakeholder:* ${$input.item.json.governance_and_score.governance.missing_information?.length || 0} items

*Action required:* Review the full document and reply with ✅ to approve or ❌ to reject.`;

return { slack_message: message };
```

### Step 1.5 — Handle the approval

**Simplest approach (no Slack interactivity required):**  
The Slack message asks the BA to manually trigger the "write to Google Docs" step
by hitting a second n8n webhook (e.g., `POST /storyguard-approve?run_id=XXX`).

**More complete approach:**  
Use Slack's Block Kit with button actions and a separate n8n webhook to handle
the button click. This requires setting up a Slack Request URL in your app settings
pointing to your n8n instance. Only worth the effort if your n8n is publicly reachable.

For now: manual approval webhook is sufficient for portfolio demonstration.

---

## Part 2 — Google Docs Integration (~60 minutes)

### What it does
Writes the approved requirements document to a formatted Google Doc.
Each approved story gets its own Doc in a designated Google Drive folder.

### Step 2.1 — Create Google Cloud OAuth credentials

If you already completed `docs/SHEETS_SETUP.md`, you have a service account.
For Google Docs, you need the **Google Docs API** enabled on the same project.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select your existing StoryGuard project
3. **APIs & Services** → **Library** → search "Google Docs API" → Enable
4. Your existing service account JSON key works — no new key needed

### Step 2.2 — Create a template folder in Google Drive

1. Create a folder in Google Drive: `StoryGuard / Approved Requirements`
2. Share it with your service account email (the one from your JSON key — ends in `@...gserviceaccount.com`) as Editor

### Step 2.3 — Add Google Docs credential in n8n

1. n8n → Credentials → New → **Google Docs**
2. Name: `StoryGuard Google Docs`
3. Auth type: Service Account
4. Paste your service account JSON

### Step 2.4 — Add a Code node to format the document content

```javascript
const story = $input.item.json.fullDoc.user_story;
const enriched = $input.item.json.fullDoc;
const score = $input.item.json.governance_and_score.quality_score;
const gov = $input.item.json.governance_and_score.governance;

const docTitle = `StoryGuard — ${story.as_a}: ${story.i_want.substring(0, 50)}`;

const docBody = `STORYGUARD REQUIREMENTS DOCUMENT
Generated: ${new Date().toISOString()}
Quality Score: ${score.total_score}/10 (${score.grade})

═══════════════════════════════════════
USER STORY
═══════════════════════════════════════
As a: ${story.as_a}
I want: ${story.i_want}
So that: ${story.so_that}
Business Value: ${story.business_value}

═══════════════════════════════════════
PERSONAS
═══════════════════════════════════════
${enriched.personas.map(p => `• ${p.role} (${p.interaction_type})\n  ${p.needs}`).join('\n\n')}

═══════════════════════════════════════
FUNCTIONAL REQUIREMENTS
═══════════════════════════════════════
${enriched.functional_requirements.map(r => `${r.id}: ${r.requirement}\n  Source: ${r.source}`).join('\n\n')}

═══════════════════════════════════════
NON-FUNCTIONAL REQUIREMENTS
═══════════════════════════════════════
${Object.entries(enriched.nfrs.non_functional_requirements).map(([k, v]) => `${k.toUpperCase()} [${v.status}]\n  ${v.requirement}`).join('\n\n')}

═══════════════════════════════════════
ACCEPTANCE CRITERIA
═══════════════════════════════════════
${enriched.acceptance_criteria.map(ac => `${ac.id} [${ac.test_type}]\n  Given: ${ac.given}\n  When: ${ac.when}\n  Then: ${ac.then}`).join('\n\n')}

═══════════════════════════════════════
GOVERNANCE AUDIT
═══════════════════════════════════════
Assumptions: ${gov.assumptions?.length || 0}
${gov.assumptions?.map(a => `• ${a.assumption} (confidence: ${a.confidence})\n  Validate: ${a.validation_needed}`).join('\n') || 'None'}

Open Questions for Stakeholder:
${gov.missing_information?.map(m => `• ${m.field}: ${m.question_for_stakeholder}`).join('\n') || 'None'}

═══════════════════════════════════════
QUALITY SCORE DETAIL
═══════════════════════════════════════
${Object.entries(score.dimension_scores).map(([k, v]) => `${k}: ${v}/2`).join('\n')}
Total: ${score.total_score}/10
Grade: ${score.grade}

Improvement suggestions:
${score.improvement_suggestions?.map(s => `• ${s}`).join('\n') || 'None'}`;

return { docTitle, docBody };
```

### Step 2.5 — Add Google Docs node

| Field | Value |
|-------|-------|
| Resource | Document |
| Operation | Create |
| Title | `{{ $json.docTitle }}` |

After creation, use a second Google Docs node to **Append Text** with `{{ $json.docBody }}`.

Note the returned `documentId` — store it in your Sheets logger as a link back to the Doc.

---

## Part 3 — Google Forms Intake Trigger (~30 minutes)

### What it does
Replaces the manual webhook trigger with a real form. BAs submit intake requests
through Google Forms, which fires the n8n webhook automatically.

### Step 3.1 — Create the intake form

1. Go to [forms.google.com](https://forms.google.com) → Blank form
2. Title: `StoryGuard — Story Intake`
3. Add questions:
   - **Intake Request** (Paragraph) — *Required* — "Describe the business need in 1–3 sentences"
   - **Submitter Name** (Short answer) — *Required*
   - **Priority** (Multiple choice) — Low / Medium / High
   - **Target Sprint** (Short answer) — Optional

### Step 3.2 — Connect Forms to n8n

**Option A — Zapier/Make (simplest):**  
Use Zapier or Make to catch the Google Form submission and POST to your n8n webhook.
Form response → Webhook POST → n8n.

**Option B — Google Apps Script (free, no third party):**

In your Google Form → three-dot menu → **Script editor**. Add:

```javascript
function onFormSubmit(e) {
  const intake = e.values[1]; // adjust index to match your form field order
  const submitter = e.values[2];
  
  const payload = {
    intake_text: intake,
    submitter: submitter,
    timestamp: new Date().toISOString()
  };
  
  UrlFetchApp.fetch('https://YOUR-N8N-URL/webhook/storyguard-intake', {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  });
}
```

In Apps Script: Triggers → Add Trigger → `onFormSubmit` → Form submit.

**Note:** Your n8n instance must be reachable from the internet for Option B.
If it's on localhost only, use Option A (Zapier/Make as relay) or run n8n with
ngrok during testing: `ngrok http 5678`.

### Step 3.3 — Update the Webhook node in n8n

Change the Webhook path from `/storyguard-intake` to match your configured URL,
and update the field mapping to read `intake_text` from the form payload.

---

## Testing the complete loop

1. Submit the intake form with a test request
2. Verify n8n receives the webhook and the pipeline starts
3. Confirm the Slack message arrives in `#storyguard-review` with correct score
4. Manually trigger the approval webhook
5. Verify the Google Doc is created in the correct Drive folder
6. Verify the Sheets logger row includes the Doc link

---

## When this phase is done

- [ ] Slack message sent on every successful pipeline run
- [ ] Slack message includes total score, grade, and open questions count
- [ ] Google Doc created on approval with all 6 pipeline sections
- [ ] Google Forms submission triggers the n8n webhook
- [ ] End-to-end test: form → pipeline → Slack → approve → Google Doc
- [ ] Ready to move to Phase 5 (run all 10 test cases)

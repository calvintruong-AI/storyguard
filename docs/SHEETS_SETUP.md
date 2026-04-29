# StoryGuard — Google Sheets Integration Setup

This guide sets up the scorecard logger so each pipeline run appends a row to your
Google Sheet automatically. Covers GCP project creation, service account credentials,
spreadsheet structure, and connection testing.

---

## Prerequisites

- A Google account with access to Google Drive
- Python 3 with pip available
- The `storyguard/` project directory cloned locally

---

## Step 1 — Install Python dependencies

```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client
```

---

## Step 2 — Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top left) → **New Project**
3. Name it `storyguard` → **Create**
4. Make sure the new project is selected in the dropdown

---

## Step 3 — Enable the Google Sheets API

1. In the left menu go to **APIs & Services → Library**
2. Search for **Google Sheets API**
3. Click it → **Enable**

---

## Step 4 — Create a service account

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → Service Account**
3. Name: `storyguard-logger` → **Create and Continue**
4. Role: **Editor** → **Continue** → **Done**
5. Click the new service account in the list
6. Go to the **Keys** tab → **Add Key → Create new key → JSON**
7. Download the JSON file

---

## Step 5 — Save the credentials file

Create the config directory and save the key:

```bash
mkdir -p /home/calvin/projects/storyguard/config
mv ~/Downloads/your-key-file.json /home/calvin/projects/storyguard/config/google_service_account.json
```

Make sure `config/` is in `.gitignore` — it already is if you used the provided `.gitignore`.

---

## Step 6 — Create the Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) → **Blank**
2. Rename the sheet tab (bottom) to exactly: `StoryGuard Scorecard`
3. The script will write headers automatically on first run — do not add them manually
4. Copy the Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
   ```

---

## Step 7 — Share the sheet with the service account

1. Open the downloaded JSON key file and copy the `client_email` value
   (looks like `storyguard-logger@your-project.iam.gserviceaccount.com`)
2. In your Google Sheet click **Share**
3. Paste the service account email → set role to **Editor** → **Send**

---

## Step 8 — Configure the script

Open `scripts/log_to_sheets.py` and update the two config values at the top:

```python
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"   # ← paste your Sheet ID here
SHEET_TAB_NAME = "StoryGuard Scorecard"  # ← must match the tab name exactly
```

---

## Step 9 — Test the connection

Run the logger against the TEST-001 enrichment output:

```bash
cd /home/calvin/projects/storyguard

python3 scripts/log_to_sheets.py \
  --file outputs/TEST-001-day2-enrichment.json \
  --raw-score 2.5 \
  --pretty
```

Expected output on success:
```json
{
  "success": true,
  "story_id": "SG-2025-001",
  "score": 0,
  "grade": "",
  "rows_appended": 1
}
```

> Note: `score` and `grade` will be 0 / empty until Steps 4–6 populate the
> `quality_score` block in the output JSON.

Open your Google Sheet — row 1 should now contain the column headers and row 2
your first data row.

---

## Spreadsheet column layout

The script writes 21 columns in this order:

| # | Column | Source |
|---|--------|--------|
| A | Story ID | `metadata.story_id` |
| B | Timestamp | `metadata.generated_at` |
| C | Domain | `metadata.domain` |
| D | Raw Intake (truncated) | `metadata.intake_text` (120 chars) |
| E | Raw Score (before) | passed via `--raw-score` flag |
| F | Enriched Score (after) | `quality_score.total_score` |
| G | Score Delta | F − E |
| H | Grade | `quality_score.grade` |
| I | Sprint Ready | `quality_score.ready_for_sprint` |
| J | Story Clarity | `quality_score.dimension_scores.story_clarity` |
| K | NFR Coverage | `quality_score.dimension_scores.nfr_coverage` |
| L | Dependency ID | `quality_score.dimension_scores.dependency_identification` |
| M | AC Testability | `quality_score.dimension_scores.acceptance_criteria_testability` |
| N | Assumption Transparency | `quality_score.dimension_scores.assumption_transparency` |
| O | NFRs Found | count of confirmed/inferred NFRs |
| P | Dependencies Found | total upstream + downstream + external |
| Q | Assumptions Documented | count of governance assumptions |
| R | Hallucination Flags | count of governance hallucination flags |
| S | Missing Info Items | count of governance missing_information items |
| T | PII Check Result | `governance.pii_check.result` |
| U | Improvement Suggestions | `quality_score.improvement_suggestions` (500 char cap) |

---

## Using from n8n

In your n8n workflow, after the Step 6 governance audit node, add an **Execute Command** node:

```
python3 /home/calvin/projects/storyguard/scripts/log_to_sheets.py \
  --data '{{ $json.body }}' \
  --raw-score {{ $node["IntakeParser"].json.raw_score }}
```

Replace the variable references with your actual n8n node names and field paths.

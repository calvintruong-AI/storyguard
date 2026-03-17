#!/usr/bin/env python3
"""
StoryGuard — Completeness Scorecard Logger
Logs each pipeline run to Google Sheets for before/after measurement.

This script is called by n8n after each completed pipeline run.
It writes one row per processed intake to your scorecard spreadsheet.

Setup (one-time):
1. Go to console.cloud.google.com
2. Create a project → Enable Google Sheets API
3. Create a Service Account → Download JSON key
4. Save key as: storyguard/config/google_service_account.json
5. Share your Google Sheet with the service account email
6. Set SHEET_ID in config below

Usage:
  python3 log_to_sheets.py --data '{"story_id": "SG-2025-001", ...}'
  python3 log_to_sheets.py --file path/to/output.json

Requirements:
  pip3 install google-auth google-auth-oauthlib google-api-python-client
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
# Update these before running

SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"
SHEET_TAB_NAME = "StoryGuard Scorecard"
SERVICE_ACCOUNT_FILE = str(Path(__file__).parent.parent / "config" / "google_service_account.json")

# Column headers — these must match the order in SHEET_COLUMNS below
SHEET_HEADERS = [
    "Story ID",
    "Timestamp",
    "Domain",
    "Raw Intake (truncated)",
    "Raw Score (before)",
    "Enriched Score (after)",
    "Score Delta",
    "Grade",
    "Sprint Ready",
    "Story Clarity",
    "NFR Coverage",
    "Dependency ID",
    "AC Testability",
    "Assumption Transparency",
    "NFRs Found",
    "Dependencies Found",
    "Assumptions Documented",
    "Hallucination Flags",
    "Missing Info Items",
    "PII Check Result",
    "Improvement Suggestions"
]

# ─────────────────────────────────────────────────────────────────────────────


def build_row(output_data: dict, raw_score: float = None) -> list:
    """
    Extract scorecard values from a completed StoryGuard output document.
    Maps to SHEET_HEADERS order.
    """
    metadata = output_data.get("metadata", {})
    quality = output_data.get("quality_score", {})
    governance = output_data.get("governance", {})
    dimensions = quality.get("dimension_scores", {})
    nfrs = output_data.get("non_functional_requirements", {})
    dependencies = output_data.get("system_dependencies", {})

    enriched_score = quality.get("total_score", 0)
    raw_score = raw_score if raw_score is not None else 0
    score_delta = round(enriched_score - raw_score, 1)

    # Count NFRs that are confirmed or inferred (not missing/not_applicable)
    nfr_count = sum(
        1 for nfr in nfrs.values()
        if isinstance(nfr, dict) and nfr.get("status") in ["confirmed", "inferred"]
    )

    # Count all dependencies
    upstream = len(dependencies.get("upstream", []))
    downstream = len(dependencies.get("downstream", []))
    external = len(dependencies.get("external_integrations", []))
    dep_count = upstream + downstream + external

    # Truncate intake for readability in sheet
    intake_text = metadata.get("intake_text", "")
    intake_truncated = intake_text[:120] + "..." if len(intake_text) > 120 else intake_text

    # Improvement suggestions as semicolon-separated string
    suggestions = "; ".join(quality.get("improvement_suggestions", []))

    return [
        metadata.get("story_id", ""),
        metadata.get("generated_at", datetime.utcnow().isoformat() + "Z"),
        metadata.get("domain", "unknown"),
        intake_truncated,
        raw_score,
        enriched_score,
        score_delta,
        quality.get("grade", ""),
        "Yes" if quality.get("ready_for_sprint") else "No",
        dimensions.get("story_clarity", 0),
        dimensions.get("nfr_coverage", 0),
        dimensions.get("dependency_identification", 0),
        dimensions.get("acceptance_criteria_testability", 0),
        dimensions.get("assumption_transparency", 0),
        nfr_count,
        dep_count,
        len(governance.get("assumptions", [])),
        len(governance.get("hallucination_flags", [])),
        len(governance.get("missing_information", [])),
        governance.get("pii_check", {}).get("result", "not_run"),
        suggestions[:500] if suggestions else ""
    ]


def ensure_headers(service, spreadsheet_id: str, tab_name: str):
    """
    Write headers to row 1 if the sheet is empty.
    Safe to call on every run — only writes if row 1 is blank.
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{tab_name}!A1:A1"
    ).execute()

    existing = result.get("values", [])
    if not existing:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_name}!A1",
            valueInputOption="RAW",
            body={"values": [SHEET_HEADERS]}
        ).execute()
        print(f"Headers written to {tab_name}")


def append_row(output_data: dict, raw_score: float = None) -> dict:
    """
    Append one scorecard row to Google Sheets.
    Returns the update response or error dict.
    """
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return {
            "success": False,
            "error": "Google API libraries not installed. Run: pip3 install google-auth google-api-python-client"
        }

    if SHEET_ID == "YOUR_GOOGLE_SHEET_ID_HERE":
        return {
            "success": False,
            "error": "SHEET_ID not configured. Update log_to_sheets.py with your Google Sheet ID."
        }

    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)

        ensure_headers(service, SHEET_ID, SHEET_TAB_NAME)

        row = build_row(output_data, raw_score=raw_score)

        response = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"{SHEET_TAB_NAME}!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()

        return {
            "success": True,
            "story_id": output_data.get("metadata", {}).get("story_id", ""),
            "score": output_data.get("quality_score", {}).get("total_score", 0),
            "grade": output_data.get("quality_score", {}).get("grade", ""),
            "rows_appended": response.get("updates", {}).get("updatedRows", 0)
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Service account file not found: {SERVICE_ACCOUNT_FILE}. See setup instructions in this file."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="StoryGuard scorecard logger — appends run results to Google Sheets"
    )
    parser.add_argument("--data", help="JSON string of StoryGuard output")
    parser.add_argument("--file", help="Path to StoryGuard output JSON file")
    parser.add_argument("--raw-score", type=float, default=0.0,
                        help="Completeness score of raw intake before enrichment (default: 0)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")

    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as f:
            output_data = json.load(f)
    elif args.data:
        output_data = json.loads(args.data)
    elif not sys.stdin.isatty():
        output_data = json.load(sys.stdin)
    else:
        parser.print_help()
        sys.exit(1)

    result = append_row(output_data, raw_score=args.raw_score)
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()

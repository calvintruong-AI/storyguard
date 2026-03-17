#!/usr/bin/env python3
"""
StoryGuard — PII Detection Pre-Check
Step 1 of the governed pipeline.

Sends intake text to a local Ollama model for PII detection.
No data leaves your machine in this step.

Usage:
  python3 pii_check.py "Your intake text here"
  python3 pii_check.py --file path/to/intake.txt

Requirements:
  pip3 install ollama
  ollama pull llama3  (or mistral, phi3 — any model you have)
"""

import sys
import json
import argparse
from datetime import datetime

try:
    import ollama
except ImportError:
    print(json.dumps({
        "error": "ollama package not installed. Run: pip3 install ollama",
        "pii_detected": None,
        "result": "error"
    }))
    sys.exit(1)


PII_PROMPT = """You are a data privacy compliance checker for a financial services company.

Your job is to analyze text for personally identifiable information (PII) or 
sensitive financial data that should not be sent to external AI services.

Check for:
- Full names of real individuals (clients, advisors, employees)
- Account numbers, policy numbers, or contract IDs
- Social security numbers or tax IDs
- Email addresses or phone numbers
- Specific dollar amounts tied to named individuals
- Dates of birth
- Physical addresses of real people

Text to analyze:
{intake_text}

Respond ONLY with valid JSON. No explanation, no markdown, no preamble.
Format exactly:
{{
  "pii_detected": true or false,
  "result": "clean" or "flagged",
  "flagged_terms": ["term1", "term2"],
  "recommendation": "safe_to_proceed" or "review_required",
  "explanation": "one sentence explanation of finding"
}}"""


def check_pii(intake_text: str, model: str = "llama3") -> dict:
    """
    Run PII detection on intake text using local Ollama model.
    Returns structured result dict.
    """
    prompt = PII_PROMPT.format(intake_text=intake_text)

    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={
                "temperature": 0.1,
                "top_p": 0.9
            }
        )

        raw_output = response["response"].strip()

        # Strip markdown code blocks if model wraps output
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            raw_output = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        result = json.loads(raw_output)

        # Ensure required fields are present
        required_fields = ["pii_detected", "result", "flagged_terms", "recommendation"]
        for field in required_fields:
            if field not in result:
                result[field] = "unknown"

        # Add metadata
        result["metadata"] = {
            "model_used": model,
            "check_performed": True,
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "intake_length": len(intake_text)
        }

        return result

    except json.JSONDecodeError as e:
        return {
            "pii_detected": None,
            "result": "parse_error",
            "flagged_terms": [],
            "recommendation": "review_required",
            "explanation": f"Model output could not be parsed as JSON: {str(e)}",
            "raw_output": raw_output if "raw_output" in locals() else "no output",
            "metadata": {
                "model_used": model,
                "check_performed": True,
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "error": "json_parse_error"
            }
        }

    except Exception as e:
        error_msg = str(e)
        if "model" in error_msg.lower() and "not found" in error_msg.lower():
            suggestion = f"Model '{model}' not found. Run: ollama pull {model}"
        elif "connection" in error_msg.lower():
            suggestion = "Ollama not running. Start with: ollama serve"
        else:
            suggestion = "Check Ollama installation and model availability"

        return {
            "pii_detected": None,
            "result": "error",
            "flagged_terms": [],
            "recommendation": "review_required",
            "explanation": f"PII check failed: {error_msg}. {suggestion}",
            "metadata": {
                "model_used": model,
                "check_performed": False,
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "error": error_msg
            }
        }


def should_proceed(pii_result: dict) -> bool:
    """
    Returns True if safe to send to external Claude API.
    Blocks on: flagged PII, errors, or parse failures.
    """
    if pii_result.get("result") in ["flagged", "error", "parse_error"]:
        return False
    if pii_result.get("pii_detected") is True:
        return False
    if pii_result.get("recommendation") == "review_required":
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="StoryGuard PII pre-check — runs locally via Ollama"
    )
    parser.add_argument(
        "intake_text",
        nargs="?",
        help="Intake text to check (or use --file)"
    )
    parser.add_argument(
        "--file",
        help="Path to text file containing intake"
    )
    parser.add_argument(
        "--model",
        default="llama3",
        help="Ollama model to use (default: llama3)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )

    args = parser.parse_args()

    # Get intake text
    if args.file:
        with open(args.file, "r") as f:
            intake_text = f.read().strip()
    elif args.intake_text:
        intake_text = args.intake_text
    elif not sys.stdin.isatty():
        intake_text = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(1)

    if not intake_text:
        print(json.dumps({"error": "No intake text provided"}))
        sys.exit(1)

    # Run check
    result = check_pii(intake_text, model=args.model)

    # Add proceed decision
    result["pipeline_action"] = "proceed" if should_proceed(result) else "blocked"

    # Output
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent))

    # Exit code: 0 = clean, 1 = flagged/error
    sys.exit(0 if should_proceed(result) else 1)


if __name__ == "__main__":
    main()

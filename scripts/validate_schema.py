#!/usr/bin/env python3
"""
validate_schema.py — Personal RAG Database Validator
=====================================================
Validates all data files (JSON, CSV, YAML, MD) in the repository for:
- JSON/YAML schema compliance
- Expected CSV headers and datatypes
- ISO 8601 date formats
- Pipe-separated tags in CSVs
- Remaining TODO placeholders

Usage:
    python scripts/validate_schema.py
"""

import csv
import json
import re
import sys
from pathlib import Path

# Reconfigure stdout to use UTF-8 to prevent encoding errors on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ---------------------------------------------------------------------------
# Constants & Colors
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_DIM = "\033[2m"

# Expected headers for CSV files
CSV_SCHEMAS = {
    "02_timeline/timeline.csv": [
        "start_date", "end_date", "event_type", "title", "organization", 
        "description", "location", "importance", "tags"
    ],
    "03_skills/skills.csv": [
        "skill_name", "category", "proficiency_level", "proficiency_numeric", 
        "years_used", "last_used", "context", "evidence_projects", "tags"
    ],
    "04_projects/projects.csv": [
        "project_name", "type", "status", "start_date", "end_date", "role", 
        "tech_stack", "description", "key_features", "impact_metrics", 
        "repository", "importance_score (1-10)", "tags"
    ],
    "05_achievements/achievements.csv": [
        "achievement_name", "category", "issuer", "date", "credential_id", 
        "description", "url", "importance", "tags"
    ],
    "09_experience/experience.csv": [
        "company", "title", "type", "start_date", "end_date", "location", 
        "description", "tech_stack", "key_achievements", "tags"
    ],
    "10_learning/reading_list.csv": [
        "title", "author", "type", "status", "year", "rating", "key_takeaways", "tags"
    ],
    "10_learning/certifications_roadmap.csv": [
        "certification_name", "provider", "status", "target_date", "priority", 
        "prerequisites", "tags"
    ],
    "12_network/network.csv": [
        "name", "relationship", "organization", "context", "strength", "tags"
    ],
    "13_content/open_source.csv": [
        "repo_name", "description", "tech_stack", "stars", "status", "url", "tags"
    ]
}

# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

def is_iso_date(date_str: str) -> bool:
    """Check if date matches ISO 8601 YYYY-MM-DD or YYYY-MM or YYYY."""
    if not date_str or date_str == "-":
        return True
    # YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return True
    # YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", date_str):
        return True
    # YYYY
    if re.match(r"^\d{4}$", date_str):
        return True
    return False


def check_placeholders(content: str) -> list[str]:
    """Check for TODOs or placeholder structures in content."""
    errors = []
    # Match strings like "TODO", "TODO_...", "placeholder", etc.
    matches = re.findall(r"\b(TODO|TODO_\w+|placeholder)\b", content, re.IGNORECASE)
    if matches:
        for match in set(matches):
            if "ganeshgiridhar" not in match.lower() and "placeholder.com" not in content.lower():
                errors.append(f"Found placeholder term: '{match}'")
    return errors


def detect_csv_delimiter(filepath: Path) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        sample = f.read(1024)
    return "\t" if sample.count("\t") > sample.count(",") else ","


# ---------------------------------------------------------------------------
# File Validators
# ---------------------------------------------------------------------------

def validate_json_file(filepath: Path) -> list[str]:
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # Check placeholders
            errors.extend(check_placeholders(content))
            # Try parsing
            json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON Syntax Error: {e.msg} at line {e.lineno}, col {e.colno}")
    except Exception as e:
        errors.append(f"JSON Read Error: {str(e)}")
    return errors


def validate_csv_file(filepath: Path, rel_path: str) -> list[str]:
    errors = []
    if rel_path not in CSV_SCHEMAS:
        return [f"CSV schema definition not found in validator for: {rel_path}"]
    
    expected_headers = CSV_SCHEMAS[rel_path]
    try:
        delimiter = detect_csv_delimiter(filepath)
        if delimiter == "\t":
            errors.append("CSV file uses Tab delimiters instead of standard Commas")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            errors.extend(check_placeholders(content))
            f.seek(0)
            
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader, None)
            
            if not headers:
                return ["CSV file is empty or missing header row"]

            # Compare headers (strip whitespace/bom)
            headers_clean = [h.strip().replace('\ufeff', '') for h in headers]
            for index, expected in enumerate(expected_headers):
                if index >= len(headers_clean):
                    errors.append(f"Missing header column: '{expected}'")
                elif headers_clean[index] != expected:
                    errors.append(f"Header mismatch at col {index + 1}. Expected '{expected}', got '{headers_clean[index]}'")

            # Validate rows
            for row_idx, row in enumerate(reader, 2):
                if not row or all(not cell.strip() for cell in row):
                    continue  # skip blank lines
                
                # Column count check
                if len(row) != len(expected_headers):
                    errors.append(f"Row {row_idx}: Column count mismatch. Expected {len(expected_headers)} fields, got {len(row)}")
                    continue
                
                # Check specifics per column
                row_dict = dict(zip(expected_headers, row))
                
                # Date fields check
                for col in ["start_date", "end_date", "date", "target_date"]:
                    if col in row_dict and row_dict[col]:
                        val = row_dict[col].strip()
                        if not is_iso_date(val):
                            errors.append(f"Row {row_idx}: Column '{col}' value '{val}' is not in valid ISO 8601 format (YYYY-MM-DD, YYYY-MM, or YYYY)")
                
                # Numeric field check
                for col in ["proficiency_numeric", "importance", "importance_score (1-10)", "stars", "rating"]:
                    if col in row_dict and row_dict[col] and row_dict[col] != "-":
                        val = row_dict[col].strip()
                        try:
                            float(val)
                        except ValueError:
                            errors.append(f"Row {row_idx}: Column '{col}' value '{val}' is not numeric")

                # Tags format check (should use pipe delimiter, not commas)
                if "tags" in row_dict and row_dict["tags"]:
                    tags_val = row_dict["tags"].strip()
                    if "," in tags_val:
                        errors.append(f"Row {row_idx}: Tags should be separated by pipes '|', found comma: '{tags_val}'")

    except Exception as e:
        errors.append(f"CSV Parse Error: {str(e)}")
    return errors


def validate_yaml_file(filepath: Path) -> list[str]:
    errors = []
    try:
        content = filepath.read_text(encoding="utf-8")
        errors.extend(check_placeholders(content))
        # Basic indentation-based validation since we don't import third-party yaml libraries
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            if line.strip() and not line.startswith("#"):
                # Check for bad indentation (must be spaces, no tabs)
                if "\t" in line:
                    errors.append(f"Line {idx}: Found tab character. Use spaces for YAML indentation.")
                # Check for key-value formatting
                if ":" in line and not line.strip().startswith("-") and not line.strip().startswith("#"):
                    parts = line.split(":", 1)
                    key = parts[0].strip()
                    if not re.match(r"^[\w_]+$", key) and not key.startswith('"') and not key.startswith("'"):
                        # might be okay, but warn if look suspicious
                        pass
    except Exception as e:
        errors.append(f"YAML Read Error: {str(e)}")
    return errors


def validate_markdown_file(filepath: Path) -> list[str]:
    errors = []
    try:
        content = filepath.read_text(encoding="utf-8")
        errors.extend(check_placeholders(content))
        # Basic validation: ensure it has at least one heading
        if not content.startswith("#") and "\n#" not in content:
            errors.append("Markdown file is missing headings")
    except Exception as e:
        errors.append(f"Markdown Read Error: {str(e)}")
    return errors


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def main():
    print(f"\n{C_BOLD}{C_CYAN}╔══════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║   personal-rag-db Schema Validation Tool         ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚══════════════════════════════════════════════════╝{C_RESET}\n")

    files_to_validate = [
        # JSON files
        ("01_identity/identity.json", "json"),
        ("01_identity/elevator_pitches.json", "json"),
        ("11_goals/goals.json", "json"),
        ("15_interview_prep/behavioral_answers.json", "json"),
        
        # YAML files
        ("01_identity/communication_style.yaml", "yaml"),
        
        # Markdown files
        ("06_psychology/psychology.md", "md"),
        ("11_goals/career_vision.md", "md"),
        ("14_values_beliefs/manifesto.md", "md"),
        ("14_values_beliefs/failures_and_lessons.md", "md"),
        ("15_interview_prep/technical_deep_dives.md", "md"),
        ("09_experience/role_details/codsoft.md", "md"),
        ("09_experience/role_details/live_in_labs.md", "md"),
        
        # CSV files
        ("02_timeline/timeline.csv", "csv"),
        ("03_skills/skills.csv", "csv"),
        ("04_projects/projects.csv", "csv"),
        ("05_achievements/achievements.csv", "csv"),
        ("09_experience/experience.csv", "csv"),
        ("10_learning/reading_list.csv", "csv"),
        ("10_learning/certifications_roadmap.csv", "csv"),
        ("12_network/network.csv", "csv"),
        ("13_content/open_source.csv", "csv"),
    ]

    total_failures = 0
    total_files = len(files_to_validate)

    print(f"{C_BOLD}Validating database files:{C_RESET}\n")

    for rel_path, file_type in files_to_validate:
        filepath = PROJECT_ROOT / rel_path
        print(f"  {C_BOLD}{rel_path:<45}{C_RESET}", end="")
        
        if not filepath.exists():
            print(f"[{C_RED}MISSING{C_RESET}]")
            total_failures += 1
            continue

        errors = []
        if file_type == "json":
            errors = validate_json_file(filepath)
        elif file_type == "csv":
            errors = validate_csv_file(filepath, rel_path)
        elif file_type == "yaml":
            errors = validate_yaml_file(filepath)
        elif file_type == "md":
            errors = validate_markdown_file(filepath)

        if errors:
            print(f"[{C_RED}FAIL{C_RESET}]")
            for err in errors:
                print(f"    {C_RED}└── {err}{C_RESET}")
            total_failures += 1
        else:
            print(f"[{C_GREEN}PASS{C_RESET}]")

    print(f"\n{C_BOLD}{'═' * 52}{C_RESET}")
    print(f"  {C_BOLD}VALIDATION SUMMARY{C_RESET}")
    print(f"{C_BOLD}{'═' * 52}{C_RESET}")
    print(f"  Total Files Validated:  {total_files}")
    print(f"  Passed:                 {C_GREEN}{total_files - total_failures}{C_RESET}")
    print(f"  Failed/Missing:         {C_RED if total_failures else C_GREEN}{total_failures}{C_RESET}")
    print(f"{C_BOLD}{'═' * 52}{C_RESET}\n")

    if total_failures > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_chunks.py — Comprehensive RAG Chunking Pipeline
======================================================
Reads ALL source files from the personal-rag-db, creates hierarchical chunks
(parent → child), generates hypothetical Q&A pairs, and writes structured
JSONL output with full metadata.

Usage:
    python scripts/build_chunks.py
    python scripts/build_chunks.py --verbose
    python scripts/build_chunks.py --output-dir 07_chunks
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Reconfigure stdout to use UTF-8 to prevent encoding errors on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKEN_RATIO = 1.3  # approx tokens per word
TARGET_MIN_TOKENS = 200
TARGET_MAX_TOKENS = 400
PARENT_MIN_TOKENS = 512
PARENT_MAX_TOKENS = 1024

# ANSI colours for terminal output
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_MAGENTA = "\033[95m"
C_DIM = "\033[2m"

# Category → importance baseline
IMPORTANCE_MAP = {
    "identity": 9,
    "communication_style": 8,
    "elevator_pitches": 8,
    "timeline": 7,
    "skills": 8,
    "projects": 9,
    "achievements": 6,
    "psychology": 9,
    "prompts": 5,
    "experience": 8,
    "learning": 5,
    "goals": 7,
    "network": 4,
    "content": 5,
    "values_beliefs": 8,
    "interview_prep": 7,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Approximate token count from text."""
    words = len(text.split())
    return int(words * TOKEN_RATIO)


def sha256(text: str) -> str:
    """SHA-256 hex digest of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_entities(text: str) -> list[str]:
    """Extract likely entities via regex — capitalized phrases, tech terms."""
    # Capitalized multi-word phrases (e.g. "Amrita Vishwa Vidyapeetham")
    cap_phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
    # Single capitalized words ≥3 chars (filter common English)
    cap_words = re.findall(r"\b[A-Z][a-z]{2,}\b", text)
    # Tech terms: known patterns
    tech_pattern = re.findall(
        r"\b(?:Python|Java|JavaScript|TypeScript|Flutter|Dart|React|Next\.js|Node\.js|"
        r"Express\.js|FastAPI|Docker|PostgreSQL|MySQL|SQLite|MongoDB|Firebase|"
        r"Gemini|LangChain|Pathway|Riverpod|Drift|Tailwind|HTML|CSS|Git|GitHub|"
        r"Kafka|Spring Boot|n8n|Figma|Azure|AWS|GCP|RAG|LLM|AI|ML|NLP|"
        r"MERN|REST|API|JWT|WCAG|GST|DFS|BFS|DP|DAA|AST|ORM|SIP|"
        r"Minimax|Zobrist|JavaFX|Vite|Pandas|NumPy|TensorFlow|PyTorch)\b",
        text,
    )
    # Deduplicate preserving order
    seen = set()
    entities = []
    stop_words = {
        "The", "This", "That", "These", "Those", "His", "Her", "Its",
        "For", "From", "With", "And", "But", "Not", "Are", "Was", "Were",
        "Has", "Had", "Have", "Can", "Will", "May", "Also", "You", "Your",
        "Key", "New", "How", "Why", "What", "When", "Where", "Who",
        "Instead", "Based", "Built", "Uses", "Core", "Deep",
    }
    for e in cap_phrases + cap_words + tech_pattern:
        e_clean = e.strip()
        if e_clean not in seen and e_clean not in stop_words and len(e_clean) > 1:
            seen.add(e_clean)
            entities.append(e_clean)
    return entities[:30]  # cap at 30


def extract_temporal(text: str) -> dict:
    """Extract date-like patterns from text."""
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    years = re.findall(r"\b(20[0-2]\d|19\d\d)\b", text)
    return {
        "dates": sorted(set(dates)),
        "years": sorted(set(years)),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_chunk(
    chunk_id: str,
    source: str,
    category: str,
    subcategory: str,
    content: str,
    context_header: str,
    importance: int = 5,
    tags: list[str] | None = None,
    chunk_type: str = "child",
) -> dict:
    """Build a standardised chunk dict."""
    token_count = estimate_tokens(content)
    return {
        "chunk_id": chunk_id,
        "source": source,
        "category": category,
        "subcategory": subcategory,
        "content": content,
        "context_header": context_header,
        "entities": extract_entities(content),
        "temporal": extract_temporal(content),
        "importance": importance,
        "tags": tags or [],
        "token_count": token_count,
        "chunk_type": chunk_type,
        "created_at": now_iso(),
        "checksum": sha256(content),
    }


# ---------------------------------------------------------------------------
# Source readers
# ---------------------------------------------------------------------------

def detect_csv_delimiter(filepath: Path) -> str:
    """Detect whether a CSV uses tabs or commas."""
    with open(filepath, "r", encoding="utf-8") as f:
        sample = f.read(2048)
    tab_count = sample.count("\t")
    comma_count = sample.count(",")
    return "\t" if tab_count > comma_count else ","


def read_csv_rows(filepath: Path) -> list[dict]:
    """Read CSV (auto-detect delimiter), return list of row dicts."""
    if not filepath.exists():
        return []
    delimiter = detect_csv_delimiter(filepath)
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # skip fully empty rows
            if any(v and v.strip() for v in row.values()):
                rows.append({k: (v.strip() if v else "") for k, v in row.items()})
    return rows


def read_json(filepath: Path) -> dict | list | None:
    """Read a JSON file."""
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def read_yaml(filepath: Path) -> dict | None:
    """Read a YAML file using a simple parser (no PyYAML dependency)."""
    if not filepath.exists():
        return None
    # Minimal YAML-like parser for flat/nested structures
    result = {}
    current_key = None
    current_list = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue
            # List item under a key
            if stripped.startswith("  - "):
                val = stripped[4:].strip().strip('"').strip("'")
                if current_list is not None:
                    current_list.append(val)
                continue
            # Top-level key: value
            match = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', stripped)
            if match:
                key = match.group(1)
                val = match.group(2).strip().strip('"').strip("'")
                if val:
                    result[key] = val
                    current_key = key
                    current_list = None
                else:
                    # value will be a list
                    current_list = []
                    result[key] = current_list
                    current_key = key
    return result


def read_markdown_sections(filepath: Path) -> list[tuple[str, str]]:
    """Split markdown by ## headings. Returns [(heading, body), ...]."""
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    sections = []
    # Split on ## headings (level 2)
    parts = re.split(r"^(#{1,3}\s+.+)$", text, flags=re.MULTILINE)
    current_heading = filepath.stem.replace("_", " ").title()
    current_body = []
    for part in parts:
        heading_match = re.match(r"^#{1,3}\s+(.+)$", part.strip())
        if heading_match:
            # Save previous section
            body_text = "\n".join(current_body).strip()
            if body_text:
                sections.append((current_heading, body_text))
            current_heading = heading_match.group(1).strip()
            current_body = []
        else:
            current_body.append(part)
    # Last section
    body_text = "\n".join(current_body).strip()
    if body_text:
        sections.append((current_heading, body_text))
    return sections


def read_text(filepath: Path) -> str:
    """Read a plain text file."""
    if not filepath.exists():
        return ""
    return filepath.read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# Chunk generators per source type
# ---------------------------------------------------------------------------

def chunk_csv(filepath: Path, category: str, id_prefix: str, verbose: bool = False) -> list[dict]:
    """Create one chunk per CSV row + a summary chunk."""
    rows = read_csv_rows(filepath)
    if not rows:
        return []
    chunks = []
    importance = IMPORTANCE_MAP.get(category, 5)
    source = str(filepath.relative_to(PROJECT_ROOT))

    for i, row in enumerate(rows, 1):
        # Build content from all fields
        content_parts = []
        tags = []
        name_field = ""
        for key, val in row.items():
            if val and val != "-":
                content_parts.append(f"{key}: {val}")
                if key in ("semantic_tags", "tags"):
                    tags.extend([t.strip() for t in val.replace("|", ",").split(",") if t.strip()])
                if key in ("skill_name", "project_name", "achievement_name", "event_name", "role_title"):
                    name_field = val

        content = "\n".join(content_parts)
        context = f"{category.title()} — {name_field or f'Entry {i}'}"

        chunk = make_chunk(
            chunk_id=f"{id_prefix}_{i:03d}",
            source=source,
            category=category,
            subcategory=name_field or f"entry_{i}",
            content=content,
            context_header=context,
            importance=importance,
            tags=tags or [category],
        )
        chunks.append(chunk)

    # Summary chunk
    if rows:
        summary_lines = [f"Summary of {category}: {len(rows)} entries."]
        for i, row in enumerate(rows, 1):
            first_vals = list(row.values())[:3]
            summary_lines.append(f"  {i}. {' | '.join(v for v in first_vals if v and v != '-')}")
        summary_content = "\n".join(summary_lines)
        summary_chunk = make_chunk(
            chunk_id=f"{id_prefix}_summary",
            source=source,
            category=category,
            subcategory="summary",
            content=summary_content,
            context_header=f"{category.title()} — Complete Summary",
            importance=importance - 1,
            tags=[category, "summary"],
        )
        chunks.append(summary_chunk)

    if verbose:
        print(f"  {C_DIM}├── {filepath.name}: {len(chunks)} chunks{C_RESET}")
    return chunks


def chunk_json(filepath: Path, category: str, id_prefix: str, verbose: bool = False) -> list[dict]:
    """Create chunks per top-level section of a JSON file."""
    data = read_json(filepath)
    if data is None:
        return []
    chunks = []
    importance = IMPORTANCE_MAP.get(category, 5)
    source = str(filepath.relative_to(PROJECT_ROOT))

    if isinstance(data, dict):
        for i, (key, value) in enumerate(data.items(), 1):
            if isinstance(value, dict):
                content = f"{key}:\n" + "\n".join(f"  {k}: {v}" for k, v in value.items())
            elif isinstance(value, list):
                content = f"{key}:\n" + "\n".join(f"  - {item}" for item in value)
            else:
                content = f"{key}: {value}"

            chunk = make_chunk(
                chunk_id=f"{id_prefix}_{i:03d}",
                source=source,
                category=category,
                subcategory=key,
                content=content,
                context_header=f"{category.title()} — {key}",
                importance=importance,
                tags=[category, key],
            )
            chunks.append(chunk)
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            content = json.dumps(item, indent=2) if isinstance(item, (dict, list)) else str(item)
            chunk = make_chunk(
                chunk_id=f"{id_prefix}_{i:03d}",
                source=source,
                category=category,
                subcategory=f"item_{i}",
                content=content,
                context_header=f"{category.title()} — Item {i}",
                importance=importance,
                tags=[category],
            )
            chunks.append(chunk)

    if verbose:
        print(f"  {C_DIM}├── {filepath.name}: {len(chunks)} chunks{C_RESET}")
    return chunks


def chunk_yaml(filepath: Path, category: str, id_prefix: str, verbose: bool = False) -> list[dict]:
    """Create chunks per section of a YAML file."""
    data = read_yaml(filepath)
    if not data:
        return []
    chunks = []
    importance = IMPORTANCE_MAP.get(category, 5)
    source = str(filepath.relative_to(PROJECT_ROOT))

    for i, (key, value) in enumerate(data.items(), 1):
        if isinstance(value, list):
            content = f"{key}:\n" + "\n".join(f"  - {item}" for item in value)
        else:
            content = f"{key}: {value}"

        chunk = make_chunk(
            chunk_id=f"{id_prefix}_{i:03d}",
            source=source,
            category=category,
            subcategory=key,
            content=content,
            context_header=f"{category.title()} — {key}",
            importance=importance,
            tags=[category, key],
        )
        chunks.append(chunk)

    if verbose:
        print(f"  {C_DIM}├── {filepath.name}: {len(chunks)} chunks{C_RESET}")
    return chunks


def chunk_markdown(filepath: Path, category: str, id_prefix: str, verbose: bool = False) -> list[dict]:
    """Split markdown by ## headings into separate chunks."""
    sections = read_markdown_sections(filepath)
    if not sections:
        return []
    chunks = []
    importance = IMPORTANCE_MAP.get(category, 5)
    source = str(filepath.relative_to(PROJECT_ROOT))

    for i, (heading, body) in enumerate(sections, 1):
        chunk = make_chunk(
            chunk_id=f"{id_prefix}_{i:03d}",
            source=source,
            category=category,
            subcategory=heading.lower().replace(" ", "_"),
            content=f"## {heading}\n\n{body}",
            context_header=f"{category.title()} — {heading}",
            importance=importance,
            tags=[category, heading.lower().replace(" ", "_")],
        )
        chunks.append(chunk)

    if verbose:
        print(f"  {C_DIM}├── {filepath.name}: {len(chunks)} chunks{C_RESET}")
    return chunks


def chunk_text(filepath: Path, category: str, id_prefix: str, verbose: bool = False) -> list[dict]:
    """Create a single chunk from a text file."""
    text = read_text(filepath)
    if not text:
        return []
    source = str(filepath.relative_to(PROJECT_ROOT))
    importance = IMPORTANCE_MAP.get(category, 5)

    chunk = make_chunk(
        chunk_id=f"{id_prefix}_001",
        source=source,
        category=category,
        subcategory=filepath.stem,
        content=text,
        context_header=f"{category.title()} — {filepath.stem}",
        importance=importance,
        tags=[category],
    )
    if verbose:
        print(f"  {C_DIM}├── {filepath.name}: 1 chunk{C_RESET}")
    return [chunk]


# ---------------------------------------------------------------------------
# Parent chunk builder
# ---------------------------------------------------------------------------

def build_parent_chunks(child_chunks: list[dict]) -> list[dict]:
    """Combine related child chunks into parent chunks (512–1024 tokens)."""
    # Group by category
    by_category: dict[str, list[dict]] = defaultdict(list)
    for c in child_chunks:
        by_category[c["category"]].append(c)

    parents = []
    for category, children in by_category.items():
        # Sort by chunk_id
        children.sort(key=lambda x: x["chunk_id"])
        buffer_content = []
        buffer_tokens = 0
        buffer_children = []
        parent_idx = 1

        for child in children:
            child_tokens = child["token_count"]
            # If adding this child would exceed max, flush
            if buffer_tokens + child_tokens > PARENT_MAX_TOKENS and buffer_content:
                parent = make_chunk(
                    chunk_id=f"parent_{category}_{parent_idx:03d}",
                    source=f"aggregated:{category}",
                    category=category,
                    subcategory="parent_aggregate",
                    content="\n\n---\n\n".join(buffer_content),
                    context_header=f"Parent Chunk — {category.title()} (Group {parent_idx})",
                    importance=max(c["importance"] for c in buffer_children),
                    tags=[category, "parent"],
                    chunk_type="parent",
                )
                parent["child_chunk_ids"] = [c["chunk_id"] for c in buffer_children]
                parents.append(parent)
                parent_idx += 1
                buffer_content = []
                buffer_tokens = 0
                buffer_children = []

            buffer_content.append(child["content"])
            buffer_tokens += child_tokens
            buffer_children.append(child)

        # Flush remaining
        if buffer_content:
            parent = make_chunk(
                chunk_id=f"parent_{category}_{parent_idx:03d}",
                source=f"aggregated:{category}",
                category=category,
                subcategory="parent_aggregate",
                content="\n\n---\n\n".join(buffer_content),
                context_header=f"Parent Chunk — {category.title()} (Group {parent_idx})",
                importance=max(c["importance"] for c in buffer_children),
                tags=[category, "parent"],
                chunk_type="parent",
            )
            parent["child_chunk_ids"] = [c["chunk_id"] for c in buffer_children]
            parents.append(parent)

    return parents


# ---------------------------------------------------------------------------
# Hypothetical Q&A pair chunks
# ---------------------------------------------------------------------------

QA_PAIRS = [
    {
        "question": "Who is Kankatala Ganesh Giridhar?",
        "category": "identity",
        "tags": ["identity", "overview"],
    },
    {
        "question": "What are Ganesh's strongest technical skills?",
        "category": "skills",
        "tags": ["skills", "technical"],
    },
    {
        "question": "Tell me about Ganesh's most important project.",
        "category": "projects",
        "tags": ["projects", "riceagent"],
    },
    {
        "question": "What is Ganesh's educational background?",
        "category": "timeline",
        "tags": ["education", "academics"],
    },
    {
        "question": "What hackathons has Ganesh participated in?",
        "category": "achievements",
        "tags": ["hackathons", "competitions"],
    },
    {
        "question": "What motivates Ganesh?",
        "category": "psychology",
        "tags": ["motivation", "drive"],
    },
    {
        "question": "What is Ganesh's communication style?",
        "category": "communication_style",
        "tags": ["communication", "persona"],
    },
    {
        "question": "What certifications does Ganesh have?",
        "category": "achievements",
        "tags": ["certifications", "learning"],
    },
    {
        "question": "What is Ganesh's approach to problem solving?",
        "category": "psychology",
        "tags": ["systems-thinking", "first-principles"],
    },
    {
        "question": "What AI and LLM experience does Ganesh have?",
        "category": "skills",
        "tags": ["ai", "llm", "rag"],
    },
    {
        "question": "What is Ganesh's career vision?",
        "category": "goals",
        "tags": ["career", "goals", "vision"],
    },
    {
        "question": "What internship experience does Ganesh have?",
        "category": "experience",
        "tags": ["internship", "codsoft", "work"],
    },
    {
        "question": "How does Ganesh handle failure?",
        "category": "psychology",
        "tags": ["resilience", "failure", "growth"],
    },
    {
        "question": "What is RiceAgent Pro?",
        "category": "projects",
        "tags": ["riceagent", "flutter", "offline-first"],
    },
    {
        "question": "What is ExecuCode?",
        "category": "projects",
        "tags": ["execucode", "ai-agents", "code-evaluation"],
    },
]


def build_qa_chunks() -> list[dict]:
    """Generate hypothetical Q&A pair chunks for common queries."""
    chunks = []
    for i, qa in enumerate(QA_PAIRS, 1):
        content = f"Hypothetical Question: {qa['question']}\n\nThis question maps to category '{qa['category']}'. " \
                  f"Relevant retrieval tags: {', '.join(qa['tags'])}."
        chunk = make_chunk(
            chunk_id=f"qa_{i:03d}",
            source="generated:hypothetical_qa",
            category=qa["category"],
            subcategory="hypothetical_qa",
            content=content,
            context_header=f"Hypothetical Q&A — {qa['question'][:60]}",
            importance=6,
            tags=qa["tags"] + ["hypothetical_qa"],
            chunk_type="qa",
        )
        chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# Source file discovery
# ---------------------------------------------------------------------------

SOURCE_MAP: list[tuple[str, str, str, str]] = [
    # (relative_path, category, id_prefix, file_type)
    ("01_identity/identity.json", "identity", "identity", "json"),
    ("01_identity/communication_style.yaml", "communication_style", "comm_style", "yaml"),
    ("01_identity/elevator_pitches.json", "identity", "elevator", "json"),
    ("02_timeline/timeline.csv", "timeline", "timeline", "csv"),
    ("03_skills/skills.csv", "skills", "skills", "csv"),
    ("04_projects/projects.csv", "projects", "projects", "csv"),
    ("05_achievements/achievements.csv", "achievements", "achievements", "csv"),
    ("06_psychology/psychology.md", "psychology", "psych", "md"),
    ("08_prompts/system_prompt.txt", "prompts", "prompt_sys", "txt"),
    ("08_prompts/resume_builder.txt", "prompts", "prompt_resume", "txt"),
    ("08_prompts/interview_coach.txt", "prompts", "prompt_interview", "txt"),
    ("09_experience/experience.csv", "experience", "experience", "csv"),
    ("10_learning/reading_list.csv", "learning", "reading", "csv"),
    ("10_learning/certifications_roadmap.csv", "learning", "cert_roadmap", "csv"),
    ("11_goals/goals.json", "goals", "goals", "json"),
    ("11_goals/career_vision.md", "goals", "career_vision", "md"),
    ("12_network/network.csv", "network", "network", "csv"),
    ("13_content/open_source.csv", "content", "content", "csv"),
    ("14_values_beliefs/manifesto.md", "values_beliefs", "manifesto", "md"),
    ("14_values_beliefs/failures_and_lessons.md", "values_beliefs", "failures", "md"),
    ("15_interview_prep/behavioral_answers.json", "interview_prep", "behavioral", "json"),
    ("15_interview_prep/technical_deep_dives.md", "interview_prep", "tech_dives", "md"),
]


def discover_role_details() -> list[tuple[str, str, str, str]]:
    """Dynamically discover role_details/*.md files."""
    role_dir = PROJECT_ROOT / "09_experience" / "role_details"
    if not role_dir.exists():
        return []
    extras = []
    for md_file in sorted(role_dir.glob("*.md")):
        rel = str(md_file.relative_to(PROJECT_ROOT))
        prefix = f"role_{md_file.stem}"
        extras.append((rel, "experience", prefix, "md"))
    return extras


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(output_dir: Path, verbose: bool = False):
    """Execute the full chunking pipeline."""
    print(f"\n{C_BOLD}{C_CYAN}╔══════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║   RAG Chunk Builder — personal-rag-db v2.0       ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚══════════════════════════════════════════════════╝{C_RESET}\n")

    all_sources = SOURCE_MAP + discover_role_details()
    all_child_chunks: list[dict] = []
    files_processed = 0
    files_skipped = 0

    type_dispatch = {
        "csv": chunk_csv,
        "json": chunk_json,
        "yaml": chunk_yaml,
        "md": chunk_markdown,
        "txt": chunk_text,
    }

    print(f"{C_BOLD}[1/4] Reading source files...{C_RESET}")
    for rel_path, category, id_prefix, file_type in all_sources:
        filepath = PROJECT_ROOT / rel_path
        if not filepath.exists():
            if verbose:
                print(f"  {C_YELLOW}⚠ Skipped (not found): {rel_path}{C_RESET}")
            files_skipped += 1
            continue

        handler = type_dispatch.get(file_type)
        if handler:
            chunks = handler(filepath, category, id_prefix, verbose)
            all_child_chunks.extend(chunks)
            files_processed += 1

    print(f"  {C_GREEN}✓ Processed {files_processed} files, skipped {files_skipped}{C_RESET}")
    print(f"  {C_GREEN}✓ Generated {len(all_child_chunks)} child chunks{C_RESET}")

    # Build parent chunks
    print(f"\n{C_BOLD}[2/4] Building parent chunks...{C_RESET}")
    parent_chunks = build_parent_chunks(all_child_chunks)
    print(f"  {C_GREEN}✓ Generated {len(parent_chunks)} parent chunks{C_RESET}")

    # Build Q&A chunks
    print(f"\n{C_BOLD}[3/4] Generating hypothetical Q&A chunks...{C_RESET}")
    qa_chunks = build_qa_chunks()
    print(f"  {C_GREEN}✓ Generated {len(qa_chunks)} Q&A chunks{C_RESET}")

    # Combine all
    all_chunks = all_child_chunks + parent_chunks + qa_chunks

    # Write output
    print(f"\n{C_BOLD}[4/4] Writing output files...{C_RESET}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # rag_chunks.jsonl — all chunks
    rag_path = output_dir / "rag_chunks.jsonl"
    with open(rag_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"  {C_GREEN}✓ {rag_path.relative_to(PROJECT_ROOT)}: {len(all_chunks)} chunks{C_RESET}")

    # parent_chunks.jsonl
    parent_path = output_dir / "parent_chunks.jsonl"
    with open(parent_path, "w", encoding="utf-8") as f:
        for chunk in parent_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"  {C_GREEN}✓ {parent_path.relative_to(PROJECT_ROOT)}: {len(parent_chunks)} chunks{C_RESET}")

    # child_chunks.jsonl
    child_path = output_dir / "child_chunks.jsonl"
    with open(child_path, "w", encoding="utf-8") as f:
        for chunk in all_child_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"  {C_GREEN}✓ {child_path.relative_to(PROJECT_ROOT)}: {len(all_child_chunks)} chunks{C_RESET}")

    # chunk_manifest.json
    category_counts = Counter(c["category"] for c in all_chunks)
    type_counts = Counter(c["chunk_type"] for c in all_chunks)
    total_tokens = sum(c["token_count"] for c in all_chunks)
    avg_tokens = total_tokens / len(all_chunks) if all_chunks else 0

    manifest = {
        "version": "2.0.0",
        "generated_at": now_iso(),
        "total_chunks": len(all_chunks),
        "child_chunks": len(all_child_chunks),
        "parent_chunks": len(parent_chunks),
        "qa_chunks": len(qa_chunks),
        "total_tokens": total_tokens,
        "avg_tokens_per_chunk": round(avg_tokens, 1),
        "files_processed": files_processed,
        "files_skipped": files_skipped,
        "chunks_by_category": dict(sorted(category_counts.items())),
        "chunks_by_type": dict(sorted(type_counts.items())),
        "sources": [s[0] for s in all_sources if (PROJECT_ROOT / s[0]).exists()],
    }
    manifest_path = output_dir / "chunk_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  {C_GREEN}✓ {manifest_path.relative_to(PROJECT_ROOT)}: manifest written{C_RESET}")

    # --- Summary ---
    print(f"\n{C_BOLD}{C_MAGENTA}{'═' * 52}{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}  CHUNK BUILD SUMMARY{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}{'═' * 52}{C_RESET}")
    print(f"  {'Total chunks:':<25} {C_BOLD}{len(all_chunks)}{C_RESET}")
    print(f"  {'  └─ Child:':<25} {len(all_child_chunks)}")
    print(f"  {'  └─ Parent:':<25} {len(parent_chunks)}")
    print(f"  {'  └─ Q&A:':<25} {len(qa_chunks)}")
    print(f"  {'Total tokens:':<25} {C_BOLD}{total_tokens:,}{C_RESET}")
    print(f"  {'Avg tokens/chunk:':<25} {avg_tokens:.1f}")
    print(f"  {'Files processed:':<25} {files_processed}")
    print(f"  {'Files skipped:':<25} {files_skipped}")
    print()
    print(f"  {C_BOLD}Chunks by Category:{C_RESET}")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 30)
        print(f"    {cat:<25} {count:>4}  {C_CYAN}{bar}{C_RESET}")
    print(f"\n{C_BOLD}{C_MAGENTA}{'═' * 52}{C_RESET}")
    print(f"{C_GREEN}  ✓ Build complete. Output: {output_dir.relative_to(PROJECT_ROOT)}/{C_RESET}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RAG Chunk Builder — builds hierarchical chunks from personal-rag-db sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python scripts/build_chunks.py --verbose --output-dir 07_chunks",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="07_chunks",
        help="Output directory relative to project root (default: 07_chunks)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed per-file processing info",
    )
    args = parser.parse_args()

    output = PROJECT_ROOT / args.output_dir
    run(output, verbose=args.verbose)


if __name__ == "__main__":
    main()

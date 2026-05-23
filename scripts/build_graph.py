#!/usr/bin/env python3
"""
build_graph.py — Knowledge Graph Builder
=========================================
Reads all source files from personal-rag-db and extracts entities and
relationships to build a structured knowledge graph.

Entity types: Person, Organization, Technology, Project, Skill,
              Certification, Role, Event, Location

Relationship types: USED_IN, WORKED_AT, BUILT, KNOWS, ACHIEVED,
                    LEARNED_FROM, STUDIED_AT, LOCATED_IN, PARTICIPATED_IN

Usage:
    python scripts/build_graph.py
    python scripts/build_graph.py --verbose
"""

import argparse
import csv
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
GRAPH_DIR = PROJECT_ROOT / "16_knowledge_graph"

PERSON_NAME = "Kankatala Ganesh Giridhar"

# ANSI colours
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_MAGENTA = "\033[95m"
C_DIM = "\033[2m"

# Known tech terms → Technology entities
KNOWN_TECH = {
    "Python", "Java", "JavaScript", "TypeScript", "Flutter", "Dart", "React",
    "Next.js", "Node.js", "Express.js", "FastAPI", "Docker", "PostgreSQL",
    "MySQL", "SQLite", "MongoDB", "Firebase", "Gemini API", "LangChain",
    "Pathway AI", "Riverpod", "Drift", "Tailwind CSS", "HTML", "CSS", "Git",
    "GitHub", "Kafka", "Spring Boot", "n8n", "Figma", "Azure", "AWS", "GCP",
    "Pandas", "NumPy", "TensorFlow", "PyTorch", "JavaFX", "Vite",
    "Google Maps API", "Canvas API", "Chart.js", "Helmet", "JWT",
    "Gemini", "OpenEnv", "GitHub Pages",
}

# Known organizations
KNOWN_ORGS = {
    "Amrita Vishwa Vidyapeetham", "Amrita University",
    "IIT Madras", "IIT Kharagpur",
    "CodSoft", "Unlox Academy", "Unlox",
    "Simplilearn", "Product Space", "Outskill",
    "IBM SkillsBuild", "IBM", "LetsUpgrade", "NSDC",
    "Sri Chaitanya", "Tirumala IIT Academy",
    "CodeChef", "Google", "Meta", "HDFC",
    "Ministry of Home Affairs",
}

# Known locations
KNOWN_LOCATIONS = {
    "Andhra Pradesh", "Visakhapatnam", "Nidadavolu", "Coimbatore",
    "Ramanathapuram", "Nediamanickam", "India", "Remote",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_entity_id(entity_type: str, name: str) -> str:
    """Create a deterministic entity ID."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"{entity_type.lower()}:{slug}"


def detect_csv_delimiter(filepath: Path) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        sample = f.read(2048)
    return "\t" if sample.count("\t") > sample.count(",") else ","


def read_csv_rows(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    delimiter = detect_csv_delimiter(filepath)
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            if any(v and v.strip() for v in row.values()):
                rows.append({k: (v.strip() if v else "") for k, v in row.items()})
    return rows


def read_json(filepath: Path):
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Entity & Relationship Storage
# ---------------------------------------------------------------------------

class GraphBuilder:
    def __init__(self):
        self.entities: dict[str, dict] = {}  # id → entity
        self.relationships: list[dict] = []
        self._rel_set: set[tuple] = set()  # dedup

    def add_entity(
        self,
        name: str,
        entity_type: str,
        properties: dict | None = None,
        source: str = "",
    ):
        eid = make_entity_id(entity_type, name)
        if eid not in self.entities:
            self.entities[eid] = {
                "id": eid,
                "name": name,
                "type": entity_type,
                "properties": properties or {},
                "sources": [source] if source else [],
            }
        else:
            if source and source not in self.entities[eid]["sources"]:
                self.entities[eid]["sources"].append(source)
            if properties:
                self.entities[eid]["properties"].update(properties)
        return eid

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: dict | None = None,
    ):
        key = (source_id, target_id, rel_type)
        if key not in self._rel_set:
            self._rel_set.add(key)
            self.relationships.append({
                "source": source_id,
                "target": target_id,
                "type": rel_type,
                "properties": properties or {},
            })

    # -----------------------------------------------------------------------
    # Extraction from identity
    # -----------------------------------------------------------------------
    def extract_identity(self):
        filepath = PROJECT_ROOT / "01_identity" / "identity.json"
        data = read_json(filepath)
        if not data:
            return

        person_id = self.add_entity(
            PERSON_NAME, "Person",
            properties={
                "role": data.get("role", ""),
                "location": data.get("location", ""),
                "primary_technical_identity": data.get("primary_technical_identity", ""),
                "value_proposition": data.get("value_proposition", ""),
            },
            source="01_identity/identity.json",
        )

        # Education
        edu_list = data.get("education", [])
        if isinstance(edu_list, list):
            for edu in edu_list:
                inst = edu.get("institution")
                if inst:
                    uni_id = self.add_entity(
                        inst, "Organization",
                        properties={"type": "academic_institution", "level": edu.get("level", "")},
                        source="01_identity/identity.json",
                    )
                    self.add_relationship(person_id, uni_id, "STUDIED_AT", {
                        "years": edu.get("years", ""),
                        "notes": edu.get("notes", ""),
                    })

        # Location
        loc_str = data.get("location", "")
        for loc in KNOWN_LOCATIONS:
            if loc.lower() in loc_str.lower():
                loc_id = self.add_entity(loc, "Location", source="01_identity/identity.json")
                self.add_relationship(person_id, loc_id, "LOCATED_IN")

    # -----------------------------------------------------------------------
    # Extraction from timeline
    # -----------------------------------------------------------------------
    def extract_timeline(self):
        rows = read_csv_rows(PROJECT_ROOT / "02_timeline" / "timeline.csv")
        person_id = make_entity_id("Person", PERSON_NAME)

        for row in rows:
            event_name = row.get("event_name", "").strip()
            category = row.get("category", "").strip()
            location = row.get("location", "").strip()
            start = row.get("start_date", "")
            end = row.get("end_date", "")

            if not event_name:
                continue

            # Add event
            event_id = self.add_entity(
                event_name, "Event",
                properties={
                    "category": category,
                    "start_date": start,
                    "end_date": end,
                    "description": row.get("description", ""),
                },
                source="02_timeline/timeline.csv",
            )
            self.add_relationship(person_id, event_id, "PARTICIPATED_IN", {
                "start_date": start, "end_date": end,
            })

            # Location
            if location:
                for loc_part in re.split(r"[/,]", location):
                    loc_clean = loc_part.strip()
                    if loc_clean and loc_clean != "-":
                        loc_id = self.add_entity(loc_clean, "Location", source="02_timeline/timeline.csv")
                        self.add_relationship(event_id, loc_id, "LOCATED_IN")

            # Check for org references
            for org in KNOWN_ORGS:
                if org.lower() in event_name.lower() or org.lower() in row.get("description", "").lower():
                    org_id = self.add_entity(org, "Organization", source="02_timeline/timeline.csv")
                    if "intern" in category.lower() or "work" in category.lower():
                        self.add_relationship(person_id, org_id, "WORKED_AT", {
                            "start_date": start, "end_date": end,
                        })
                    elif "education" in category.lower():
                        self.add_relationship(person_id, org_id, "STUDIED_AT")

    # -----------------------------------------------------------------------
    # Extraction from skills
    # -----------------------------------------------------------------------
    def extract_skills(self):
        rows = read_csv_rows(PROJECT_ROOT / "03_skills" / "skills.csv")
        person_id = make_entity_id("Person", PERSON_NAME)

        for row in rows:
            skill_name = row.get("skill_name", "").strip()
            if not skill_name:
                continue

            skill_id = self.add_entity(
                skill_name, "Skill",
                properties={
                    "category": row.get("category", ""),
                    "proficiency": row.get("proficiency", ""),
                    "description": row.get("description", ""),
                    "last_used": row.get("last_used", ""),
                },
                source="03_skills/skills.csv",
            )
            self.add_relationship(person_id, skill_id, "KNOWS", {
                "proficiency": row.get("proficiency", ""),
            })

            # Extract tech from tools_frameworks
            tools = row.get("tools_frameworks", "")
            if tools and tools != "-":
                for tool_raw in re.split(r"[,/]", tools):
                    tool = tool_raw.strip()
                    if tool and len(tool) > 1:
                        # Match against known tech
                        matched = False
                        for known in KNOWN_TECH:
                            if known.lower() == tool.lower() or tool.lower().startswith(known.lower().split()[0]):
                                tech_id = self.add_entity(known, "Technology", source="03_skills/skills.csv")
                                self.add_relationship(skill_id, tech_id, "USED_IN")
                                matched = True
                                break
                        if not matched and len(tool) > 2:
                            tech_id = self.add_entity(tool, "Technology", source="03_skills/skills.csv")
                            self.add_relationship(skill_id, tech_id, "USED_IN")

    # -----------------------------------------------------------------------
    # Extraction from projects
    # -----------------------------------------------------------------------
    def extract_projects(self):
        rows = read_csv_rows(PROJECT_ROOT / "04_projects" / "projects.csv")
        person_id = make_entity_id("Person", PERSON_NAME)

        for row in rows:
            proj_name = row.get("project_name", "").strip()
            if not proj_name:
                continue

            proj_id = self.add_entity(
                proj_name, "Project",
                properties={
                    "repository": row.get("repository", ""),
                    "description": row.get("description", ""),
                    "key_features": row.get("key_features", ""),
                    "importance_score": row.get("importance_score (1-10)", ""),
                },
                source="04_projects/projects.csv",
            )
            self.add_relationship(person_id, proj_id, "BUILT")

            # Tech stack
            tech_stack = row.get("tech_stack", "")
            if tech_stack:
                for tech_raw in re.split(r"[,/()]", tech_stack):
                    tech = tech_raw.strip()
                    if tech and len(tech) > 1 and tech != "-":
                        for known in KNOWN_TECH:
                            if known.lower() == tech.lower() or tech.lower() in known.lower():
                                tech_id = self.add_entity(known, "Technology", source="04_projects/projects.csv")
                                self.add_relationship(proj_id, tech_id, "USED_IN")
                                break
                        else:
                            if len(tech) > 2:
                                tech_id = self.add_entity(tech, "Technology", source="04_projects/projects.csv")
                                self.add_relationship(proj_id, tech_id, "USED_IN")

    # -----------------------------------------------------------------------
    # Extraction from achievements
    # -----------------------------------------------------------------------
    def extract_achievements(self):
        rows = read_csv_rows(PROJECT_ROOT / "05_achievements" / "achievements.csv")
        person_id = make_entity_id("Person", PERSON_NAME)

        for row in rows:
            ach_name = row.get("achievement_name", "").strip()
            if not ach_name:
                continue

            category = row.get("category", "").strip()
            issuer = row.get("issuer", "").strip()

            if "certification" in category.lower():
                ach_id = self.add_entity(
                    ach_name, "Certification",
                    properties={
                        "issuer": issuer,
                        "date": row.get("date", ""),
                        "credential_id": row.get("credential_id", ""),
                        "description": row.get("description", ""),
                    },
                    source="05_achievements/achievements.csv",
                )
                self.add_relationship(person_id, ach_id, "ACHIEVED")

                # Issuer org
                if issuer and issuer != "-":
                    # Split composite issuers
                    for org_part in re.split(r"[,&]", issuer):
                        org_clean = org_part.strip()
                        if org_clean and org_clean != "-":
                            org_id = self.add_entity(org_clean, "Organization", source="05_achievements/achievements.csv")
                            self.add_relationship(ach_id, org_id, "LEARNED_FROM")
            else:
                # Hackathon, badge, etc.
                event_id = self.add_entity(
                    ach_name, "Event",
                    properties={
                        "category": category,
                        "issuer": issuer,
                        "date": row.get("date", ""),
                        "description": row.get("description", ""),
                    },
                    source="05_achievements/achievements.csv",
                )
                self.add_relationship(person_id, event_id, "PARTICIPATED_IN")

                if issuer and issuer != "-":
                    for org_part in re.split(r"[,&]", issuer):
                        org_clean = org_part.strip()
                        if org_clean and org_clean != "-":
                            org_id = self.add_entity(org_clean, "Organization", source="05_achievements/achievements.csv")
                            self.add_relationship(event_id, org_id, "LOCATED_IN")

    # -----------------------------------------------------------------------
    # Extraction from experience (if exists)
    # -----------------------------------------------------------------------
    def extract_experience(self):
        rows = read_csv_rows(PROJECT_ROOT / "09_experience" / "experience.csv")
        person_id = make_entity_id("Person", PERSON_NAME)

        for row in rows:
            role_title = row.get("role_title", row.get("title", "")).strip()
            company = row.get("company", row.get("organization", "")).strip()
            if not role_title:
                continue

            role_id = self.add_entity(
                role_title, "Role",
                properties={
                    "company": company,
                    "start_date": row.get("start_date", ""),
                    "end_date": row.get("end_date", ""),
                    "description": row.get("description", ""),
                },
                source="09_experience/experience.csv",
            )
            self.add_relationship(person_id, role_id, "WORKED_AT")

            if company and company != "-":
                org_id = self.add_entity(company, "Organization", source="09_experience/experience.csv")
                self.add_relationship(role_id, org_id, "WORKED_AT")

    # -----------------------------------------------------------------------
    # Run all extractors
    # -----------------------------------------------------------------------
    def build(self, verbose: bool = False):
        extractors = [
            ("Identity", self.extract_identity),
            ("Timeline", self.extract_timeline),
            ("Skills", self.extract_skills),
            ("Projects", self.extract_projects),
            ("Achievements", self.extract_achievements),
            ("Experience", self.extract_experience),
        ]
        for name, fn in extractors:
            before_e = len(self.entities)
            before_r = len(self.relationships)
            fn()
            new_e = len(self.entities) - before_e
            new_r = len(self.relationships) - before_r
            if verbose:
                print(f"  {C_DIM}├── {name}: +{new_e} entities, +{new_r} relationships{C_RESET}")

    def export(self) -> tuple[list[dict], list[dict]]:
        entities = list(self.entities.values())
        return entities, self.relationships


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(verbose: bool = False):
    print(f"\n{C_BOLD}{C_CYAN}╔══════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║   Knowledge Graph Builder — personal-rag-db      ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚══════════════════════════════════════════════════╝{C_RESET}\n")

    builder = GraphBuilder()

    print(f"{C_BOLD}[1/3] Extracting entities and relationships...{C_RESET}")
    builder.build(verbose=verbose)

    entities, relationships = builder.export()

    print(f"\n{C_BOLD}[2/3] Writing graph files...{C_RESET}")
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    ent_path = GRAPH_DIR / "entities.json"
    with open(ent_path, "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    print(f"  {C_GREEN}✓ entities.json: {len(entities)} entities{C_RESET}")

    rel_path = GRAPH_DIR / "relationships.json"
    with open(rel_path, "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=2, ensure_ascii=False)
    print(f"  {C_GREEN}✓ relationships.json: {len(relationships)} relationships{C_RESET}")

    # --- Summary ---
    print(f"\n{C_BOLD}[3/3] Graph Summary{C_RESET}")
    type_counts = Counter(e["type"] for e in entities)
    rel_counts = Counter(r["type"] for r in relationships)

    print(f"\n{C_BOLD}{C_MAGENTA}{'═' * 52}{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}  KNOWLEDGE GRAPH SUMMARY{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}{'═' * 52}{C_RESET}")
    print(f"  {'Total entities:':<25} {C_BOLD}{len(entities)}{C_RESET}")
    print(f"  {'Total relationships:':<25} {C_BOLD}{len(relationships)}{C_RESET}")
    print()

    print(f"  {C_BOLD}Entities by Type:{C_RESET}")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 30)
        print(f"    {etype:<20} {count:>4}  {C_CYAN}{bar}{C_RESET}")

    print()
    print(f"  {C_BOLD}Relationships by Type:{C_RESET}")
    for rtype, count in sorted(rel_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 30)
        print(f"    {rtype:<20} {count:>4}  {C_CYAN}{bar}{C_RESET}")

    print(f"\n{C_BOLD}{C_MAGENTA}{'═' * 52}{C_RESET}")
    print(f"{C_GREEN}  ✓ Graph build complete. Output: 16_knowledge_graph/{C_RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Graph Builder — extracts entities and relationships from personal-rag-db.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed extraction info")
    args = parser.parse_args()
    run(verbose=args.verbose)


if __name__ == "__main__":
    main()

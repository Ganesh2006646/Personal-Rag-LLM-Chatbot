# Personal RAG Database — Kankatala Ganesh Giridhar (v2.0.0)

This repository contains the structured, production-grade knowledge base and processing pipeline for an AI-powered digital twin representing **Kankatala Ganesh Giridhar**. It is optimized for retrieval-augmented generation (RAG), intent-based query routing, hierarchical semantic search, and authentic personality emulation.

---

## 1. High-End System Architecture

This database is structured to support multi-faceted search (dense semantic search, sparse keyword search, and graph traversal) to answer personal, technical, and behavioral questions with absolute accuracy.

```mermaid
graph TD
    subgraph Raw Data Source (01–15)
        JSON[JSON Files: bio, goals, prep]
        CSV[CSV Files: timeline, skills, experience]
        YAML[YAML Files: comm_style]
        MD[Markdown: psychology, deep dives]
    end

    subgraph Processing Pipeline (scripts/)
        VAL[validate_schema.py] -->|Checks integrity & TODOs| RUN[build_chunks.py]
        RUN -->|Hierarchical Chunking| CHUNKS[07_chunks/]
        GRAPH[build_graph.py] -->|Extracts Entities/Rels| KG[16_knowledge_graph/]
    end

    subgraph RAG Retrieval Engine
        ROUTER[18_query_router/router_config.json] -->|Classifies intent| INDEX[18_query_router/index_map.json]
        INDEX -->|DENSE search| VECTOR[17_embeddings/config.json]
        INDEX -->|SPARSE search| KEYWORD[BM25 Engine]
        INDEX -->|GRAPH search| KG
    end

    Raw Data Source --> Processing Pipeline
    CHUNKS -->|Embeddings| VECTOR
```

---

## 2. Directory Layout & File Catalog

The repository is organized into 18 logical layers:

```
personal-rag-db/
├── 01_identity/                 # Core identity and communications
│   ├── identity.json            # Name, contact info, education, and social URLs
│   ├── communication_style.yaml # Writing rules, tone, and audience profiles
│   └── elevator_pitches.json    # Adaptable personal pitches (30s, 2m, tech, casual)
├── 02_timeline/                 # Chronological milestones
│   └── timeline.csv             # 20+ chronological life/career events
├── 03_skills/                   # Detailed competence catalog
│   └── skills.csv               # 23+ skills with proficiency levels (1-5) and evidence
├── 04_projects/                 # Tech stack and project specifications
│   └── projects.csv             # 15 projects with metrics, roles, and importance
├── 05_achievements/             # Awards and official records
│   └── achievements.csv         # Certificates, competition scores, and awards
├── 06_psychology/               # Cognitive and personality profiles
│   └── psychology.md            # Mindset, linear paradigm, and motivators
├── 07_chunks/                   # Processed outputs for Vector DB import
│   ├── rag_chunks.jsonl         # All chunks (child + parent + Q&A)
│   ├── child_chunks.jsonl       # Fine-grained chunks (200-400 tokens)
│   ├── parent_chunks.jsonl      # Aggregated context chunks (512-1024 tokens)
│   └── chunk_manifest.json      # Processing statistics and checksums
├── 08_prompts/                  # Production-ready LLM system instructions
│   ├── system_prompt.txt        # Core prompt with in-context examples & guardrails
│   ├── resume_builder.txt       # ATS-optimized resume generator instructions
│   └── interview_coach.txt      # Interactive interview prep coach instructions
├── 09_experience/               # Professional history
│   ├── experience.csv           # Work, internship, and research positions
│   └── role_details/            # In-depth logs for key career milestones
│       ├── codsoft.md           # MERN-stack internship breakdown
│       └── live_in_labs.md      # Sustainable rural research details
├── 10_learning/                 # Courses, workshops, and readings
│   ├── reading_list.csv         # Educational courses, self-study, and ratings
│   └── certifications_roadmap.csv # Active roadmap for certifications (e.g., Azure)
├── 11_goals/                    # Professional and personal targets
│   ├── goals.json               # Short (6m), mid (1-2y), and long-term (5y) roadmap
│   └── career_vision.md         # Narrative 5-year vision and value proposition
├── 12_network/                  # Professional relationships (Anonymized)
│   └── network.csv              # Mentors, professors, and partners (gitignored)
├── 13_content/                  # Open-source presence
│   └── open_source.csv          # Index of public GitHub repositories
├── 14_values_beliefs/           # Engineering ethics and philosophies
│   ├── manifesto.md             # The Linear Paradigm and Engineering Morality
│   └── failures_and_lessons.md  # Setbacks analyzed using the STAR-L framework
├── 15_interview_prep/           # Human resources and technical prep kits
│   ├── behavioral_answers.json  # 10 HR behavioral questions with STAR answers
│   └── technical_deep_dives.md  # Detailed design architecture diagrams and explanations
├── 16_knowledge_graph/          # Graph database mappings
│   ├── entities.json            # Extracted node metadata (Person, Org, Tech, etc.)
│   ├── relationships.json       # Directed edges (BUILT, USED_IN, KNOWS, etc.)
│   └── graph_schema.json        # Node and edge schema validation criteria
├── 17_embeddings/               # Embeddings settings
│   └── config.json              # Model, dimensional, and database recommendations
├── 18_query_router/             # Retrieval routing logic
│   ├── router_config.json       # Query intent classifications and mappings
│   └── index_map.json           # Dense/Sparse vector index mapping rules
├── schemas/                     # Validation schemas
│   ├── identity.schema.json     # JSON schema for validating identity.json
│   └── chunks.schema.json       # JSON schema for validating individual chunks
├── scripts/                     # Automation scripts
│   ├── build_chunks.py          # Processes source files into parent/child/QA chunks
│   ├── build_graph.py           # Generates knowledge graph entities and relationships
│   ├── validate_schema.py       # Validates structural integrity and checks for TODOs
│   └── stats.py                 # Outputs a visual database statistics summary
├── CHANGELOG.md                 # Project version control changelog
└── README.md                    # Project documentation (this file)
```

---

## 3. Automation Scripts & Pipelines

All scripts are written in standard Python 3 with zero external dependencies to ensure ease of deployment.

### Validate Data Files
Before generating chunks or building the graph, validate that the database is free of placeholders, uses proper CSV delimiters, and follows ISO date formats:
```bash
python scripts/validate_schema.py
```

### Build RAG Chunks
Build child, parent, and hypothetical Q&A chunks with metadata, temporal stamps, token estimates, and SHA-256 checksums:
```bash
# Basic run
python scripts/build_chunks.py

# Verbose run showing all files processed
python scripts/build_chunks.py --verbose
```

### Extract Knowledge Graph
Extract entities and relationships from files to build a structured graph:
```bash
python scripts/build_graph.py
```

### Review Database Statistics
Generate a completion report and chunk distribution heatmap:
```bash
python scripts/stats.py
```

---

## 4. Verification and Schema Checks

The database includes built-in quality control metrics:
* **Date Formats:** All dates are in strict ISO 8601 (`YYYY-MM-DD`, `YYYY-MM`, or `YYYY`).
* **CSV Standard:** Standard commas `,` are used as delimiters with proper quotes, and pipes `|` are used as list delimiters inside columns.
* **No Placeholders:** Checked for any empty values or standard `TODO` and `placeholder` keywords to ensure all retrieved answers are grounded in real data.
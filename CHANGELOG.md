# Changelog

All notable changes to the Personal RAG Database project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-05-23

### Added
- **Expanded Architecture (Categories 09-18):**
  - Added structured experience records: `09_experience/experience.csv`, `codsoft.md`, and `live_in_labs.md`.
  - Added reading lists and certifications: `10_learning/reading_list.csv` and `certifications_roadmap.csv`.
  - Added goal tracking and career visions: `11_goals/goals.json` and `career_vision.md`.
  - Added personal and professional contacts: `12_network/network.csv`.
  - Added open-source code index: `13_content/open_source.csv`.
  - Added core beliefs and failure logs: `14_values_beliefs/manifesto.md` and `failures_and_lessons.md` (STAR-L).
  - Added interview preparation kits: `15_interview_prep/behavioral_answers.json` and `technical_deep_dives.md` (with architectural diagrams).
  - Added knowledge graph schema: `16_knowledge_graph/graph_schema.json`.
  - Added vector search embedding recommendations: `17_embeddings/config.json`.
  - Added routing templates: `18_query_router/router_config.json` and `index_map.json`.
- **Infrastructure Scripts:**
  - `scripts/build_chunks.py`: Automates the parsing and chunking of JSON, CSV, YAML, and Markdown files into child, parent, and Q&A chunks, generating token estimates and manifests.
  - `scripts/build_graph.py`: Parses all source files to extract entities (Person, Org, Tech, etc.) and relationships (BUILT, WORKED_AT, KNOWS, etc.).
  - `scripts/validate_schema.py`: Verifies CSV headers, ISO dates, pipe tags, and checks for placeholder TODO values.
  - `scripts/stats.py`: Prints statistics on files, chunks, and token counts.
- **Enhanced System Prompts:**
  - Added `08_prompts/system_prompt.txt`: Production system prompt with in-context examples.
  - Added `08_prompts/resume_builder.txt`: Prompt for tailoring ATS-optimized resumes.
  - Added `08_prompts/interview_coach.txt`: Interactive coaching prompt.

### Changed
- Standardized all CSV delimiters to commas.
- Upgraded formatting across all directories to conform to strict, machine-readable validation schemas.

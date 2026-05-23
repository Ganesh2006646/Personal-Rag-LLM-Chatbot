# 🧠 Personal RAG Database & Chatbot Engine — Kankatala Ganesh Giridhar

> **Production knowledge base powering a live, highly-personalized AI Digital Twin at [brandofganesh.vercel.app](https://brandofganesh.vercel.app)**

This repository houses the structured personal database and high-performance pipeline driving Ganesh's AI Digital Twin. It is optimized for retrieval-augmented generation (RAG), context-aware personalization, and edge-optimized serverless execution.

---

## ⚡ Serverless RAG Architecture

The chatbot is built entirely around an **on-demand, zero-cost Serverless RAG** design. Instead of paying for a 24/7 running server and a heavy vector database subscription, the backend runs instantly within Vercel's serverless function constraints:

```
┌────────────────────────────┐
│    Portfolio Frontend      │
│  brandofganesh.vercel.app  │ (HTML / CSS / JS Chat Widget)
└────────────┬───────────────┘
             │ POST /api/chat { message, history, visitorInfo }
             ▼
┌────────────────────────────┐
│  Vercel Serverless Function │
│       api/chat.js          │
│  ┌──────────────────────┐  │
│  │ 1. Embed query       │  │ (gemini-embedding-2)
│  │ 2. Cosine similarity │  │ (in-memory search over vectors.json)
│  │ 3. Top-8 retrieval   │  │ (RAG context compilation)
│  │ 4. Gemini 2.5 Flash  │  │ (SSE streaming response)
│  └──────────────────────┘  │
│                            │
│  data/vectors.json (24.8MB)│ (399 chunks pre-embedded)
└────────────────────────────┘
```

### Why Serverless RAG?
* **Zero Infrastructure Cost**: Scaled down to $0/month. You only pay for active execution time, making it ideal for portfolio chatbots.
* **In-Memory Speed**: The pre-embedded database (`vectors.json`) loads directly into the serverless container's RAM. Cosine similarity calculations happen in **sub-milliseconds** with no external database network lag.
* **Stream Delivery**: Utilizes **Server-Sent Events (SSE)** to stream the response back token-by-token for a premium, real-time typing interface.

---

## 🤖 Advanced Chatbot Features

Your digital twin features state-of-the-art personalization, UX resilience, and secure routing:

### 1. ⚡ Onboarding & Role-Aware Greetings
* The widget collects the visitor’s **Name** and **Role** (Recruiter, Developer, Student).
* The profile is passed dynamically to the Vercel backend and appended to the Gemini system instructions.
* The AI Twin adapts its tone and opening pitch specifically to the visitor:
  * **Recruiters**: Warm and professional, highlighting project metrics, commercial impact, and availability.
  * **Developers**: Peer-to-peer technical deep-dives about compiler logic, offline sync queues, and database schemas.
  * **Students**: Helpful mentorship advice about hackathons, learning tracks, and campus life.

### 2. ⚡ Smart Quick-Replies (Onboarding Skip)
* High-intent action chips (`🚀 See Projects`, `📞 Contact Ganesh`, `💼 View LinkedIn`) are embedded on both the onboarding and welcome screens.
* Clicking any chip instantly skips form-filling, logs the visitor, and fires the request immediately for zero-friction access.

### 3. 🔗 Smart Same-Window Redirection
* All markdown links in the chat are inspected dynamically.
* Same-site links (like `#about`, `work.html`, or local hashes) load seamlessly in the **existing tab (`target="_self"`)**, preserving user experience.
* External links (GitHub repos, LinkedIn profiles) open safely in a **new tab (`target="_blank"`)**.

### 4. 🛡️ Resilient AI Limit Interceptor
* If the Gemini API experiences a 429 quota rate limit or network timeout, the client intercepts the failure gracefully.
* Instead of displaying standard console logs or red errors, it outputs a charming, witty AI message redirecting the visitor smoothly to alternate contact pages.

---

## 📊 Database & Knowledge Graph Stats

The knowledge base compiles **35 source documents** (including your full resume, hackathon entries, engineering manifesto, and 10 LinkedIn data CSVs) into optimized structures.

### 1. Chunk Pipeline Statistics
Running `build_chunks.py` processes raw data into semantic chunks:

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Total Chunks** | **399** | Complete retrieval nodes |
| Child Chunks | 344 | Fine-grained (200–400 tokens) |
| Parent Chunks | 40 | Macro context (512–1024 tokens) |
| Hypothetical Q&As | 15 | AI intent prediction pairs |
| **Total Tokens** | **58,861** | Dense semantic catalog |
| Total Categories | 17 | Categorized RAG routes (identity, projects, linkedin, timeline) |

### 2. Knowledge Graph Mappings
We construct a directed Graph Database (`entities.json` + `relationships.json`) mapping your professional universe:

| Metric | Count | Description |
| :--- | :--- | :--- |
| **Total Nodes (Entities)** | **109** | Skills, projects, roles, certifications, organizations, hackathons |
| **Total Edges (Relationships)** | **110** | Directed linkages (`BUILT`, `USED_IN`, `WORKED_AT`, `KNOWS`) |

---

## 🛠️ Data Pipeline Pipeline Scripts

Written in Python 3 with **zero external dependencies** for maximum portability:

```bash
# 1. Validate data schemas, date formats, and check for placeholders
python scripts/validate_schema.py

# 2. Build child, parent, and hypothetical chunks with SHA-256 integrity checks
python scripts/build_chunks.py

# 3. Extract entities and relationships to compile the Knowledge Graph
python scripts/build_graph.py

# 4. Generate comprehensive database statistics and heatmap
python scripts/stats.py

# 5. Embed chunks to compile vectors (requires GEMINI_API_KEY)
python scripts/generate_embeddings.py --api-key YOUR_API_KEY
```

---

## 🎨 Technology Stack

* **LLM Engine**: Google Gemini 2.5 Flash
* **Vector Models**: Google Gemini Embedding (`gemini-embedding-2`)
* **Similarity Metric**: Cosine Similarity (In-Memory execution)
* **API Delivery**: Serverless Function (Vercel Node.js Edge)
* **Real-time UX**: Server-Sent Events (SSE stream protocol)
* **Client Widget**: Self-contained Vanilla HTML/CSS/JS

---

<p align="center">
  <strong>Built with 🧠 by <a href="https://brandofganesh.vercel.app">Kankatala Ganesh Giridhar</a></strong><br/>
  <em>The Linear Paradigm — consistent daily execution over manufactured turning points.</em>
</p>
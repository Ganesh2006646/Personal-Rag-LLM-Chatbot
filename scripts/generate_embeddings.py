#!/usr/bin/env python3
"""
generate_embeddings.py — Generates local vector store for in-memory RAG
======================================================================
Reads 07_chunks/rag_chunks.jsonl, calls Gemini text-embedding-004 API,
and writes vectors and payloads to portfolio-chatbot/src/data/vectors.json.

Usage:
    python scripts/generate_embeddings.py --api-key <GEMINI_API_KEY>
"""

import argparse
import json
import urllib.request
import urllib.error
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "portfolio-chatbot" / "src" / "data" / "vectors.json"

def get_embedding(text: str, api_key: str) -> list[float]:
    """Generate vector embedding using Gemini API text-embedding-004."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text}]
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode("utf-8"))
                return data["embedding"]["values"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                sleep_time = (2 ** attempt) + 1
                print(f"    Rate limit hit. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise e
    raise Exception("Failed to generate embedding after retries.")

def main():
    parser = argparse.ArgumentParser(description="Generate local vector embeddings.")
    parser.add_argument("--api-key", required=True, help="Gemini API Key")
    args = parser.parse_args()
    
    chunks_file = PROJECT_ROOT / "07_chunks" / "rag_chunks.jsonl"
    if not chunks_file.exists():
        print(f"Chunks file not found at: {chunks_file}")
        print("Please run 'python scripts/build_chunks.py' first.")
        return

    # 1. Read chunks
    print("[1/3] Reading rag_chunks.jsonl...")
    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line.strip()))
    print(f"  ✓ Read {len(chunks)} chunks.")

    # 2. Embed each chunk
    print("[2/3] Generating embeddings...")
    vector_db = []
    
    for i, chunk in enumerate(chunks, 1):
        chunk_id = chunk["chunk_id"]
        content = chunk["content"]
        
        print(f"  ({i}/{len(chunks)}) Embedding: {chunk_id}...", end="", flush=True)
        try:
            vector = get_embedding(content, args.api_key)
            print(" Done.")
        except Exception as e:
            print(f" Failed: {str(e)}")
            continue
            
        vector_db.append({
            "id": chunk_id,
            "vector": vector,
            "payload": {
                "chunk_id": chunk_id,
                "source": chunk.get("source", ""),
                "category": chunk.get("category", ""),
                "subcategory": chunk.get("subcategory", ""),
                "content": content,
                "context_header": chunk.get("context_header", ""),
                "importance": chunk.get("importance", 5),
                "tags": chunk.get("tags", []),
                "chunk_type": chunk.get("chunk_type", "child"),
                "child_chunk_ids": chunk.get("child_chunk_ids", [])
            }
        })
        # Sleep slightly to stay within default API limits
        time.sleep(0.5)

    # 3. Write to JSON
    print(f"[3/3] Saving vector store to: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(vector_db, f, indent=2, ensure_ascii=False)
        
    print("✓ Vector database generated successfully.")

if __name__ == "__main__":
    main()

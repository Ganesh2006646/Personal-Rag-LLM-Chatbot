#!/usr/bin/env python3
"""
sync_qdrant.py — Synchronizes personal-rag-db chunks with Qdrant Cloud
======================================================================
Reads 07_chunks/rag_chunks.jsonl, generates embeddings using the Gemini API,
and uploads them to Qdrant Cloud.

Usage:
    python scripts/sync_qdrant.py --api-key <GEMINI_API_KEY> --qdrant-url <QDRANT_URL> --qdrant-key <QDRANT_API_KEY>
"""

import argparse
import hashlib
import json
import urllib.request
import urllib.error
import uuid
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECTION_NAME = "personal_rag_db"

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
    
    # Simple retry logic for rate limits
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

def qdrant_request(endpoint: str, payload: dict | None, qdrant_url: str, qdrant_key: str, method: str = "POST") -> dict:
    """Send requests to the Qdrant REST API."""
    # Ensure qdrant_url ends without slash
    qdrant_url = qdrant_url.rstrip("/")
    url = f"{qdrant_url}/{endpoint.lstrip('/')}"
    
    headers = {
        "Content-Type": "application/json"
    }
    if qdrant_key:
        headers["api-key"] = qdrant_key
        
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers,
        method=method
    )
    
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def sync(gemini_key: str, qdrant_url: str, qdrant_key: str):
    chunks_file = PROJECT_ROOT / "07_chunks" / "rag_chunks.jsonl"
    if not chunks_file.exists():
        print(f"Chunks file not found at: {chunks_file}")
        print("Please run 'python scripts/build_chunks.py' first.")
        return

    # 1. Read chunks
    print("[1/4] Reading rag_chunks.jsonl...")
    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line.strip()))
    print(f"  ✓ Read {len(chunks)} chunks.")

    # 2. Setup Qdrant Collection
    print(f"[2/4] Initializing Qdrant collection '{COLLECTION_NAME}'...")
    try:
        # Check if collection exists
        col_info = qdrant_request(f"collections/{COLLECTION_NAME}", None, qdrant_url, qdrant_key, "GET")
        print("  ✓ Collection already exists.")
    except Exception:
        # Create collection (768 dimensions for text-embedding-004, cosine distance)
        payload = {
            "vectors": {
                "size": 768,
                "distance": "Cosine"
            }
        }
        qdrant_request(f"collections/{COLLECTION_NAME}", payload, qdrant_url, qdrant_key, "PUT")
        print(f"  ✓ Created collection '{COLLECTION_NAME}' with 768 dims (Cosine).")

    # 3. Generate Embeddings & Batch Upload
    print("[3/4] Generating embeddings and upserting points...")
    points = []
    batch_size = 20
    
    for i, chunk in enumerate(chunks, 1):
        chunk_id = chunk["chunk_id"]
        content = chunk["content"]
        
        print(f"  ({i}/{len(chunks)}) Embedding: {chunk_id}...", end="", flush=True)
        try:
            vector = get_embedding(content, gemini_key)
            print(" Done.")
        except Exception as e:
            print(f" Failed: {str(e)}")
            continue
            
        # Generate a stable UUID from chunk_id
        point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
        
        # Build payload metadata
        meta = {
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
        
        points.append({
            "id": point_uuid,
            "vector": vector,
            "payload": meta
        })
        
        # Upload batch
        if len(points) >= batch_size or i == len(chunks):
            print(f"  --> Upserting batch of {len(points)} to Qdrant...", end="", flush=True)
            payload = {
                "points": points
            }
            qdrant_request(f"collections/{COLLECTION_NAME}/points?wait=true", payload, qdrant_url, qdrant_key, "PUT")
            print(" Completed.")
            points = []
            
    print(f"\n[4/4] Sync complete. {len(chunks)} chunks uploaded to Qdrant Cloud.")

def main():
    parser = argparse.ArgumentParser(description="Upload personal RAG chunks to Qdrant Cloud.")
    parser.add_argument("--api-key", required=True, help="Gemini API Key")
    parser.add_argument("--qdrant-url", required=True, help="Qdrant Cluster URL")
    parser.add_argument("--qdrant-key", required=True, help="Qdrant API Key")
    args = parser.parse_args()
    
    sync(args.api_key, args.qdrant_url, args.qdrant_key)

if __name__ == "__main__":
    main()

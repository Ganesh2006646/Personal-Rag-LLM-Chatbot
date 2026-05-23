#!/usr/bin/env python3
"""
stats.py — Personal RAG Database Stats Reporter
================================================
Counts files, total chunks, tokens, completeness, and displays a summary table.
"""

import json
import sys
from pathlib import Path

# Reconfigure stdout to use UTF-8 to prevent encoding errors on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


PROJECT_ROOT = Path(__file__).resolve().parent.parent

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_MAGENTA = "\033[95m"

def main():
    manifest_path = PROJECT_ROOT / "07_chunks" / "chunk_manifest.json"
    
    print(f"\n{C_BOLD}{C_CYAN}╔══════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║   personal-rag-db Database Statistics            ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚══════════════════════════════════════════════════╝{C_RESET}\n")

    if not manifest_path.exists():
        print(f"Manifest file not found at: {manifest_path}")
        print("Please run 'python scripts/build_chunks.py' first to generate chunks and the manifest.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"  {'Database Version:':<25} {C_BOLD}{manifest.get('version', 'N/A')}{C_RESET}")
    print(f"  {'Generated At:':<25} {manifest.get('generated_at', 'N/A')}")
    print(f"  {'Files Processed:':<25} {manifest.get('files_processed', 0)}")
    print(f"  {'Files Skipped:':<25} {manifest.get('files_skipped', 0)}")
    print(f"  {'Total Tokens (Est.):':<25} {C_BOLD}{manifest.get('total_tokens', 0):,}{C_RESET}")
    print(f"  {'Avg Tokens/Chunk:':<25} {manifest.get('avg_tokens_per_chunk', 0)}")
    print()

    print(f"{C_BOLD}Chunks by Type:{C_RESET}")
    for ctype, count in manifest.get("chunks_by_type", {}).items():
        print(f"  - {ctype:<15} {count:>5}")
    print()

    print(f"{C_BOLD}{C_MAGENTA}Category Distribution Heatmap:{C_RESET}")
    print(f"  {'-' * 45}")
    print(f"  {'Category':<25} | {'Chunks':<6} | {'Percentage':<10}")
    print(f"  {'-' * 45}")
    
    total_chunks = manifest.get("total_chunks", 0)
    for cat, count in sorted(manifest.get("chunks_by_category", {}).items(), key=lambda x: -x[1]):
        pct = (count / total_chunks * 100) if total_chunks else 0
        bar = "█" * min(int(pct // 3) + 1, 20)
        print(f"  {cat:<25} | {count:>6} | {pct:>5.1f}%  {C_CYAN}{bar}{C_RESET}")
    
    print(f"  {'-' * 45}")
    print(f"  {'Total Chunks':<25} | {total_chunks:>6} | 100.0%\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pinecone Search Script with CLIP Encoding

This script:
- Takes a brand brief as input
- Encodes it with CLIP model (clip-ViT-B-32)
- Queries Pinecone with the CLIP vector
- Returns top_k results
"""

import sys
import os
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    from pinecone import Pinecone
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Error: Missing required package. {e}", file=sys.stderr)
    print("Please install: pip install python-dotenv pinecone sentence-transformers", file=sys.stderr)
    sys.exit(1)


def main():
    """Main function to search Pinecone with CLIP encoding"""
    # Log messages go to stderr (so they appear in terminal but don't interfere with JSON parsing)
    print("🔍 CLIP Encoding started", file=sys.stderr, flush=True)
    
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: python search_pinecone.py <brief_file> <api_key> <index_name>"}), file=sys.stderr)
        sys.exit(1)
    
    brief_file = sys.argv[1]
    api_key = sys.argv[2]
    index_name = sys.argv[3]
    
    # Read brief
    try:
        with open(brief_file, 'r') as f:
            brand_brief = f.read().strip()
        print(f"📝 Brief loaded: {len(brand_brief)} characters", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read brief file: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Load CLIP model
    print("🤖 Loading CLIP model (clip-ViT-B-32)...", file=sys.stderr, flush=True)
    try:
        model = SentenceTransformer('clip-ViT-B-32')
        print("✅ CLIP model loaded", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load CLIP model: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Encode brief with CLIP
    print("🔢 Encoding brief with CLIP...", file=sys.stderr, flush=True)
    try:
        # CLIP can encode text directly
        query_vector = model.encode(brand_brief, convert_to_numpy=True).tolist()
        print(f"✅ CLIP encoding complete: {len(query_vector)} dimensions", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to encode brief: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Connect to Pinecone
    print("🌲 Connecting to Pinecone...", file=sys.stderr, flush=True)
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        print(f"✅ Connected to Pinecone index: {index_name}", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to connect to Pinecone: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Query Pinecone
    print("🔍 Pinecone Querying...", file=sys.stderr, flush=True)
    try:
        top_k = 200  # Return top 200 results to ensure we get enough for all categories
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        
        print(f"✅ Query complete: {len(results.matches)} results found", file=sys.stderr, flush=True)
        
        # Format results
        formatted_results = {
            "results": [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata or {},
                }
                for match in results.matches
            ],
            "count": len(results.matches),
        }
        
        # Output JSON to stdout ONLY (this will be captured by Node.js)
        # All log messages go to stderr, so stdout is clean JSON
        print(json.dumps(formatted_results), flush=True)
        
    except Exception as e:
        print(json.dumps({"error": f"Failed to query Pinecone: {e}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Quick script to check Pinecone index statistics
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment
project_root = Path(__file__).parent.parent
env_path = project_root / '.env.local'
load_dotenv(env_path)

api_key = os.getenv('PINECONE_API_KEY')
index_name = os.getenv('PINECONE_INDEX_NAME', 'branding-playground')

if not api_key:
    print("❌ Error: PINECONE_API_KEY not found in .env.local")
    sys.exit(1)

# Connect to Pinecone
pc = Pinecone(api_key=api_key)
index = pc.Index(index_name)

# Get overall stats
stats = index.describe_index_stats()
print(f"\n📊 Pinecone Index: {index_name}")
print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
print(f"   Dimension: {stats.get('dimension', 'N/A')}")
print(f"   Index fullness: {stats.get('index_fullness', 'N/A')}")

# Query to get breakdown by category
print(f"\n🔍 Sampling vectors to get category breakdown...")
try:
    # Query with a dummy vector to get results
    dummy_vector = [0.0] * stats.get('dimension', 512)
    results = index.query(
        vector=dummy_vector,
        top_k=10000,  # Get as many as possible
        include_metadata=True
    )
    
    # Count by category metadata
    category_counts = {}
    for match in results.matches:
        category = match.metadata.get('category', 'unknown') if match.metadata else 'unknown'
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print(f"\n📋 Category Breakdown (from {len(results.matches)} sampled vectors):")
    for category, count in sorted(category_counts.items()):
        print(f"   {category:30s}: {count:4d} vectors")
    
    # Check specifically for photography/products
    products_count = category_counts.get('photography/products', 0)
    print(f"\n✅ Photography/Products: {products_count} vectors")
    
    if products_count >= 530:
        print(f"   ✅ SUCCESS: Products category has {products_count} vectors (target was ~530)")
    else:
        print(f"   ⚠️  Products category has {products_count} vectors (expected ~530)")
        
except Exception as e:
    print(f"⚠️  Warning: Could not query vectors for breakdown: {e}")

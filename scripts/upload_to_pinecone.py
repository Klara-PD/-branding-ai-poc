#!/usr/bin/env python3
"""
Upload images to Pinecone vector database with CLIP embeddings.

This script:
- Reads images from the data directory structure
- Generates CLIP embeddings using sentence-transformers
- Uses MD5 hashing for deduplication
- Uploads vectors to Pinecone with metadata
- Includes progress tracking with tqdm
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import json
import re
from collections import Counter

try:
    from dotenv import load_dotenv
    from pinecone import Pinecone, ServerlessSpec
    from sentence_transformers import SentenceTransformer
    from tqdm import tqdm
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("\nPlease install dependencies with:")
    print("pip install python-dotenv pinecone sentence-transformers tqdm pillow")
    sys.exit(1)


# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}


def load_environment() -> tuple[str, str]:
    """Load environment variables from .env.local"""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env.local'
    
    if not env_path.exists():
        raise FileNotFoundError(
            f".env.local file not found at {env_path}\n"
            "Please create .env.local with PINECONE_API_KEY and PINECONE_INDEX_NAME"
        )
    
    load_dotenv(env_path)
    
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'branding-playground')
    
    if not api_key:
        raise ValueError(
            "PINECONE_API_KEY not found in .env.local\n"
            "Please add PINECONE_API_KEY to your .env.local file"
        )
    
    return api_key, index_name


def get_image_md5(image_path: Path) -> str:
    """Calculate MD5 hash of an image file for deduplication"""
    hash_md5 = hashlib.md5()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_color_data(project_root: Path) -> Optional[Dict]:
    """
    Load color_palettes_tagged.json from flow_poc project.
    Returns dict keyed by SHA256 hash IDs.
    """
    # Try to find color data in flow_poc (sibling directory)
    flow_poc_root = project_root.parent / 'flow_poc'
    possible_files = [
        flow_poc_root / 'color_clip_project' / 'color_palettes_tagged.json',
        flow_poc_root / 'color_palettes_tagged.json',
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    colors_dict = {}
                    for entry in data:
                        entry_id = entry.get('id')
                        if entry_id:
                            colors_dict[entry_id] = entry
                    print(f"✓ Loaded {len(colors_dict)} color entries from {file_path.name}")
                    return colors_dict
                elif isinstance(data, dict):
                    print(f"✓ Loaded {len(data)} color entries from {file_path.name}")
                    return data
            except Exception as e:
                print(f"  Warning: Could not load color data from {file_path}: {e}")
                continue
    
    print("  Warning: color_palettes_tagged.json not found, color extraction will be used as fallback")
    return None


def extract_id_from_filename(filename: str) -> Optional[str]:
    """Try to extract a hash-like ID from filename."""
    stem = Path(filename).stem
    
    # Look for 64-char hex string (SHA256)
    sha256_pattern = r'[a-f0-9]{64}'
    match = re.search(sha256_pattern, stem, re.IGNORECASE)
    if match:
        return match.group(0)
    
    # Look for 32-char hex string (MD5)
    md5_pattern = r'[a-f0-9]{32}'
    match = re.search(md5_pattern, stem, re.IGNORECASE)
    if match:
        return match.group(0)
    
    return None


def match_image_to_colors_data(image_path: Path, colors_data: Dict, project_root: Path) -> Optional[Dict]:
    """
    Match an image to its entry in colors_data using multiple strategies.
    """
    if not colors_data:
        return None
    
    filename = image_path.name
    filename_no_ext = image_path.stem
    
    # Strategy 1: Match by SHA256 hash
    try:
        hash_sha256 = hashlib.sha256()
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        sha256_hash = hash_sha256.hexdigest()
        if sha256_hash in colors_data:
            return colors_data[sha256_hash]
    except Exception:
        pass
    
    # Strategy 2: Match by MD5 hash
    try:
        md5_hash = get_image_md5(image_path)
        if md5_hash in colors_data:
            return colors_data[md5_hash]
    except Exception:
        pass
    
    # Strategy 3: Extract ID from filename
    extracted_id = extract_id_from_filename(filename)
    if extracted_id and extracted_id in colors_data:
        return colors_data[extracted_id]
    
    # Strategy 4: Match by filename
    if filename in colors_data or filename_no_ext in colors_data:
        return colors_data.get(filename) or colors_data.get(filename_no_ext)
    
    # Strategy 5: Partial match
    for key in colors_data.keys():
        if filename_no_ext in key or key in filename_no_ext:
            return colors_data[key]
    
    return None


def extract_color_metadata(color_entry: Dict) -> Dict:
    """Extract hex codes and contrast rating from color entry."""
    metadata = {}
    
    # Extract hex codes
    hex_codes = []
    if 'colors' in color_entry:
        colors = color_entry['colors']
        if isinstance(colors, list):
            hex_codes = [c for c in colors if isinstance(c, str) and c.startswith('#')]
    
    metadata['hex_codes'] = hex_codes if hex_codes else []
    
    # Extract contrast rating
    contrast_rating = None
    if 'contrast_rating' in color_entry:
        contrast_rating = color_entry['contrast_rating']
    elif 'aaa_rating' in color_entry:
        contrast_rating = color_entry['aaa_rating']
    elif 'tags' in color_entry:
        tags = color_entry['tags']
        if isinstance(tags, dict):
            color_behavior = tags.get('color_behavior', [])
            for tag in color_behavior:
                if isinstance(tag, str) and 'AAA' in tag.upper():
                    contrast_rating = tag
                    break
    
    metadata['contrast_rating'] = contrast_rating
    return metadata


def extract_dominant_colors_from_image(image_path: Path, num_colors: int = 5) -> List[str]:
    """
    Extract dominant colors from an image using Pillow.
    Returns list of hex color codes.
    """
    try:
        img = Image.open(image_path)
        
        # Resize for faster processing
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get all pixels
        pixels = list(img.getdata())
        
        # Count color frequencies (quantize to reduce colors)
        color_counts = Counter()
        for r, g, b in pixels:
            # Quantize to reduce color space (16 levels per channel)
            r_q = (r // 16) * 16
            g_q = (g // 16) * 16
            b_q = (b // 16) * 16
            color_counts[(r_q, g_q, b_q)] += 1
        
        # Get most common colors
        most_common = color_counts.most_common(num_colors)
        
        # Convert to hex codes
        hex_codes = []
        for (r, g, b), count in most_common:
            hex_code = f"#{r:02x}{g:02x}{b:02x}"
            hex_codes.append(hex_code.upper())
        
        return hex_codes
    
    except Exception as e:
        print(f"    Warning: Failed to extract colors from {image_path.name}: {e}")
        return []


def get_image_files(data_root: Path) -> List[tuple[Path, str]]:
    """
    Recursively find all image files in the data directory.
    
    Returns:
        List of tuples: (image_path, category)
        Category format: 'brand_color_mood', 'photography/models', etc.
    """
    image_files: List[tuple[Path, str]] = []
    
    # Expected folder structure
    category_folders = {
        'brand_color_mood': ['brand_color_mood'],
        'typography': ['typography'],
        'logo_geometry': ['logo_geometry'],
        'photography/models': ['photography', 'models'],
        'photography/products': ['photography', 'products'],
        'photography/environments': ['photography', 'environments'],
        'illustration': ['illustration'],
    }
    
    for category, folder_parts in category_folders.items():
        category_path = data_root / Path(*folder_parts)
        
        if not category_path.exists():
            print(f"Warning: Category folder not found: {category_path}")
            continue
        
        # Find all image files in this category
        for ext in IMAGE_EXTENSIONS:
            for image_path in category_path.rglob(f'*{ext}'):
                if image_path.is_file():
                    image_files.append((image_path, category))
            for image_path in category_path.rglob(f'*{ext.upper()}'):
                if image_path.is_file():
                    image_files.append((image_path, category))
    
    return image_files


def initialize_pinecone(api_key: str, index_name: str, dimension: int = 512) -> Pinecone.Index:
    """Initialize Pinecone client and index"""
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if index_name not in existing_indexes:
        print(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print(f"Index {index_name} created successfully")
    else:
        print(f"Using existing index: {index_name}")
    
    # Connect to index
    index = pc.Index(index_name)
    
    # Wait for index to be ready
    import time
    time.sleep(1)
    
    return index


def main():
    """Main execution function"""
    print("=" * 60)
    print("Pinecone Image Upload Script")
    print("=" * 60)
    
    # Load environment
    try:
        api_key, index_name = load_environment()
        print(f"\n✓ Loaded environment variables")
        print(f"  Index: {index_name}")
    except (FileNotFoundError, ValueError) as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    
    # Get project root and data directory
    project_root = Path(__file__).parent.parent
    data_root = project_root / 'data'
    
    if not data_root.exists():
        print(f"\n✗ Error: Data directory not found at {data_root}")
        sys.exit(1)
    
    # Find all image files
    print(f"\n📁 Scanning for images in {data_root}...")
    image_files = get_image_files(data_root)
    
    # Filter to only brand_color_mood if specified
    if len(sys.argv) > 1 and sys.argv[1] == '--brand-color-mood-only':
        print("  Filtering to brand_color_mood category only")
        image_files = [(path, cat) for path, cat in image_files if cat == 'brand_color_mood']
        print(f"  Filtered to {len(image_files)} brand_color_mood images")
    
    if not image_files:
        print("\n✗ No image files found in data directory")
        print("\nPlease add images to the following folders:")
        print("  - data/brand_color_mood/")
        print("  - data/typography/")
        print("  - data/logo_geometry/")
        print("  - data/photography/models/")
        print("  - data/photography/products/")
        print("  - data/photography/environments/")
        print("  - data/illustration/")
        sys.exit(1)
    
    print(f"✓ Found {len(image_files)} image files")
    
    # Initialize CLIP model
    print("\n🤖 Loading CLIP model (clip-ViT-B-32)...")
    try:
        model = SentenceTransformer('clip-ViT-B-32')
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        sys.exit(1)
    
    # Initialize Pinecone
    print(f"\n🌲 Connecting to Pinecone...")
    try:
        index = initialize_pinecone(api_key, index_name, dimension=512)
        print("✓ Connected to Pinecone")
    except Exception as e:
        print(f"✗ Error connecting to Pinecone: {e}")
        sys.exit(1)
    
    # Load color data for brand_color_mood images
    colors_data = None
    if any(cat == 'brand_color_mood' for _, cat in image_files):
        print("\n🎨 Loading color data for brand_color_mood images...")
        colors_data = load_color_data(project_root)
    
    # Get existing vectors for deduplication
    print("\n🔍 Checking for existing vectors (deduplication)...")
    existing_ids = set()
    try:
        # Query index stats to get current vector count
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        print(f"  Current vectors in index: {total_vectors}")
        
        # Note: Full deduplication would require fetching all IDs,
        # which is expensive. We'll use MD5 hashes as IDs instead.
    except Exception as e:
        print(f"  Warning: Could not check existing vectors: {e}")
    
    # Process images and generate embeddings
    print("\n📤 Processing images and generating embeddings...")
    vectors_to_upsert: List[Dict] = []
    processed_hashes: Dict[str, str] = {}  # MD5 hash -> ID mapping
    skipped_count = 0
    error_count = 0
    
    for image_path, category in tqdm(image_files, desc="Processing", unit="image"):
        try:
            # Calculate MD5 hash for deduplication
            image_hash = get_image_md5(image_path)
            
            # Use hash as ID (Pinecone handles duplicates on upsert)
            vector_id = image_hash
            
            # Skip if we've already processed this hash
            if vector_id in processed_hashes:
                skipped_count += 1
                continue
            
            # Load and encode image
            try:
                image = Image.open(image_path)
                # CLIP can handle various image formats
                embedding = model.encode(image).tolist()
            except Exception as e:
                print(f"\n  Warning: Could not process {image_path}: {e}")
                error_count += 1
                continue
            
            # Prepare metadata
            # Use relative path from project root
            relative_path = image_path.relative_to(project_root)
            metadata = {
                'file_path': str(relative_path),
                'category': category,
                'filename': image_path.name,
                'md5_hash': image_hash,
            }
            
            # Add color metadata for brand_color_mood images
            if category == 'brand_color_mood':
                hex_codes = []
                contrast_rating = None
                
                # Strategy 1: Try to match with color data JSON
                if colors_data:
                    color_entry = match_image_to_colors_data(image_path, colors_data, project_root)
                    if color_entry:
                        color_metadata = extract_color_metadata(color_entry)
                        hex_codes = color_metadata.get('hex_codes', [])
                        contrast_rating = color_metadata.get('contrast_rating')
                        if hex_codes:
                            print(f"    ✓ Matched {image_path.name}: {len(hex_codes)} hex codes")
                
                # Strategy 2: Fallback - extract colors directly from image
                if not hex_codes:
                    hex_codes = extract_dominant_colors_from_image(image_path, num_colors=5)
                    if hex_codes:
                        print(f"    ✓ Extracted {len(hex_codes)} colors from {image_path.name}")
                
                # Add to metadata
                if hex_codes:
                    metadata['hex_codes'] = hex_codes
                if contrast_rating:
                    metadata['contrast_rating'] = contrast_rating
            
            # Prepare vector
            vector_data = {
                'id': vector_id,
                'values': embedding,
                'metadata': metadata
            }
            
            vectors_to_upsert.append(vector_data)
            processed_hashes[vector_id] = category
            
        except Exception as e:
            print(f"\n  Error processing {image_path}: {e}")
            error_count += 1
            continue
    
    print(f"\n✓ Processed {len(vectors_to_upsert)} images")
    if skipped_count > 0:
        print(f"  Skipped {skipped_count} duplicates")
    if error_count > 0:
        print(f"  Errors: {error_count}")
    
    if not vectors_to_upsert:
        print("\n✗ No vectors to upload")
        sys.exit(1)
    
    # Upload to Pinecone in batches
    print(f"\n🚀 Uploading {len(vectors_to_upsert)} vectors to Pinecone...")
    batch_size = 100  # Pinecone recommends batches of 100
    
    try:
        for i in tqdm(range(0, len(vectors_to_upsert), batch_size), desc="Uploading", unit="batch"):
            batch = vectors_to_upsert[i:i + batch_size]
            index.upsert(vectors=batch)
        
        print(f"\n✓ Successfully uploaded {len(vectors_to_upsert)} vectors to Pinecone!")
        
        # Get final stats
        final_stats = index.describe_index_stats()
        print(f"\n📊 Final index stats:")
        print(f"  Total vectors: {final_stats.total_vector_count}")
        
    except Exception as e:
        print(f"\n✗ Error uploading to Pinecone: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Upload complete! ✅")
    print("=" * 60)


if __name__ == '__main__':
    main()

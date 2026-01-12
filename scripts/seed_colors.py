#!/usr/bin/env python3
"""
Color Seeding Script - Hard Reset for Colors Category

Completely replaces all color vectors in Pinecone with new data from color_analysis.json.
Performs a hard reset by deleting all existing color vectors, then uploading new ones.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

try:
    from pinecone import Pinecone
    from sentence_transformers import SentenceTransformer
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("\nPlease install dependencies with:")
    print("pip install pinecone sentence-transformers pillow python-dotenv tqdm")
    sys.exit(1)


def load_environment() -> tuple[str, str]:
    """Load environment variables"""
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


def delete_all_color_vectors(index, category: str = 'brand_color_mood'):
    """Delete all vectors with category='brand_color_mood' from Pinecone"""
    print(f"\n🗑️  Deleting all existing vectors with category='{category}'...")
    
    deleted_count = 0
    try:
        # Query to find all vectors with this category
        # Use a dummy vector to query (we only care about metadata filtering)
        dummy_vector = [0.0] * 512  # CLIP dimension
        
        # Query with metadata filter to get all color vectors
        # Note: Pinecone v3 uses metadata filtering, not namespaces
        results = index.query(
            vector=dummy_vector,
            top_k=10000,  # Get as many as possible
            include_metadata=True,
            filter={"category": {"$eq": category}}
        )
        
        if results.matches:
            # Extract IDs to delete
            ids_to_delete = [match.id for match in results.matches]
            print(f"   Found {len(ids_to_delete)} vectors to delete")
            
            # Delete in batches of 1000 (Pinecone limit)
            batch_size = 1000
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i + batch_size]
                index.delete(ids=batch)
                deleted_count += len(batch)
                print(f"   Deleted batch {i//batch_size + 1}: {len(batch)} vectors")
        else:
            print(f"   No vectors found with category='{category}'")
            
    except Exception as e:
        print(f"   ⚠️  Error during deletion: {e}")
        print(f"   Continuing anyway - new vectors will be upserted")
    
    print(f"✅ Deleted {deleted_count} vectors")
    return deleted_count


def load_color_analysis(color_data_folder: Path) -> Dict:
    """Load all JSON files from color_data folder"""
    if not color_data_folder.exists():
        raise FileNotFoundError(
            f"Color data folder not found: {color_data_folder}\n"
            "Please ensure data/brand_color_mood/color_data exists"
        )
    
    print(f"\n📂 Loading color analysis data from {color_data_folder}...")
    
    color_data = {}
    json_files = list(color_data_folder.glob('*.json'))
    
    if not json_files:
        raise FileNotFoundError(
            f"No JSON files found in {color_data_folder}"
        )
    
    print(f"   Found {len(json_files)} JSON files")
    
    for json_file in tqdm(json_files, desc="Loading JSON files", unit="file"):
        try:
            with open(json_file, 'r') as f:
                entry = json.load(f)
            
            # Use filename from JSON as key, or derive from JSON filename
            filename = entry.get('filename')
            if not filename:
                # Derive from JSON filename (e.g., color_00228.json -> color_00228.png)
                filename = json_file.stem + '.png'
            
            color_data[filename] = entry
            
        except Exception as e:
            print(f"\n⚠️  Error loading {json_file.name}: {e}")
            continue
    
    print(f"✅ Loaded {len(color_data)} color entries")
    return color_data


def find_image_file(image_key: str, images_folder: Path) -> Optional[Path]:
    """Find image file matching the key from color_analysis.json"""
    # Try multiple strategies to find the image
    image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif']
    
    # Strategy 1: Direct filename match
    for ext in image_extensions:
        image_path = images_folder / image_key
        if image_path.exists():
            return image_path
        # Try with extension
        if not image_key.endswith(ext):
            image_path = images_folder / f"{image_key}{ext}"
            if image_path.exists():
                return image_path
    
    # Strategy 2: Match by filename without extension
    key_no_ext = Path(image_key).stem
    for ext in image_extensions:
        image_path = images_folder / f"{key_no_ext}{ext}"
        if image_path.exists():
            return image_path
    
    # Strategy 3: Search for partial match
    for image_file in images_folder.glob('*'):
        if image_file.is_file() and image_file.suffix.lower() in image_extensions:
            if key_no_ext in image_file.stem or image_file.stem in key_no_ext:
                return image_file
    
    return None


def get_text_for_search(entry: Dict) -> str:
    """Extract text field for search - use semantic_vibe, keywords, or color names"""
    if 'semantic_vibe' in entry and entry['semantic_vibe']:
        return entry['semantic_vibe']
    
    if 'keywords' in entry:
        if isinstance(entry['keywords'], list):
            return ', '.join(entry['keywords'])
        return str(entry['keywords'])
    
    # Fallback: use color names from extracted_colors
    if 'extracted_colors' in entry:
        color_names = [c.get('name', '') for c in entry['extracted_colors'] if c.get('name')]
        if color_names:
            return ', '.join(color_names)
    
    if 'description' in entry:
        return str(entry['description'])
    
    return ""


def main():
    print("=" * 70)
    print("Color Seeding - Hard Reset for Colors Category")
    print("=" * 70)
    
    try:
        # Load environment
        api_key, index_name = load_environment()
        project_root = Path(__file__).parent.parent
        
        print(f"\n✅ Pinecone API key found")
        print(f"📊 Index name: {index_name}")
        
        # Initialize Pinecone
        print(f"\n🌲 Connecting to Pinecone...")
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        print(f"✅ Connected to index: {index_name}")
        
        # Load color analysis data from color_data folder
        color_data_folder = project_root / 'data' / 'brand_color_mood' / 'color_data'
        color_data = load_color_analysis(color_data_folder)
        
        # Find images folder (check both locations)
        images_folder = project_root / 'public' / 'assets' / 'brand_color_mood'
        if not images_folder.exists():
            images_folder = project_root / 'data' / 'brand_color_mood'
            if not images_folder.exists():
                raise FileNotFoundError(
                    f"Images folder not found. Checked:\n"
                    f"  - {project_root / 'public' / 'assets' / 'brand_color_mood'}\n"
                    f"  - {project_root / 'data' / 'brand_color_mood'}"
                )
        
        print(f"📁 Using images folder: {images_folder}")
        
        # Step 1: Delete all existing color vectors
        deleted_count = delete_all_color_vectors(index, category='brand_color_mood')
        
        # Step 2: Load CLIP model
        print(f"\n🤖 Loading CLIP model (sentence-transformers/clip-ViT-B-32)...")
        model = SentenceTransformer('clip-ViT-B-32')
        print(f"✅ CLIP model loaded")
        
        # Step 3: Process each entry
        print(f"\n📤 Processing {len(color_data)} color entries...")
        
        vectors_to_upsert = []
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for entry_key, entry_data in tqdm(color_data.items(), desc="Processing", unit="entry"):
            try:
                # Find image file
                image_path = find_image_file(entry_key, images_folder)
                if not image_path:
                    print(f"\n⚠️  Image not found for key: {entry_key}")
                    skipped_count += 1
                    continue
                
                # Load and encode image
                try:
                    image = Image.open(image_path).convert('RGB')
                    embedding = model.encode(image, convert_to_numpy=True).tolist()
                except Exception as e:
                    print(f"\n⚠️  Error encoding {image_path.name}: {e}")
                    error_count += 1
                    continue
                
                # Prepare metadata
                # Store entire JSON entry as stringified colors_data
                colors_data_str = json.dumps(entry_data)
                
                # Get text for search
                text_field = get_text_for_search(entry_data)
                
                # Use filename as ID (or generate from path)
                vector_id = image_path.stem
                
                # Prepare metadata
                metadata = {
                    'file_path': str(image_path.relative_to(project_root)),
                    'category': 'brand_color_mood',
                    'filename': image_path.name,
                    'colors_data': colors_data_str,  # Entire JSON object as string
                    'text': text_field,  # Semantic vibe or keywords for search
                }
                
                # Add any other fields from entry_data to metadata
                for key, value in entry_data.items():
                    if key not in ['colors_data', 'text']:  # Don't duplicate
                        # Only add simple types that Pinecone supports
                        if isinstance(value, (str, int, float, bool)):
                            metadata[key] = value
                        elif isinstance(value, list) and all(isinstance(x, (str, int, float)) for x in value):
                            metadata[key] = value
                
                # Prepare vector
                vector_data = {
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                }
                
                vectors_to_upsert.append(vector_data)
                processed_count += 1
                
            except Exception as e:
                print(f"\n⚠️  Error processing entry {entry_key}: {e}")
                error_count += 1
                continue
        
        # Step 4: Upload to Pinecone
        if vectors_to_upsert:
            print(f"\n🚀 Uploading {len(vectors_to_upsert)} vectors to Pinecone...")
            
            # Upload in batches of 100
            batch_size = 100
            for i in tqdm(range(0, len(vectors_to_upsert), batch_size), desc="Uploading", unit="batch"):
                batch = vectors_to_upsert[i:i + batch_size]
                try:
                    index.upsert(vectors=batch)
                except Exception as e:
                    print(f"\n⚠️  Error uploading batch {i//batch_size + 1}: {e}")
            
            print(f"✅ Upload complete!")
        else:
            print(f"\n⚠️  No vectors to upload")
        
        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"🗑️  Deleted old vectors: {deleted_count}")
        print(f"✅ Processed: {processed_count} entries")
        print(f"⏭️  Skipped (image not found): {skipped_count} entries")
        print(f"❌ Errors: {error_count} entries")
        print(f"📤 Uploaded: {len(vectors_to_upsert)} vectors")
        print(f"\n✅ Color seeding complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

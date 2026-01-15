#!/usr/bin/env python3
"""
Update metadata JSON files to match renamed image files.
Matches images by content (hash) to preserve metadata when filenames change.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional

def get_image_hash(image_path: Path) -> str:
    """Calculate SHA256 hash of image file"""
    sha256_hash = hashlib.sha256()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def update_logo_metadata(project_root: Path):
    """Update logo_metadata.json with new filenames"""
    logo_folder = project_root / 'data' / 'logo_geometry'
    metadata_file = project_root / 'data' / 'logo_metadata.json'
    
    if not metadata_file.exists():
        print("⚠️  logo_metadata.json not found")
        return
    
    # Load existing metadata
    with open(metadata_file, 'r') as f:
        old_metadata = json.load(f)
    
    print(f"📂 Found {len(old_metadata)} entries in logo_metadata.json")
    
    # Get all image files in folder
    image_files = list(logo_folder.glob('*.png')) + list(logo_folder.glob('*.jpg'))
    print(f"📁 Found {len(image_files)} image files in folder")
    
    # Create hash map of old entries by reading their file_path
    old_hash_map = {}
    print("🔍 Calculating hashes for old entries...")
    for old_filename, old_entry in old_metadata.items():
        if 'file_path' in old_entry:
            old_path = project_root / old_entry['file_path']
            if old_path.exists():
                try:
                    old_hash = get_image_hash(old_path)
                    old_hash_map[old_hash] = old_entry
                except Exception as e:
                    print(f"⚠️  Error hashing {old_path}: {e}")
    
    print(f"   Calculated hashes for {len(old_hash_map)} old entries")
    
    # Now match new files
    new_metadata = {}
    matched_count = 0
    
    print("🔍 Matching new filenames to old entries...")
    for image_path in image_files:
        new_filename = image_path.name
        image_hash = get_image_hash(image_path)
        
        if image_hash in old_hash_map:
            # Found match! Update entry
            old_entry = old_hash_map[image_hash].copy()
            old_entry['filename'] = new_filename
            old_entry['file_path'] = str(image_path.relative_to(project_root))
            new_metadata[new_filename] = old_entry
            matched_count += 1
        else:
            # No match found - this is a new file or renamed differently
            print(f"⚠️  No match found for {new_filename}")
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(new_metadata, f, indent=2)
    
    print(f"✅ Updated {matched_count} entries in logo_metadata.json")
    print(f"📊 Total entries: {len(new_metadata)}")

def update_illustration_metadata(project_root: Path):
    """Update illustration_metadata.json with new filenames"""
    illustration_folder = project_root / 'data' / 'illustration'
    metadata_file = project_root / 'data' / 'illustration_metadata.json'
    
    if not metadata_file.exists():
        print("⚠️  illustration_metadata.json not found")
        return
    
    # Load existing metadata
    with open(metadata_file, 'r') as f:
        old_metadata = json.load(f)
    
    print(f"📂 Found {len(old_metadata)} entries in illustration_metadata.json")
    
    # Get all image files in folder
    image_files = list(illustration_folder.glob('*.png')) + list(illustration_folder.glob('*.jpg'))
    print(f"📁 Found {len(image_files)} image files in folder")
    
    # Create hash map of old entries by reading their file_path
    old_hash_map = {}
    print("🔍 Calculating hashes for old entries...")
    for old_filename, old_entry in old_metadata.items():
        if 'file_path' in old_entry:
            old_path = project_root / old_entry['file_path']
            if old_path.exists():
                try:
                    old_hash = get_image_hash(old_path)
                    old_hash_map[old_hash] = old_entry
                except Exception as e:
                    print(f"⚠️  Error hashing {old_path}: {e}")
    
    print(f"   Calculated hashes for {len(old_hash_map)} old entries")
    
    # Now match new files
    new_metadata = {}
    matched_count = 0
    
    print("🔍 Matching new filenames to old entries...")
    for image_path in image_files:
        new_filename = image_path.name
        image_hash = get_image_hash(image_path)
        
        if image_hash in old_hash_map:
            # Found match! Update entry
            old_entry = old_hash_map[image_hash].copy()
            old_entry['filename'] = new_filename
            old_entry['file_path'] = str(image_path.relative_to(project_root))
            new_metadata[new_filename] = old_entry
            matched_count += 1
        else:
            # No match found - this is a new file or renamed differently
            print(f"⚠️  No match found for {new_filename}")
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(new_metadata, f, indent=2)
    
    print(f"✅ Updated {matched_count} entries in illustration_metadata.json")
    print(f"📊 Total entries: {len(new_metadata)}")

def main():
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("Updating Metadata JSON Files with New Filenames")
    print("=" * 70)
    
    print("\n🔄 Updating logo_metadata.json...")
    update_logo_metadata(project_root)
    
    print("\n🔄 Updating illustration_metadata.json...")
    update_illustration_metadata(project_root)
    
    print("\n✅ Update complete!")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Rename image files to their content hash (SHA256).
This ensures metadata is tied to image content, not filenames.
"""

import hashlib
from pathlib import Path
from typing import List
import json

def get_image_hash(image_path: Path) -> str:
    """Calculate SHA256 hash of image file"""
    sha256_hash = hashlib.sha256()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def rename_files_to_hash(folder_path: Path, category: str):
    """Rename all image files in folder to their content hash"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}
    
    # Get all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(folder_path.glob(f'*{ext}'))
        image_files.extend(folder_path.glob(f'*{ext.upper()}'))
    
    print(f"\n📁 Found {len(image_files)} images in {folder_path.name}")
    
    renamed_count = 0
    skipped_count = 0
    rename_map = {}
    
    for image_path in sorted(image_files):
        # Calculate hash
        image_hash = get_image_hash(image_path)
        new_name = f"{image_hash}.png"
        new_path = image_path.parent / new_name
        
        # Skip if already hashed
        if image_path.name == new_name:
            skipped_count += 1
            continue
        
        # Store mapping
        rename_map[str(image_path.name)] = new_name
        
        # Rename file
        try:
            image_path.rename(new_path)
            renamed_count += 1
            if renamed_count % 50 == 0:
                print(f"   Renamed {renamed_count} files...")
        except Exception as e:
            print(f"⚠️  Error renaming {image_path.name}: {e}")
    
    # Save rename mapping
    if rename_map:
        mapping_file = folder_path.parent / f"{category}_rename_map.json"
        with open(mapping_file, 'w') as f:
            json.dump(rename_map, f, indent=2)
        print(f"💾 Saved rename mapping to {mapping_file.name}")
    
    print(f"✅ Renamed {renamed_count} files, skipped {skipped_count} (already hashed)")
    return renamed_count

def main():
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("Rename Images to Content Hash")
    print("=" * 70)
    
    folders_to_process = [
        ("data/logo_geometry", "logo"),
        ("data/illustration", "illustration"),
    ]
    
    total_renamed = 0
    for folder_path_str, category in folders_to_process:
        folder_path = project_root / folder_path_str
        if not folder_path.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            continue
        
        renamed = rename_files_to_hash(folder_path, category)
        total_renamed += renamed
    
    print(f"\n{'=' * 70}")
    print(f"✅ Complete! Renamed {total_renamed} files total")
    print(f"{'=' * 70}")
    print("\n📝 Next steps:")
    print("   1. Run: python3 scripts/enrich_graphics.py --yes")
    print("   2. Metadata will now be tied to image content, not filenames")

if __name__ == '__main__':
    main()

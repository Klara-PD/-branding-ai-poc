#!/usr/bin/env python3
"""
Rename image files to organized numbered format:
- Logos: Logo_00001.png, Logo_00002.png, ...
- Illustrations: Illustration_00001.png, Illustration_00002.png, ...
- Photography Products: Product_00001.png, Product_00002.png, ...
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List

def rename_folder_to_numbers(folder_path: Path, prefix: str, metadata_file: Path = None):
    """Rename all image files in folder to numbered format"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}
    
    # Get all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(folder_path.glob(f'*{ext}'))
        image_files.extend(folder_path.glob(f'*{ext.upper()}'))
    
    image_files = sorted(image_files)  # Sort for consistent numbering
    total_files = len(image_files)
    
    if total_files == 0:
        print(f"⚠️  No images found in {folder_path.name}")
        return None
    
    print(f"\n📁 Found {total_files} images in {folder_path.name}")
    
    # Load existing metadata if it exists
    old_metadata = {}
    if metadata_file and metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                old_metadata = json.load(f)
            print(f"📂 Loaded {len(old_metadata)} entries from {metadata_file.name}")
        except Exception as e:
            print(f"⚠️  Could not load metadata: {e}")
    
    # Create rename mapping and new metadata
    rename_map = {}
    new_metadata = {}
    renamed_count = 0
    
    # Calculate padding (e.g., if 1000 files, use 4 digits: 0001)
    padding = len(str(total_files))
    
    for idx, image_path in enumerate(image_files, start=1):
        old_name = image_path.name
        new_name = f"{prefix}_{str(idx).zfill(padding)}.png"
        new_path = image_path.parent / new_name
        
        # Store mapping
        rename_map[old_name] = new_name
        
        # Update metadata if it exists
        if old_name in old_metadata:
            old_entry = old_metadata[old_name].copy()
            old_entry['filename'] = new_name
            old_entry['file_path'] = str(new_path.relative_to(metadata_file.parent.parent))
            new_metadata[new_name] = old_entry
        
        # Rename file
        try:
            image_path.rename(new_path)
            renamed_count += 1
            if renamed_count % 100 == 0:
                print(f"   Renamed {renamed_count}/{total_files} files...")
        except Exception as e:
            print(f"⚠️  Error renaming {old_name}: {e}")
    
    # Save rename mapping
    mapping_file = folder_path.parent / f"{prefix.lower()}_rename_map.json"
    with open(mapping_file, 'w') as f:
        json.dump(rename_map, f, indent=2)
    print(f"💾 Saved rename mapping to {mapping_file.name}")
    
    # Update metadata file if it exists
    if metadata_file:
        if new_metadata:
            with open(metadata_file, 'w') as f:
                json.dump(new_metadata, f, indent=2)
            print(f"✅ Updated {metadata_file.name} with {len(new_metadata)} entries")
        else:
            # Create empty metadata structure
            with open(metadata_file, 'w') as f:
                json.dump({}, f, indent=2)
            print(f"📝 Created empty {metadata_file.name}")
    
    print(f"✅ Renamed {renamed_count}/{total_files} files")
    return rename_map

def main():
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("Rename Images to Numbered Format")
    print("=" * 70)
    
    folders_to_process = [
        ("data/logo_geometry", "Logo", "data/logo_metadata.json"),
        ("data/illustration", "Illustration", "data/illustration_metadata.json"),
        ("data/photography/products", "Product", None),  # No metadata file for products yet
    ]
    
    total_renamed = 0
    for folder_path_str, prefix, metadata_file_str in folders_to_process:
        folder_path = project_root / folder_path_str
        if not folder_path.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            continue
        
        metadata_file = project_root / metadata_file_str if metadata_file_str else None
        rename_map = rename_folder_to_numbers(folder_path, prefix, metadata_file)
        
        if rename_map:
            total_renamed += len(rename_map)
    
    print(f"\n{'=' * 70}")
    print(f"✅ Complete! Renamed {total_renamed} files total")
    print(f"{'=' * 70}")
    print("\n📝 Files are now organized with numbered names:")
    print("   - Logos: Logo_00001.png, Logo_00002.png, ...")
    print("   - Illustrations: Illustration_00001.png, Illustration_00002.png, ...")
    print("   - Products: Product_00001.png, Product_00002.png, ...")

if __name__ == '__main__':
    main()

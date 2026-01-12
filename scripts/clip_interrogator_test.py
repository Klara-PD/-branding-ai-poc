#!/usr/bin/env python3
"""
CLIP Interrogator Test using BLIP Image Captioning

Tests how well AI models interpret product images by generating captions.
Uses Salesforce/blip-image-captioning-base model via transformers.
"""

import os
import sys
import random
from pathlib import Path

try:
    from PIL import Image
    from transformers import BlipProcessor, BlipForConditionalGeneration
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("\nPlease install dependencies with:")
    print("pip install transformers pillow torch")
    sys.exit(1)


def get_random_images(folder_path: Path, count: int = 3):
    """Get random image files from a folder"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(folder_path.glob(f'*{ext}'))
        image_files.extend(folder_path.glob(f'*{ext.upper()}'))
    
    if len(image_files) < count:
        print(f"⚠️  Warning: Only found {len(image_files)} images, returning all")
        return image_files
    
    return random.sample(image_files, count)


def generate_caption(image_path: Path, processor, model):
    """Generate a caption for an image using BLIP"""
    try:
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        # Process image and generate caption
        inputs = processor(image, return_tensors="pt")
        
        # Generate caption (unconditional)
        out = model.generate(**inputs, max_length=50, num_beams=3)
        caption = processor.decode(out[0], skip_special_tokens=True)
        
        return caption
    except Exception as e:
        return f"Error: {e}"


def main():
    print("=" * 60)
    print("CLIP Interrogator Test - BLIP Image Captioning")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    products_folder = project_root / 'data' / 'photography' / 'products'
    
    if not products_folder.exists():
        print(f"❌ Error: Products folder not found at {products_folder}")
        sys.exit(1)
    
    # Get random images
    print(f"\n📁 Scanning {products_folder}...")
    random_images = get_random_images(products_folder, count=3)
    
    if not random_images:
        print(f"❌ No images found in {products_folder}")
        sys.exit(1)
    
    print(f"✅ Selected {len(random_images)} random images:")
    for img in random_images:
        print(f"   - {img.name}")
    
    # Load BLIP model
    print(f"\n🤖 Loading BLIP model (Salesforce/blip-image-captioning-base)...")
    print("   (This may take a minute on first run - downloading model weights)")
    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nMake sure you have internet connection for first-time model download")
        sys.exit(1)
    
    # Generate captions
    print(f"\n🔍 Generating captions...")
    print("=" * 60)
    
    results = []
    for i, image_path in enumerate(random_images, 1):
        print(f"\n[{i}/{len(random_images)}] Processing: {image_path.name}")
        caption = generate_caption(image_path, processor, model)
        results.append((image_path.name, caption))
        print(f"   Caption: {caption}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\n📊 Results:")
    for filename, caption in results:
        print(f"\n📸 Image: {filename}")
        print(f"   What AI sees: {caption}")
    
    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    luxury_keywords = ['luxury', 'premium', 'elegant', 'sophisticated', 'high-end', 'upscale', 'refined']
    generic_keywords = ['bottle', 'container', 'object', 'item', 'product', 'thing']
    skincare_keywords = ['skincare', 'beauty', 'cosmetic', 'cream', 'serum', 'lotion', 'moisturizer']
    
    for filename, caption in results:
        caption_lower = caption.lower()
        has_luxury = any(kw in caption_lower for kw in luxury_keywords)
        has_skincare = any(kw in caption_lower for kw in skincare_keywords)
        is_generic = any(kw in caption_lower for kw in generic_keywords) and not has_skincare
        
        print(f"\n📸 {filename}:")
        if has_skincare:
            print("   ✅ Context-aware: Mentions skincare/beauty context")
        elif has_luxury:
            print("   ⚠️  Partially aware: Mentions luxury but not product type")
        elif is_generic:
            print("   ❌ Generic: Just describes objects without context")
        else:
            print("   ❓ Unclear: Caption doesn't match expected patterns")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Asset Enrichment Script - Brand-Aware Metadata Generation

Uses OpenAI's gpt-4o-mini Vision to generate rich, brand-aware metadata
for product images. This metadata will be embedded into Pinecone alongside
images to improve search relevance.
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

try:
    from openai import OpenAI
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("\nPlease install dependencies with:")
    print("pip install openai pillow python-dotenv tqdm")
    sys.exit(1)


# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}

# System prompt for art director analysis - High-end design critic perspective
SYSTEM_PROMPT = """You are a Senior Design Critic and Art Director for a high-end visual culture magazine (like Kinfolk, Wallpaper*, or Cereal).
Your task is to analyze this image not just for *content*, but for *essence* and *atmosphere*.

Analyze the following dimensions deeply:
1. **Atmosphere & Energy:** Is it ethereal, grounded, kinetic, static, moody, clinical, or whimsical? describe the emotional temperature.
2. **Lighting & Shadow:** Use terms like 'chiaroscuro', 'diffused softbox', 'harsh sunlight', 'volumetric', 'rim lighting', or 'flat lay'.
3. **Composition & Line:** Discuss negative space, leading lines, geometric tension, symmetry vs. asymmetry, and focal points.
4. **Materiality & Texture:** Describe the tactile quality—matte, glossy, granular, velvet, raw concrete, polished steel.
5. **Design Language:** Reference specific styles if applicable (e.g., Brutalist, Mid-Century, Memphis, Minimalist, Bauhaus, Organic Modern).

**Output format:** A single, rich, evocative paragraph (3-4 sentences). Do NOT start with "The image shows". Dive straight into the visual narrative."""

USER_PROMPT = "Analyze this product image with the depth and sophistication of a design critic. Provide a rich, evocative description that captures the essence and atmosphere."


def load_environment() -> tuple[str, str, str]:
    """Load environment variables and check for API key (OpenRouter or OpenAI)"""
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env.local'
    
    if not env_path.exists():
        raise FileNotFoundError(
            f".env.local file not found at {env_path}\n"
            "Please create .env.local with OPENAI_API_KEY or OPENROUTER_API_KEY"
        )
    
    load_dotenv(env_path)
    
    # Check for OpenRouter first (preferred), then OpenAI
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    use_openrouter = bool(os.getenv('OPENROUTER_API_KEY'))
    
    if not api_key:
        raise ValueError(
            "API key not found in .env.local\n"
            "Please add OPENROUTER_API_KEY or OPENAI_API_KEY to your .env.local file"
        )
    
    return api_key, project_root, 'openrouter' if use_openrouter else 'openai'


def encode_image_to_base64(image_path: Path) -> str:
    """Encode image to base64 for OpenAI API"""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_mime_type(image_path: Path) -> str:
    """Get MIME type based on file extension"""
    ext = image_path.suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
    }
    return mime_types.get(ext, 'image/jpeg')


def get_product_images(products_folder: Path) -> List[Path]:
    """Get all image files from products folder"""
    image_files = []
    
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(products_folder.glob(f'*{ext}'))
        image_files.extend(products_folder.glob(f'*{ext.upper()}'))
    
    return sorted(image_files)


def analyze_image(client: OpenAI, image_path: Path, provider: str = 'openai', max_retries: int = 3) -> Optional[str]:
    """Analyze a single image using Vision API (OpenRouter or OpenAI)"""
    try:
        # Encode image
        base64_image = encode_image_to_base64(image_path)
        mime_type = get_image_mime_type(image_path)
        
        # Determine model name based on provider
        if provider == 'openrouter':
            # OpenRouter uses openai/gpt-4o-mini for vision models
            model_name = "openai/gpt-4o-mini"
        else:
            model_name = "gpt-4o-mini"
        
        # Call Vision API
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": USER_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=400,  # Increased for richer descriptions
            temperature=0.8,  # Slightly higher for more creative/evocative language
        )
        
        description = response.choices[0].message.content.strip()
        return description
        
    except Exception as e:
        print(f"\n⚠️  Error analyzing {image_path.name}: {e}")
        return None


def estimate_cost(num_images: int) -> Dict[str, float]:
    """Estimate API costs for processing images"""
    # GPT-4o-mini Vision pricing (as of 2024):
    # Input: $0.15 per 1M tokens (images count as tokens)
    # Output: $0.60 per 1M tokens
    # Rough estimate: ~1000 tokens per image (input) + ~100 tokens (output)
    
    # Conservative estimate: $0.001 per image
    cost_per_image = 0.001
    total_cost = num_images * cost_per_image
    
    return {
        "cost_per_image": cost_per_image,
        "estimated_total": total_cost,
        "num_images": num_images
    }


def main():
    print("=" * 70)
    print("Asset Enrichment - Brand-Aware Metadata Generation")
    print("=" * 70)
    
    try:
        # Load environment
        api_key, project_root, provider = load_environment()
        provider_name = "OpenRouter" if provider == 'openrouter' else "OpenAI"
        print(f"\n✅ {provider_name} API key found")
        
        # Initialize OpenAI client (works with both OpenAI and OpenRouter)
        if provider == 'openrouter':
            # OpenRouter uses OpenAI-compatible API
            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            client = OpenAI(api_key=api_key)
        
        # Get products folder
        products_folder = project_root / 'data' / 'photography' / 'products'
        if not products_folder.exists():
            print(f"❌ Error: Products folder not found at {products_folder}")
            sys.exit(1)
        
        # Get all product images
        print(f"\n📁 Scanning {products_folder}...")
        image_files = get_product_images(products_folder)
        
        if not image_files:
            print(f"❌ No images found in {products_folder}")
            sys.exit(1)
        
        print(f"✅ Found {len(image_files)} product images")
        
        # Estimate costs
        cost_estimate = estimate_cost(len(image_files))
        print(f"\n💰 Cost Estimate:")
        print(f"   Images to process: {cost_estimate['num_images']}")
        print(f"   Estimated cost: ${cost_estimate['estimated_total']:.2f}")
        print(f"   (Approximate - actual cost may vary)")
        
        # Confirm before proceeding
        print(f"\n⚠️  This will process {len(image_files)} images using OpenAI API.")
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)
        
        # Output file
        output_file = project_root / 'product_metadata.json'
        
        # Load existing metadata if file exists
        existing_metadata = {}
        if output_file.exists():
            try:
                with open(output_file, 'r') as f:
                    existing_metadata = json.load(f)
                print(f"\n📂 Found existing metadata file with {len(existing_metadata)} entries")
                print(f"   Will skip already processed images")
            except Exception as e:
                print(f"⚠️  Warning: Could not load existing metadata: {e}")
                existing_metadata = {}
        
        # Process images
        print(f"\n🔍 Processing images with GPT-4o-mini Vision...")
        print("=" * 70)
        
        metadata = existing_metadata.copy()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        # Filter out already processed images
        images_to_process = [
            img for img in image_files 
            if img.name not in existing_metadata
        ]
        
        if not images_to_process:
            print("✅ All images already processed!")
            return
        
        print(f"📊 Processing {len(images_to_process)} new images...")
        
        # Process with progress bar
        for image_path in tqdm(images_to_process, desc="Analyzing", unit="image"):
            description = analyze_image(client, image_path, provider=provider)
            
            if description:
                metadata[image_path.name] = {
                    "filename": image_path.name,
                    "description": description,
                    "file_path": str(image_path.relative_to(project_root))
                }
                processed_count += 1
                
                # Save incrementally every 10 images
                if processed_count % 10 == 0:
                    with open(output_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
            else:
                error_count += 1
            
            # Skip already processed
            if image_path.name in existing_metadata:
                skipped_count += 1
        
        # Final save
        print(f"\n💾 Saving metadata to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✅ Processed: {processed_count} images")
        print(f"⏭️  Skipped (already processed): {skipped_count} images")
        print(f"❌ Errors: {error_count} images")
        print(f"📊 Total metadata entries: {len(metadata)}")
        print(f"💾 Saved to: {output_file}")
        
        # Show sample
        if metadata:
            print(f"\n📝 Sample description:")
            sample_key = list(metadata.keys())[0]
            sample = metadata[sample_key]
            print(f"   Image: {sample['filename']}")
            print(f"   Description: {sample['description'][:200]}...")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("💾 Saving progress...")
        if 'metadata' in locals() and metadata:
            with open(output_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"✅ Progress saved to {output_file}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

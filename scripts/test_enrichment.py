#!/usr/bin/env python3
"""
Quick test script to show the new enrichment output quality
Tests on first 3 images only
"""

import os
import sys
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

try:
    from openai import OpenAI
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("\nPlease install dependencies with:")
    print("pip install openai python-dotenv tqdm")
    sys.exit(1)


# System prompt - same as enrich_assets.py
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

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}


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


def get_product_images(products_folder: Path, limit: int = 3) -> list:
    """Get first N image files from products folder"""
    image_files = []
    
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(products_folder.glob(f'*{ext}'))
        image_files.extend(products_folder.glob(f'*{ext.upper()}'))
    
    return sorted(image_files)[:limit]


def analyze_image(client: OpenAI, image_path: Path, provider: str = 'openrouter') -> str:
    """Analyze a single image using Vision API"""
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    mime_type = get_image_mime_type(image_path)
    
    # Determine model name based on provider
    if provider == 'openrouter':
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
        max_tokens=400,
        temperature=0.8,
    )
    
    return response.choices[0].message.content.strip()


def main():
    print("=" * 70)
    print("Enrichment Test - New System Prompt Quality Check")
    print("=" * 70)
    
    # Load environment
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env.local'
    load_dotenv(env_path)
    
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    use_openrouter = bool(os.getenv('OPENROUTER_API_KEY'))
    provider = 'openrouter' if use_openrouter else 'openai'
    provider_name = "OpenRouter" if use_openrouter else "OpenAI"
    
    if not api_key:
        print("❌ Error: No API key found")
        sys.exit(1)
    
    print(f"\n✅ Using {provider_name} API")
    
    # Initialize client
    if provider == 'openrouter':
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        client = OpenAI(api_key=api_key)
    
    # Get products folder
    products_folder = project_root / 'data' / 'photography' / 'products'
    if not products_folder.exists():
        print(f"❌ Error: Products folder not found")
        sys.exit(1)
    
    # Get first 3 images
    print(f"\n📁 Getting first 3 images from {products_folder}...")
    image_files = get_product_images(products_folder, limit=3)
    
    if not image_files:
        print("❌ No images found")
        sys.exit(1)
    
    print(f"✅ Found {len(image_files)} images to test\n")
    
    # Process images
    results = []
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Processing: {image_path.name}")
        try:
            description = analyze_image(client, image_path, provider=provider)
            results.append({
                "filename": image_path.name,
                "description": description
            })
            print(f"✅ Generated description ({len(description)} chars)\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
            results.append({
                "filename": image_path.name,
                "description": f"Error: {e}"
            })
    
    # Display results
    print("=" * 70)
    print("RESULTS - New System Prompt Output")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*70}")
        print(f"Image {i}: {result['filename']}")
        print(f"{'='*70}")
        print(f"\n{result['description']}\n")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Photography Enrichment Script - Category-Specific Metadata Generation

Uses OpenAI's gpt-4o-mini Vision to generate rich, category-specific metadata
for photography images. Each category (products, models, environments) uses
a specialized system prompt tailored to that domain.
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
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("\nPlease install dependencies with:")
    print("pip install openai python-dotenv tqdm")
    sys.exit(1)


# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}

# Category-specific system prompts
CATEGORY_PROMPTS = {
    # PHOTO: PRODUCTS -> Save to data/product_metadata.json
    "products": """You are a Product Photographer. Analyze the shot composition.
    Describe:
    - The lighting (Softbox, Hard sunlight, Cinematic, Moody).
    - The materiality (Matte, Glossy, Translucent, Velvet).
    - The vibe (Luxury, Organic, Industrial, Clinical).
    CONSTRAINT: Focus on LIGHTING and MATERIAL. Do not describe the product function (e.g. don't say 'it is a shampoo bottle', describe the form).""",

    # PHOTO: MODELS -> Save to data/model_metadata.json
    "models": """You are a Casting Director. Analyze the PEOPLE in the shot.
    Describe:
    - Demographics (Estimated age range, ethnicity, gender identity).
    - The Energy (High energy, Calm, Melancholic, Joyful).
    - The Pose (Candid movement, Static studio pose, Running, Dancing).
    - The Gaze (Direct eye contact, Looking away, Closed eyes).
    - Group dynamic (Solitary, Couple, Crowd).
    CONSTRAINT: Do NOT describe the clothing styling or the background. Focus strictly on the HUMAN element and body language.""",

    # PHOTO: ENVIRONMENTS -> Save to data/environment_metadata.json
    "environments": """You are an Architectural Photographer. Analyze the space.
    Describe:
    - The location type (Urban street, Interior living room, Abstract studio, Nature).
    - The architectural style (Modern, Rustic, Brutalist, Minimalist).
    - The camera technique (Wide angle, Macro, Motion blur, Film grain).
    - The lighting atmosphere (Golden hour, Neon night, Overexposed).
    CONSTRAINT: Focus on the SPACE, ARCHITECTURE and CAMERA WORK.""",
}

USER_PROMPT = "Analyze this image according to your expertise and provide a detailed description."

# Output file mapping
OUTPUT_FILES = {
    "products": "data/product_metadata.json",
    "models": "data/model_metadata.json",
    "environments": "data/environment_metadata.json",
}


def load_environment() -> tuple[str, str, str]:
    """Load environment variables and check for API key (OpenRouter or OpenAI)"""
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env.local'
    
    if not env_path.exists():
        raise FileNotFoundError(
            f".env.local file not found at {env_path}\n"
            "Please create .env.local with OPENROUTER_API_KEY or OPENAI_API_KEY"
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


def get_images_from_folder(folder_path: Path) -> List[Path]:
    """Get all image files from a folder"""
    image_files = []
    
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(folder_path.glob(f'*{ext}'))
        image_files.extend(folder_path.glob(f'*{ext.upper()}'))
    
    return sorted(image_files)


def analyze_image(client: OpenAI, image_path: Path, category: str, provider: str = 'openrouter') -> Optional[str]:
    """Analyze a single image using Vision API with category-specific prompt"""
    try:
        # Encode image
        base64_image = encode_image_to_base64(image_path)
        mime_type = get_image_mime_type(image_path)
        
        # Get category-specific system prompt
        system_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["products"])
        
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
                    "content": system_prompt
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
        
        description = response.choices[0].message.content.strip()
        return description
        
    except Exception as e:
        print(f"\n⚠️  Error analyzing {image_path.name}: {e}")
        return None


def estimate_cost(num_images: int) -> Dict[str, float]:
    """Estimate API costs for processing images"""
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
    print("Photography Enrichment - Category-Specific Metadata Generation")
    print("=" * 70)
    
    try:
        # Load environment
        api_key, project_root, provider = load_environment()
        provider_name = "OpenRouter" if provider == 'openrouter' else "OpenAI"
        print(f"\n✅ {provider_name} API key found")
        
        # Initialize OpenAI client
        if provider == 'openrouter':
            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            client = OpenAI(api_key=api_key)
        
        # Get photography folder - check both possible locations
        photography_folder = project_root / 'public' / 'assets' / 'photography'
        if not photography_folder.exists():
            # Fallback to data/photography if public doesn't exist
            photography_folder = project_root / 'data' / 'photography'
            if not photography_folder.exists():
                print(f"❌ Error: Photography folder not found")
                print(f"   Checked: {project_root / 'public' / 'assets' / 'photography'}")
                print(f"   Checked: {project_root / 'data' / 'photography'}")
                sys.exit(1)
            print(f"📁 Using data/photography (public/assets/photography not found)")
        else:
            print(f"📁 Using public/assets/photography")
        
        # Process each category
        categories = ["products", "models", "environments"]
        total_images = 0
        category_stats = {}
        
        print(f"\n📁 Scanning {photography_folder}...")
        
        for category in categories:
            category_folder = photography_folder / category
            if not category_folder.exists():
                print(f"⚠️  Category folder not found: {category_folder}")
                continue
            
            image_files = get_images_from_folder(category_folder)
            if image_files:
                category_stats[category] = len(image_files)
                total_images += len(image_files)
                print(f"   ✅ {category}: {len(image_files)} images")
            else:
                print(f"   ⚠️  {category}: No images found")
        
        if total_images == 0:
            print(f"\n❌ No images found in any category")
            sys.exit(1)
        
        print(f"\n📊 Total images to process: {total_images}")
        
        # Estimate costs
        cost_estimate = estimate_cost(total_images)
        print(f"\n💰 Cost Estimate:")
        print(f"   Estimated cost: ${cost_estimate['estimated_total']:.2f}")
        print(f"   (Approximate - actual cost may vary)")
        
        # Confirm before proceeding (skip if --yes flag provided)
        print(f"\n⚠️  This will process {total_images} images across {len(category_stats)} categories.")
        if '--yes' not in sys.argv:
            response = input("Continue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled.")
                sys.exit(0)
        else:
            print("🚀 Auto-confirmed (--yes flag provided)")
        
        # Process each category
        print("\n" + "=" * 70)
        print("Processing Categories")
        print("=" * 70)
        
        for category in categories:
            category_folder = photography_folder / category
            if not category_folder.exists():
                continue
            
            image_files = get_images_from_folder(category_folder)
            if not image_files:
                continue
            
            output_file = project_root / OUTPUT_FILES[category]
            
            # Load existing metadata if file exists
            existing_metadata = {}
            if output_file.exists():
                try:
                    with open(output_file, 'r') as f:
                        existing_metadata = json.load(f)
                    print(f"\n📂 [{category}] Found existing metadata: {len(existing_metadata)} entries")
                except Exception as e:
                    print(f"⚠️  [{category}] Warning: Could not load existing metadata: {e}")
                    existing_metadata = {}
            
            # Filter out already processed images
            images_to_process = [
                img for img in image_files 
                if img.name not in existing_metadata
            ]
            
            if not images_to_process:
                print(f"✅ [{category}] All images already processed!")
                continue
            
            print(f"\n🔍 [{category}] Processing {len(images_to_process)} new images...")
            print(f"   System prompt: {CATEGORY_PROMPTS[category][:80]}...")
            
            metadata = existing_metadata.copy()
            processed_count = 0
            error_count = 0
            
            # Process with progress bar
            for image_path in tqdm(images_to_process, desc=f"[{category}]", unit="img"):
                description = analyze_image(client, image_path, category, provider=provider)
                
                if description:
                    metadata[image_path.name] = {
                        "filename": image_path.name,
                        "description": description,
                        "file_path": str(image_path.relative_to(project_root)),
                        "category": category
                    }
                    processed_count += 1
                    
                    # Save incrementally every 10 images
                    if processed_count % 10 == 0:
                        with open(output_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                else:
                    error_count += 1
            
            # Final save for this category
            print(f"💾 [{category}] Saving metadata to {output_file}...")
            with open(output_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ [{category}] Complete: {processed_count} processed, {error_count} errors")
        
        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        for category in categories:
            output_file = project_root / OUTPUT_FILES[category]
            if output_file.exists():
                with open(output_file, 'r') as f:
                    metadata = json.load(f)
                print(f"📊 {category}: {len(metadata)} total entries in {OUTPUT_FILES[category]}")
        
        print(f"\n✅ Enrichment complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("💾 Progress has been saved incrementally")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

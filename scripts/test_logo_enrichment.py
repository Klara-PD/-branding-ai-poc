#!/usr/bin/env python3
"""
Test script to process only 5 logos and show results
"""

import sys
from pathlib import Path

# Import functions from enrich_graphics.py
sys.path.insert(0, str(Path(__file__).parent))
from enrich_graphics import (
    load_environment, analyze_image, get_images_from_folder,
    OpenAI, json
)

def test_5_logos():
    """Process only 5 logos and show results"""
    print("=" * 70)
    print("Testing Logo Enrichment - 5 Images")
    print("=" * 70)
    
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
    
    # Get logo folder
    logo_folder = project_root / 'data' / 'logo_geometry'
    image_files = get_images_from_folder(logo_folder)
    
    if not image_files:
        print("❌ No images found")
        return
    
    # Limit to 5 images
    test_images = sorted(image_files)[:5]
    print(f"\n📁 Processing {len(test_images)} test images...")
    
    # System prompt for logos
    system_prompt = """You are a specialist assistant that helps users write high-quality metadata for logos.
Analyze the image and return a JSON object with exactly six fields: 'description', 'logo_type', 'style_character', 'visual_era', 'visual_style_tags', and 'brand_voice'.

### CRITICAL CONSTRAINTS (DO NOT IGNORE):
1. **NO Specific Colors:** Never mention actual color names (e.g., red, blue, green). Describe only the nature of the palette (e.g., 'monochromatic', 'high contrast', 'muted', 'vibrant').
2. **NO Brand Name Reading:** Do NOT read, quote, or paraphrase any text or brand names visible in the logo. Focus ONLY on the visual design elements.
3. **NO Specific Content:** Never mention specific depicted elements (e.g., 'animal', 'building', 'object name'). Describe ONLY the geometric construction, form, and visual approach.
4. **NO Fluff:** Do not include titles or marketing hype.

### DESCRIPTION FIELD MUST FOCUS ON:
- Geometric construction and form relationships
- Negative space usage and balance
- Stroke weight and line quality
- Relationship between icon/symbol and typography (if present)
- Visual hierarchy and composition
- Form language (geometric, organic, abstract, etc.)

### LOGO_TYPE FIELD:
Use ONE of these categories (choose the MOST descriptive):
- "wordmark" - Text-based logo, typography-focused, no symbol
- "pictorial" - Representational symbol or icon (with or without text)
- "abstract" - Non-representational, conceptual symbol (with or without text)
- "emblem" - Symbol contained within a shape or badge (with or without text)
- "lettermark" - Monogram or initial-based logo
- "mascot" - Character or figure-based logo
- "combination mark" - Both symbol and text elements combined as distinct elements

### STYLE_CHARACTER FIELD:
Use ONE or TWO words describing the overall style character:
- "tech-forward" - Modern, digital, innovative
- "heritage" - Classic, traditional, established
- "minimalist" - Simple, clean, uncluttered
- "bold" - Strong, confident, impactful
- "elegant" - Refined, sophisticated, graceful
- "playful" - Fun, whimsical, lighthearted
- "corporate" - Professional, formal, business-like
- "artistic" - Creative, expressive, unique
- "rugged" - Strong, durable, outdoorsy
- "luxury" - Premium, exclusive, high-end

### VISUAL_ERA FIELD:
Use ONE word describing the visual era/period the style references:
- "modern" - Contemporary, current design trends
- "brutalist" - Raw, bold, architectural, geometric
- "mid-century" - 1950s-1960s aesthetic
- "vintage" - Classic, old-fashioned, nostalgic (pre-1980s)
- "retro" - 1980s-1990s aesthetic
- "contemporary" - Current, present-day style
- "futuristic" - Forward-looking, sci-fi inspired
- "timeless" - Classic, doesn't reference specific era
- "art-deco" - 1920s-1930s style
- "postmodern" - Eclectic, experimental

### VISUAL_STYLE_TAGS FIELD:
Use an array of 5 tags describing technical and visual characteristics:
Examples: "monoline", "negative-space", "geometric", "gradient-fill", "sans-serif", "serif", "hand-drawn", "vector", "thick-stroke", "thin-stroke", "rounded", "angular", "symmetrical", "asymmetrical", "layered", "flat", "dimensional"

### BRAND_VOICE FIELD:
Use ONE word describing the perceived personality:
- "authoritative" - Commanding, confident, powerful
- "approachable" - Friendly, welcoming, accessible
- "innovative" - Forward-thinking, creative, cutting-edge
- "trustworthy" - Reliable, dependable, stable
- "playful" - Fun, lighthearted, energetic
- "sophisticated" - Refined, elegant, mature
- "bold" - Confident, strong, assertive
- "friendly" - Warm, inviting, personable
- "professional" - Serious, business-like, formal
- "creative" - Artistic, expressive, unique

### OUTPUT FORMAT (JSON ONLY):
{
  "description": "Focus on geometric construction, negative space usage, stroke weight, and the relationship between the icon and typography.",
  "logo_type": "one category from the list above",
  "style_character": "one or two words from the style character list",
  "visual_era": "one word from the visual era list",
  "visual_style_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "brand_voice": "one word from the brand voice list"
}"""
    
    USER_PROMPT = "Analyze this image and return a JSON object with 'description', 'logo_type', 'style_character', 'visual_era', 'visual_style_tags', and 'brand_voice' fields."
    
    results = {}
    required_fields = ['description', 'logo_type', 'style_character', 'visual_era', 'visual_style_tags', 'brand_voice']
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n[{i}/5] Processing {image_path.name}...")
        analysis_result = analyze_image(client, image_path, system_prompt, provider=provider, required_fields=required_fields)
        
        if analysis_result:
            results[image_path.name] = {
                "filename": image_path.name,
                "description": analysis_result.get("description", ""),
                "logo_type": analysis_result.get("logo_type", ""),
                "style_character": analysis_result.get("style_character", ""),
                "visual_era": analysis_result.get("visual_era", ""),
                "visual_style_tags": analysis_result.get("visual_style_tags", []),
                "brand_voice": analysis_result.get("brand_voice", ""),
            }
            print(f"✅ Success!")
        else:
            print(f"❌ Failed")
            results[image_path.name] = {"error": "Failed to process"}
    
    # Show results
    print("\n" + "=" * 70)
    print("RESULTS - All 5 Examples")
    print("=" * 70)
    
    for i, (filename, data) in enumerate(results.items(), 1):
        if "error" not in data:
            print(f"\n📄 Example {i}: {filename}")
            print(f"   Logo Type: {data.get('logo_type', 'N/A')}")
            print(f"   Style Character: {data.get('style_character', 'N/A')}")
            print(f"   Visual Era: {data.get('visual_era', 'N/A')}")
            print(f"   Brand Voice: {data.get('brand_voice', 'N/A')}")
            print(f"   Description: {data['description'][:150]}...")
            print(f"   Visual Style Tags: {', '.join(data['visual_style_tags'][:5])}")
        else:
            print(f"\n❌ {filename}: {data['error']}")
    
    # Save test results
    test_output = project_root / 'data' / 'logo_metadata_test.json'
    with open(test_output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {test_output.name}")
    print(f"📊 Processed: {sum(1 for v in results.values() if 'error' not in v)}/{len(results)} successfully")
    
    return results

if __name__ == '__main__':
    try:
        test_5_logos()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

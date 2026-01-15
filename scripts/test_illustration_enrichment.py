#!/usr/bin/env python3
"""
Test script to process only 10 illustrations and show results
"""

import sys
from pathlib import Path

# Import functions from enrich_graphics.py
sys.path.insert(0, str(Path(__file__).parent))
from enrich_graphics import (
    load_environment, analyze_image, get_images_from_folder,
    process_standard_mode, OpenAI, json
)

def test_10_illustrations():
    """Process only 10 illustrations and show results"""
    print("=" * 70)
    print("Testing Illustration Enrichment - 10 Images")
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
    
    # Get illustration folder
    illustration_folder = project_root / 'data' / 'illustration'
    image_files = get_images_from_folder(illustration_folder)
    
    if not image_files:
        print("❌ No images found")
        return
    
    # Limit to 5 images
    test_images = sorted(image_files)[:5]
    print(f"\n📁 Processing {len(test_images)} test images...")
    
    # System prompt for illustrations (same as in enrich_graphics.py)
    system_prompt = """You are a specialist assistant that helps users write high-quality metadata for illustrations.
Analyze the image and return a JSON object with exactly seven fields: 'description', 'content_category', 'style_character', 'visual_era', 'audience_appeal', 'visual_style_tags', and 'mood_tone'.

### CRITICAL CONSTRAINTS (DO NOT IGNORE):
1. **NO Specific Colors:** Never mention actual color names (e.g., red, green, rainbow). Describe only the nature of the palette (e.g., 'monochromatic', 'high contrast', 'muted', 'vibrant').
2. **NO Specific Content Details:** Never mention specific depicted elements (e.g., 'face', 'couple', 'car', 'bottle', 'lips', 'garden'). Describe ONLY the artistic style, technique, and visual approach.
3. **NO Scene Description:** Do NOT describe what is shown in the image. Focus ONLY on HOW it is rendered (technique, style, composition approach, line quality, texture, etc.).
4. **NO Text Content:** If text appears, NEVER quote it or paraphrase it. Describe ONLY the typography style (e.g., 'bold', 'handwritten', 'geometric') without mentioning the content.
5. **NO Fluff:** Do not include titles or marketing hype.

### CONTENT_CATEGORY FIELD:
Use ONE of these general categories (NO detailed description):
- "figurative" - Contains people, characters, or human-like forms
- "nature" - Contains natural elements (plants, landscapes, animals, etc.)
- "abstract" - Abstract or non-representational imagery
- "product" - Product or object rendered/displayed
- "element" - Single element, icon, or symbol
- "typography" - Text-focused or letterform-based
- "mixed" - Combination of multiple categories

### STYLE_CHARACTER FIELD:
Use ONE or TWO words describing the overall style character:
- "elegant" - Sophisticated, refined, graceful
- "childish" - Playful, naive, child-like
- "pop" - Bold, vibrant, pop culture influenced
- "sophisticated" - Mature, polished, refined
- "playful" - Fun, whimsical, lighthearted
- "corporate" - Professional, business-like, formal
- "artistic" - Creative, expressive, avant-garde
- "minimalist" - Simple, clean, uncluttered
- "maximalist" - Rich, detailed, ornate
- "quirky" - Unconventional, offbeat, unique

### VISUAL_ERA FIELD:
Use ONE word describing the visual era/period the style references:
- "modern" - Contemporary, current design trends
- "vintage" - Classic, old-fashioned, nostalgic (pre-1980s)
- "retro" - 1980s-1990s aesthetic
- "contemporary" - Current, present-day style
- "futuristic" - Forward-looking, sci-fi inspired
- "timeless" - Classic, doesn't reference specific era
- "mid-century" - 1950s-1960s aesthetic
- "art-deco" - 1920s-1930s style
- "brutalist" - Raw, bold, architectural
- "postmodern" - Eclectic, experimental

### AUDIENCE_APPEAL FIELD:
Use ONE word describing the target audience (NOT product audience, but visual style audience):
- "children" - Appealing to kids, simple, colorful
- "teens" - Youthful, trendy, energetic
- "adults" - Mature, sophisticated, refined
- "professionals" - Business, corporate, formal
- "general" - Broad appeal, universal
- "niche" - Specific, specialized appeal
- "youthful" - Young adults, vibrant, fresh
- "mature" - Older adults, classic, refined

### DESCRIPTION FIELD MUST FOCUS ON:
- Artistic technique (vector, watercolor, digital, etc.)
- Style approach (flat, dimensional, abstract, realistic, etc.)
- Composition structure (centered, dynamic, grid-based, etc.)
- Line quality and form (thick, thin, organic, geometric, etc.)
- Texture and surface quality (smooth, grainy, paper-like, etc.)
- Visual treatment (gradient, solid, layered, etc.)

### OUTPUT FORMAT (JSON ONLY):
{
  "description": "Clear, concise description focusing ONLY on artistic technique, style, and visual approach - NOT the subject matter.",
  "content_category": "one category from the list above",
  "style_character": "one or two words from the style character list",
  "visual_era": "one word from the visual era list",
  "audience_appeal": "one word from the audience appeal list",
  "visual_style_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "mood_tone": "Brief phrase describing emotional resonance"
}"""
    
    USER_PROMPT = "Analyze this image and return a JSON object with 'description', 'visual_style_tags', and 'mood_tone' fields."
    
    results = {}
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n[{i}/5] Processing {image_path.name}...")
        analysis_result = analyze_image(client, image_path, system_prompt, provider=provider)
        
        if analysis_result:
            results[image_path.name] = {
                "filename": image_path.name,
                "description": analysis_result.get("description", ""),
                "content_category": analysis_result.get("content_category", ""),
                "style_character": analysis_result.get("style_character", ""),
                "visual_era": analysis_result.get("visual_era", ""),
                "audience_appeal": analysis_result.get("audience_appeal", ""),
                "visual_style_tags": analysis_result.get("visual_style_tags", []),
                "mood_tone": analysis_result.get("mood_tone", ""),
            }
            print(f"✅ Success!")
        else:
            print(f"❌ Failed")
            results[image_path.name] = {"error": "Failed to process"}
    
    # Show results
    print("\n" + "=" * 70)
    print("RESULTS - First 3 Examples")
    print("=" * 70)
    
    for i, (filename, data) in enumerate(list(results.items())[:3], 1):
        if "error" not in data:
            print(f"\n📄 Example {i}: {filename}")
            print(f"   Content Category: {data.get('content_category', 'N/A')}")
            print(f"   Style Character: {data.get('style_character', 'N/A')}")
            print(f"   Visual Era: {data.get('visual_era', 'N/A')}")
            print(f"   Audience Appeal: {data.get('audience_appeal', 'N/A')}")
            print(f"   Description: {data['description'][:150]}...")
            print(f"   Visual Style Tags: {', '.join(data['visual_style_tags'][:5])}")
            print(f"   Mood/Tone: {data['mood_tone']}")
        else:
            print(f"\n❌ {filename}: {data['error']}")
    
    # Save test results
    test_output = project_root / 'data' / 'illustration_metadata_test.json'
    with open(test_output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {test_output.name}")
    print(f"📊 Processed: {sum(1 for v in results.values() if 'error' not in v)}/{len(results)} successfully")
    
    return results

if __name__ == '__main__':
    try:
        test_10_illustrations()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

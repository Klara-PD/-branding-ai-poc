#!/usr/bin/env python3
"""
Vector-Based Category Refinement Script

This script implements vector arithmetic for vibe steering:
1. Re-encode the brief to get base_vector
2. For each slider, encode steering prompts and apply vector math
3. Normalize the final vector
4. Query Pinecone with the refined vector
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

try:
    from pinecone import Pinecone
    from sentence_transformers import SentenceTransformer
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required package. {e}", file=sys.stderr)
    print("Please install: pip install pinecone sentence-transformers numpy pillow", file=sys.stderr)
    sys.exit(1)

# STEERING_PROMPTS: Positive and negative prompts for each slider
# CLIP performs better with natural language descriptions of scenes/lighting
STEERING_PROMPTS = {
    # COLORS
    "temp": {"pos": "warm golden hour lighting, cinematic sun-drenched atmosphere", "neg": "cool blue tones, cold winter atmosphere, arctic lighting"},
    "vibrancy": {"pos": "neon highly saturated colors, vibrant pop-art aesthetic", "neg": "muted pastel colors, desaturated film look, soft washed out"},
    "brightness": {"pos": "bright high-key photography, white background, airy", "neg": "dark moody low-key lighting, deep shadows, cinematic noir"},
    
    # TYPOGRAPHY (Keep simple as these are structural)
    "style": {"pos": "modern sans-serif typography, clean Helvetica font", "neg": "classic serif typography, traditional Times New Roman"},
    "weight": {"pos": "bold heavy typography, thick distinct strokes", "neg": "thin elegant typography, hairline font"},
    "width": {"pos": "extended wide typography, stretched letters", "neg": "condensed narrow typography, tall letters"},

    # LOGO
    "structure": {"pos": "abstract minimalist icon, simple symbol", "neg": "typographic wordmark logo, text-based branding"},
    "shape": {"pos": "organic fluid shapes, nature-inspired curves", "neg": "geometric sharp shapes, grid-based polygon design"},
    "complexity": {"pos": "minimalist reductionist logo, single line", "neg": "detailed complex emblem, intricate crest illustration"},

    # ILLUSTRATION
    "dimension": {"pos": "3d render style, blender claymorphism, volumetric lighting", "neg": "flat 2d vector art, solid colors, clean lines"},
    "realism": {"pos": "abstract surrealism art, distorted forms", "neg": "realistic technical drawing, detailed sketch"},
    "tool": {"pos": "clean digital vector art, illustrator", "neg": "hand-drawn charcoal sketch, rough pencil texture"},

    # PHOTO: MODEL
    "posing": {"pos": "candid lifestyle photography, natural movement, caught in the moment", "neg": "staged studio fashion photography, static pose, lookbook"},
    "framing": {"pos": "extreme close-up portrait, face focus", "neg": "wide angle full body shot, environmental context"},
    "gaze": {"pos": "model looking directly at camera, intense eye contact", "neg": "model looking away, candid side profile, unware of camera"},

    # PHOTO: PRODUCT
    "context": {"pos": "product isolated on plain background, minimal studio", "neg": "product in lifestyle context, in use, real life environment"},
    "lighting": {"pos": "soft diffused window lighting, soft shadows", "neg": "hard dramatic studio lighting, high contrast, sharp shadows"},
    "focus": {"pos": "macro detail shot, texture focus", "neg": "full product shot, entire object visible"},

    # PHOTO: ENVIRONMENT
    "location": {"pos": "interior design photography, indoor living space", "neg": "exterior architecture photography, outdoor facade"},
    "nature": {"pos": "urban concrete environment, city street, brutalist", "neg": "nature landscape, forest, greenery, organic environment"},
    "time": {"pos": "daytime bright sunlight, noon clear sky", "neg": "night time photography, artificial city lights, evening"}
}

# Map old frontend keys to new steering prompt keys
# This maintains compatibility with the existing frontend while using the new descriptive prompts
KEY_MAPPING = {
    # Colors
    'warm_cool': 'temp',
    'pastel_neon': 'vibrancy',
    'dark_bright': 'brightness',
    
    # Typography
    'serif_sans': 'style',
    'light_bold': 'weight',
    'condensed_extended': 'width',
    
    # Logo
    'typographic_iconic': 'structure',
    'geometric_organic': 'shape',
    'minimal_detailed': 'complexity',
    
    # Illustration
    'flat_3d': 'dimension',
    'abstract_literal': 'realism',
    'digital_handdrawn': 'tool',
    
    # Photo_Model
    'staged_candid': 'posing',
    'portrait_fullbody': 'framing',
    'direct_gaze_looking_away': 'gaze',
    
    # Photo_Product
    'studio_clean_contextual': 'context',
    'soft_light_hard_light': 'lighting',
    'macro_full_object': 'focus',
    
    # Photo_Environment
    'interior_exterior': 'location',
    'urban_nature': 'nature',
    'day_night': 'time',
}

# Map category types to Pinecone namespaces/categories
CATEGORY_NAMESPACE_MAP = {
    'colors': ['brand_color_mood'],
    'typography': ['typography'],
    'logo': ['logo_geometry'],
    'illustration': ['illustration'],
    'photo_model': ['photography/models', 'models'],
    'photo_product': ['photography/products', 'products'],
    'photo_environment': ['photography/environments', 'environments'],
}


def main():
    """Main function to refine category search using vector arithmetic"""
    print("🎛️ Vector-based category refinement started", file=sys.stderr, flush=True)
    
    if len(sys.argv) < 6:
        print(json.dumps({"error": "Usage: python refine_category.py <brief_file> <category_type> <slider_values_json> <api_key> <index_name> [image_path]"}), file=sys.stderr)
        sys.exit(1)
    
    brief_file = sys.argv[1]
    category_type = sys.argv[2]
    slider_values_json = sys.argv[3]
    api_key = sys.argv[4]
    index_name = sys.argv[5]
    image_path = sys.argv[6] if len(sys.argv) > 6 else None
    exclude_image_id = sys.argv[7] if len(sys.argv) > 7 else None  # ID to exclude from results
    
    # Read brief (still needed as fallback)
    try:
        with open(brief_file, 'r') as f:
            brand_brief = f.read().strip()
        print(f"📝 Brief loaded: {len(brand_brief)} characters", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read brief file: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Parse slider values
    try:
        slider_values = json.loads(slider_values_json)
        print(f"🎚️ Slider values: {len(slider_values)} sliders", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse slider values: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Load CLIP model
    print("🤖 Loading CLIP model (clip-ViT-B-32)...", file=sys.stderr, flush=True)
    try:
        model = SentenceTransformer('clip-ViT-B-32')
        print("✅ CLIP model loaded", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load CLIP model: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Step 1: Get base_vector from image or brief
    # #region agent log
    import json as json_module
    log_data = {"location": "refine_category.py:182", "message": "Image path check", "data": {"has_image_path": bool(image_path), "image_path": image_path, "path_exists": Path(image_path).exists() if image_path else False}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}
    with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
        f.write(json_module.dumps(log_data) + '\n')
    # #endregion
    if image_path and Path(image_path).exists():
        print(f"🖼️ Loading image to get base_vector: {image_path}", file=sys.stderr, flush=True)
        try:
            # Load and encode image with CLIP
            img = Image.open(image_path)
            # #region agent log
            log_data = {"location": "refine_category.py:189", "message": "Image opened successfully", "data": {"image_path": image_path, "image_mode": img.mode, "image_size": img.size}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}
            with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
                f.write(json_module.dumps(log_data) + '\n')
            # #endregion
            # CLIP can encode images directly
            base_vector = model.encode(img, convert_to_numpy=True)
            print(f"✅ Image base vector: {len(base_vector)} dimensions", file=sys.stderr, flush=True)
            # #region agent log
            log_data = {"location": "refine_category.py:193", "message": "Image encoded successfully", "data": {"image_path": image_path, "vector_length": len(base_vector), "vector_norm": float(np.linalg.norm(base_vector))}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}
            with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
                f.write(json_module.dumps(log_data) + '\n')
            # #endregion
        except Exception as e:
            print(f"⚠️ Failed to encode image, falling back to brief: {e}", file=sys.stderr, flush=True)
            # #region agent log
            log_data = {"location": "refine_category.py:197", "message": "Image encoding failed", "data": {"image_path": image_path, "error": str(e)}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}
            with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
                f.write(json_module.dumps(log_data) + '\n')
            # #endregion
            # Fallback to brief
            try:
                base_vector = model.encode(brand_brief, convert_to_numpy=True)
                print(f"✅ Brief base vector (fallback): {len(base_vector)} dimensions", file=sys.stderr, flush=True)
            except Exception as e2:
                print(json.dumps({"error": f"Failed to encode brief: {e2}"}), file=sys.stderr)
                sys.exit(1)
    else:
        # Use brief as base
        print("🔢 Encoding brief to get base_vector...", file=sys.stderr, flush=True)
        try:
            base_vector = model.encode(brand_brief, convert_to_numpy=True)
            print(f"✅ Brief base vector: {len(base_vector)} dimensions", file=sys.stderr, flush=True)
        except Exception as e:
            print(json.dumps({"error": f"Failed to encode brief: {e}"}), file=sys.stderr)
            sys.exit(1)
    
    # Step 2: Calculate steering vectors using Difference Vector (Push/Pull) method
    print("🧮 Calculating steering vectors using Difference Vector method...", file=sys.stderr, flush=True)
    final_vector = base_vector.copy()
    
    for slider_key, slider_value in slider_values.items():
        # Map old frontend keys to new steering prompt keys
        mapped_key = KEY_MAPPING.get(slider_key, slider_key)
        
        if mapped_key not in STEERING_PROMPTS:
            print(f"⚠️ Unknown slider key: {slider_key} (mapped to {mapped_key}), skipping", file=sys.stderr, flush=True)
            continue
        
        if abs(slider_value) < 0.01:  # Skip if slider is essentially neutral
            continue
        
        # Step A: Get the two poles from the dictionary
        pos_desc = STEERING_PROMPTS[mapped_key]['pos']
        neg_desc = STEERING_PROMPTS[mapped_key]['neg']
        
        # Step B: Calculate the Difference Vector (The "Axis")
        # This represents the pure concept of moving from negative to positive pole
        print(f"  📊 Calculating axis for {slider_key}...", file=sys.stderr, flush=True)
        pos_vector = model.encode(pos_desc, convert_to_numpy=True)
        neg_vector = model.encode(neg_desc, convert_to_numpy=True)
        axis_vector = pos_vector - neg_vector
        
        # Step C: Apply to the base with STRONGER weight
        # We use the slider value (-1 to 1) to determine direction along this axis
        # Weight of 0.75 ensures strong steering effect
        steering_contribution = axis_vector * slider_value * 0.75
        final_vector = final_vector + steering_contribution
        
        direction = "toward positive" if slider_value > 0 else "toward negative"
        print(f"  ✓ Applied {slider_key}: {slider_value:.2f} ({direction}) -> axis vector * {slider_value:.2f} * 0.75", file=sys.stderr, flush=True)
    
    # Step 3: Normalize final_vector
    print("📐 Normalizing final vector...", file=sys.stderr, flush=True)
    vector_norm = np.linalg.norm(final_vector)
    if vector_norm > 0:
        final_vector = final_vector / vector_norm
    print(f"✅ Vector normalized (norm was {vector_norm:.4f})", file=sys.stderr, flush=True)
    # #region agent log
    log_data = {"location": "refine_category.py:262", "message": "After steering and normalization", "data": {"final_vector_norm": float(np.linalg.norm(final_vector)), "vector_changed": float(np.linalg.norm(final_vector - base_vector))}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
    with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
        f.write(json_module.dumps(log_data) + '\n')
    # #endregion
    
    # Step 4: Connect to Pinecone
    print("🌲 Connecting to Pinecone...", file=sys.stderr, flush=True)
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        print(f"✅ Connected to Pinecone index: {index_name}", file=sys.stderr, flush=True)
    except Exception as e:
        print(json.dumps({"error": f"Failed to connect to Pinecone: {e}"}), file=sys.stderr)
        sys.exit(1)
    
    # Step 5: Query Pinecone with final_vector
    print("🔍 Querying Pinecone with refined vector...", file=sys.stderr, flush=True)
    try:
        # Increase top_k significantly to ensure we have enough results after filtering and exclusion
        # With 2,700 images total, we need to query more to get enough in each category
        top_k = 500  # Increased from 200 to 500 to get more results
        results = index.query(
            vector=final_vector.tolist(),
            top_k=top_k,
            include_metadata=True
        )
        
        print(f"✅ Query complete: {len(results.matches)} results found (queried top_k={top_k})", file=sys.stderr, flush=True)
        
        # Filter results by category namespace if specified
        allowed_categories = CATEGORY_NAMESPACE_MAP.get(category_type, [])
        if allowed_categories:
            filtered_matches = []
            for match in results.matches:
                cat = match.metadata.get('category', '') if match.metadata else ''
                if any(allowed in cat or cat in allowed for allowed in allowed_categories):
                    filtered_matches.append(match)
            results.matches = filtered_matches
            print(f"📊 Filtered to {len(filtered_matches)} results in category: {category_type} (from {len(results.matches) + len(filtered_matches) - len(filtered_matches)} total)", file=sys.stderr, flush=True)
            
            if len(filtered_matches) == 0:
                print(f"⚠️ WARNING: No results in category {category_type} after filtering!", file=sys.stderr, flush=True)
                print(f"⚠️ Allowed categories: {allowed_categories}", file=sys.stderr, flush=True)
                # Show sample categories from results for debugging
                sample_cats = [m.metadata.get('category', 'NO_CATEGORY') if m.metadata else 'NO_METADATA' for m in results.matches[:10]]
                print(f"⚠️ Sample categories in results: {set(sample_cats)}", file=sys.stderr, flush=True)
        
        # Exclude current image from results if specified
        # BUT: Only exclude if we have enough results to spare (at least 2 results after exclusion)
        if exclude_image_id:
            original_count = len(results.matches)
            original_top_id = results.matches[0].id if results.matches else None
            
            # Only exclude if we have more than 1 result (need at least 1 result after exclusion)
            if original_count > 1:
                results.matches = [m for m in results.matches if m.id != exclude_image_id]
                excluded_count = original_count - len(results.matches)
                new_top_id = results.matches[0].id if results.matches else None
                
                if excluded_count > 0:
                    print(f"🚫 Excluded {excluded_count} current image(s) from results (excluded ID: {exclude_image_id})", file=sys.stderr, flush=True)
                    print(f"📊 Original top ID: {original_top_id}, New top ID: {new_top_id}", file=sys.stderr, flush=True)
                    print(f"📊 Remaining results after exclusion: {len(results.matches)}", file=sys.stderr, flush=True)
                    
                    # Verify we actually got a different image
                    if new_top_id == original_top_id:
                        print(f"⚠️ WARNING: After exclusion, top result is still the same! This shouldn't happen.", file=sys.stderr, flush=True)
                else:
                    print(f"⚠️ No images excluded (excluded ID: {exclude_image_id}, top result ID: {original_top_id})", file=sys.stderr, flush=True)
                    print(f"⚠️ This might mean the ID format doesn't match. Checking ID formats...", file=sys.stderr, flush=True)
                    if results.matches:
                        print(f"⚠️ Sample result IDs: {[m.id for m in results.matches[:5]]}", file=sys.stderr, flush=True)
                
                # If exclusion removed all results, this is a problem
                if len(results.matches) == 0:
                    print(f"❌ ERROR: Exclusion removed ALL results! Query returned {original_count} results, but all were excluded.", file=sys.stderr, flush=True)
                    print(f"❌ This means the current image was the ONLY result in this category.", file=sys.stderr, flush=True)
            else:
                print(f"⚠️ Only {original_count} result(s) found - skipping exclusion to avoid empty results", file=sys.stderr, flush=True)
                print(f"⚠️ Will return the same image (this means the query needs more diversity)", file=sys.stderr, flush=True)
            
            # #region agent log
            log_data = {"location": "refine_category.py:318", "message": "Exclusion check", "data": {"exclude_image_id": exclude_image_id, "original_count": original_count, "excluded_count": excluded_count, "remaining_count": len(results.matches), "original_top_id": original_top_id, "new_top_id": new_top_id, "exclusion_worked": excluded_count > 0, "all_results_excluded": len(results.matches) == 0}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run2", "hypothesisId": "D"}
            with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
                f.write(json_module.dumps(log_data) + '\n')
            # #endregion
        
        # Format results
        formatted_results = {
            "results": [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata or {},
                }
                for match in results.matches
            ],
            "count": len(results.matches),
        }
        # #region agent log
        top_result_ids = [r.id for r in results.matches[:5]]
        log_data = {"location": "refine_category.py:314", "message": "Query results", "data": {"result_count": len(results.matches), "top_5_ids": top_result_ids, "top_score": float(results.matches[0].score) if results.matches else None}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
        with open('/Users/klara/Documents/branding-ai-poc/.cursor/debug.log', 'a') as f:
            f.write(json_module.dumps(log_data) + '\n')
        # #endregion
        
        # Output JSON to stdout ONLY
        print(json.dumps(formatted_results), flush=True)
        
    except Exception as e:
        print(json.dumps({"error": f"Failed to query Pinecone: {e}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

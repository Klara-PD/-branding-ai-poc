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

def generate_dynamic_poles(brand_brief: str, left_label: str, right_label: str) -> dict:
    """
    Generate dynamic steering poles based on brand brief and slider labels.
    
    Args:
        brand_brief: The brand's visual_prompt (e.g., "coffee shop in Barcelona")
        left_label: Left side of slider (e.g., "Urban")
        right_label: Right side of slider (e.g., "Nature")
    
    Returns:
        Dictionary with "pos" and "neg" poles:
        - pos: brand_brief + " more " + right_label (e.g., "coffee shop in Barcelona more nature")
        - neg: brand_brief + " more " + left_label (e.g., "coffee shop in Barcelona more urban")
    """
    # Create poles by combining brand brief with slider direction
    pos_pole = f"{brand_brief} more {right_label.lower()}"
    neg_pole = f"{brand_brief} more {left_label.lower()}"
    
    return {
        "pos": pos_pole,
        "neg": neg_pole
}

def compute_base_weight_scale(max_abs_slider: float) -> float:
    """
    Smoothly reduce base vector weight when sliders move toward extremes.
    - <= 0.30: no change (1.0)
    - >= 0.70: reduce by 50% (0.5)
    - 0.30..0.70: linear ramp from 1.0 to 0.5
    """
    if max_abs_slider <= 0.30:
        return 1.0
    if max_abs_slider >= 0.70:
        return 0.5
    ramp = (max_abs_slider - 0.30) / 0.40
    return 1.0 - (0.5 * ramp)

def get_opposite_keywords(slider_key: str, slider_value: float, tuning_meta: dict) -> list:
    meta = tuning_meta.get(slider_key, {}) if isinstance(tuning_meta, dict) else {}
    if slider_value > 0:
        return meta.get('leftKeywords', []) or []
    if slider_value < 0:
        return meta.get('rightKeywords', []) or []
    return []

def get_palette_for_direction(slider_key: str, slider_value: float, tuning_meta: dict) -> list:
    meta = tuning_meta.get(slider_key, {}) if isinstance(tuning_meta, dict) else {}
    if slider_value > 0:
        return meta.get('rightPalettes', []) or []
    if slider_value < 0:
        return meta.get('leftPalettes', []) or []
    return []

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
        print(json.dumps({"error": "Usage: python refine_category.py <brief_file> <category_type> <slider_values_json> <api_key> <index_name> [image_path] [exclude_image_id] [slider_labels_json] [slider_tuning_meta_json] [locked_image_ids_json]"}), file=sys.stderr)
        sys.exit(1)
    
    brief_file = sys.argv[1]
    category_type = sys.argv[2]
    slider_values_json = sys.argv[3]
    api_key = sys.argv[4]
    index_name = sys.argv[5]
    image_path = sys.argv[6] if len(sys.argv) > 6 else None
    exclude_image_id = sys.argv[7] if len(sys.argv) > 7 else None  # ID to exclude from results
    slider_labels_json = sys.argv[8] if len(sys.argv) > 8 else None  # Slider labels for dynamic pole generation
    slider_tuning_meta_json = sys.argv[9] if len(sys.argv) > 9 else None  # Keywords/palettes per slider
    locked_image_ids_json = sys.argv[10] if len(sys.argv) > 10 else None  # Locked IDs within category
    
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
    
    # Parse slider labels (for dynamic pole generation)
    slider_labels = {}
    if slider_labels_json:
        try:
            slider_labels = json.loads(slider_labels_json)
            print(f"🏷️ Slider labels: {len(slider_labels)} sliders", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"⚠️ Failed to parse slider labels, will use fallback: {e}", file=sys.stderr, flush=True)
            slider_labels = {}
    else:
        print(f"⚠️ No slider labels provided, will use fallback labels ('left'/'right')", file=sys.stderr, flush=True)

    # Parse tuning meta (keywords + palettes)
    slider_tuning_meta = {}
    if slider_tuning_meta_json:
        try:
            slider_tuning_meta = json.loads(slider_tuning_meta_json)
            print(f"🏷️ Slider tuning meta: {len(slider_tuning_meta)} sliders", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"⚠️ Failed to parse slider tuning meta, ignoring: {e}", file=sys.stderr, flush=True)
            slider_tuning_meta = {}

    # Parse locked image IDs
    locked_image_ids = []
    if locked_image_ids_json:
        try:
            locked_image_ids = json.loads(locked_image_ids_json)
            if not isinstance(locked_image_ids, list):
                locked_image_ids = []
            print(f"🔒 Locked image IDs: {len(locked_image_ids)}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"⚠️ Failed to parse locked image IDs, ignoring: {e}", file=sys.stderr, flush=True)
            locked_image_ids = []
    
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
    base_vector_norm = np.linalg.norm(base_vector)
    max_abs_slider = max((abs(v) for v in slider_values.values()), default=0.0)
    base_weight_scale = compute_base_weight_scale(max_abs_slider)
    final_vector = base_vector * base_weight_scale
    print(f"⚖️ Base vector weight scale: {base_weight_scale:.2f} (max_abs_slider={max_abs_slider:.2f})", file=sys.stderr, flush=True)
    
    # Track steering impact for debugging
    total_steering_magnitude = 0.0
    slider_count = 0
    
    for slider_key, slider_value in slider_values.items():
        if abs(slider_value) < 0.01:  # Skip if slider is essentially neutral
            continue
        
        # Step A: Generate dynamic poles based on brand brief and slider labels
        # Get slider labels (left/right) from the labels mapping
        slider_label_info = slider_labels.get(slider_key, {})
        left_label = slider_label_info.get('left', 'left')
        right_label = slider_label_info.get('right', 'right')
        
        # Debug: Log what labels we're using
        if slider_key not in slider_labels:
            print(f"  ⚠️ Slider key '{slider_key}' not found in slider_labels, using fallback labels", file=sys.stderr, flush=True)
            print(f"     Available keys: {list(slider_labels.keys())}", file=sys.stderr, flush=True)
        
        # Generate dynamic poles: brand_brief + "more [label]"
        poles = generate_dynamic_poles(brand_brief, left_label, right_label)
        pos_desc = poles['pos']
        neg_desc = poles['neg']
        
        print(f"  📊 Generating dynamic poles for {slider_key}...", file=sys.stderr, flush=True)
        print(f"     Left label: '{left_label}', Right label: '{right_label}'", file=sys.stderr, flush=True)
        print(f"     Positive: {pos_desc}", file=sys.stderr, flush=True)
        print(f"     Negative: {neg_desc}", file=sys.stderr, flush=True)
        
        # Step B: Calculate the Difference Vector (The "Axis")
        # This represents the pure concept of moving from negative to positive pole
        print(f"  📊 Calculating axis for {slider_key}...", file=sys.stderr, flush=True)
        pos_vector = model.encode(pos_desc, convert_to_numpy=True)
        neg_vector = model.encode(neg_desc, convert_to_numpy=True)
        axis_vector = pos_vector - neg_vector
        
        # Step C: Apply to the base with EXTREME weight for slider extremes
        # We use the slider value (-1 to 1) to determine direction along this axis
        # Base weight increased significantly to ensure visible changes
        # When slider is at extremes (close to ±1), apply much stronger steering
        base_weight = 5.0  # Increased from 2.5 to 5.0 for more visible changes
        
        # Exponential scaling: slider values closer to ±1 get exponentially stronger effect
        # abs(slider_value) ranges from 0 to 1, so abs(slider_value)^2 gives more weight to extremes
        # For example: 0.5 -> 0.25x, 0.8 -> 0.64x, 1.0 -> 1.0x (full effect)
        # We want extremes to be MUCH stronger, so we use a power function
        abs_slider = abs(slider_value)
        # Use cubic scaling: 0.5 -> 0.125x, 0.8 -> 0.512x, 1.0 -> 1.0x (full effect)
        # Then multiply by a boost factor for extremes
        extreme_boost = 1.0 + (abs_slider ** 2) * 4.0  # At 1.0, boost is 5.0x (increased from 3.0x)
        steering_weight = base_weight * extreme_boost
        
        # For maximum extremes (slider at ±1), apply even stronger effect
        if abs_slider > 0.8:  # Lowered threshold from 0.9 to 0.8 for earlier extreme boost
            # At extremes, add extra boost
            extreme_multiplier = 2.0 + (abs_slider - 0.8) * 5.0  # At 1.0, multiplier is 3.0x (increased from 2.0x)
            steering_weight *= extreme_multiplier
        
        # Smooth small movements (<30%) by scaling down the steering weight
        if abs_slider < 0.30:
            steering_weight *= (abs_slider / 0.30)

        # Negative boosting: push away from the opposite pole keywords
        neg_keywords = get_opposite_keywords(slider_key, slider_value, slider_tuning_meta)
        neg_boost_vector = None
        neg_boost_weight = 0.0
        if neg_keywords:
            neg_boost_weight = 0.6 * abs_slider
            neg_boost_vector = model.encode(" ".join(neg_keywords), convert_to_numpy=True)

        steering_contribution = axis_vector * slider_value * steering_weight
        if neg_boost_vector is not None and neg_boost_weight > 0:
            steering_contribution = steering_contribution - (neg_boost_vector * neg_boost_weight)
        steering_magnitude = np.linalg.norm(steering_contribution)
        total_steering_magnitude += steering_magnitude
        slider_count += 1
        
        final_vector = final_vector + steering_contribution
        
        direction = "toward positive" if slider_value > 0 else "toward negative"
        print(f"  ✓ Applied {slider_key}: {slider_value:.2f} ({direction}) -> axis vector * {slider_value:.2f} * {steering_weight:.2f} (magnitude: {steering_magnitude:.4f}, extreme_boost: {extreme_boost:.2f}x)", file=sys.stderr, flush=True)
    
    # Debug: Log steering impact before normalization
    if slider_count > 0:
        vector_before_norm = np.linalg.norm(final_vector)
        vector_change_before_norm = np.linalg.norm(final_vector - base_vector)
        print(f"📊 Steering impact (before normalization):", file=sys.stderr, flush=True)
        print(f"   Base vector norm: {base_vector_norm:.4f}", file=sys.stderr, flush=True)
        print(f"   Final vector norm (before norm): {vector_before_norm:.4f}", file=sys.stderr, flush=True)
        print(f"   Total steering magnitude: {total_steering_magnitude:.4f}", file=sys.stderr, flush=True)
        print(f"   Vector change magnitude: {vector_change_before_norm:.4f}", file=sys.stderr, flush=True)
        print(f"   Active sliders: {slider_count}", file=sys.stderr, flush=True)
    
    # Step 3: Normalize final_vector
    # final_vector = normalize( base_weight_scale * base_vector + Σ(steering_contribution_i) )
    print("📐 Normalizing final vector...", file=sys.stderr, flush=True)
    vector_norm = np.linalg.norm(final_vector)
    if vector_norm > 0:
        final_vector = final_vector / vector_norm
        base_vector_normalized = base_vector / base_vector_norm if base_vector_norm > 0 else base_vector
        vector_change_after_norm = np.linalg.norm(final_vector - base_vector_normalized)
        print(f"✅ Vector normalized (norm was {vector_norm:.4f})", file=sys.stderr, flush=True)
        print(f"📊 Steering impact (after normalization):", file=sys.stderr, flush=True)
        print(f"   Normalized vector change magnitude: {vector_change_after_norm:.4f}", file=sys.stderr, flush=True)
        print(f"   Cosine similarity to base: {float(np.dot(final_vector, base_vector_normalized)):.4f}", file=sys.stderr, flush=True)
    else:
        print(f"⚠️ Warning: Final vector has zero norm, using base vector", file=sys.stderr, flush=True)
        final_vector = base_vector / base_vector_norm if base_vector_norm > 0 else base_vector
    
    # #region agent log
    log_data = {
        "location": "refine_category.py:275", 
        "message": "After steering and normalization", 
        "data": {
            "final_vector_norm": float(np.linalg.norm(final_vector)), 
            "vector_changed": float(np.linalg.norm(final_vector - (base_vector / base_vector_norm if base_vector_norm > 0 else base_vector))),
            "total_steering_magnitude": float(total_steering_magnitude),
            "slider_count": slider_count,
            "steering_weight": "2.5-7.5 (dynamic with extreme boost)"
        }, 
        "timestamp": int(__import__('time').time() * 1000), 
        "sessionId": "debug-session", 
        "runId": "run1", 
        "hypothesisId": "D"
    }
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
    
    # Step 5: Query Pinecone with final_vector (with auto-extreme retry logic)
    print("🔍 Querying Pinecone with refined vector...", file=sys.stderr, flush=True)
    
    # Track previous result ID for auto-extreme logic
    # Use excluded image as previous, but we'll also track the actual top result
    previous_result_id = exclude_image_id  # Use excluded image as previous if provided
    first_query_top_id = None  # Track the first query's top result
    
    # Auto-extreme retry logic: if same image returned, increase steering weight
    max_retries = 4  # Increased from 3 to 4 for more aggressive retries
    retry_multiplier = 2.5  # Increased from 2.0 to 2.5 for faster escalation
    current_steering_multiplier = 1.0

    # Build palette filter from slider tuning meta (applies across all tuning)
    palette_hexes = []
    for slider_key, slider_value in slider_values.items():
        if abs(slider_value) < 0.30:
            continue
        palette_hexes.extend(get_palette_for_direction(slider_key, slider_value, slider_tuning_meta))
    palette_hexes = list({h.upper() for h in palette_hexes if isinstance(h, str)})
    use_palette_filter = len(palette_hexes) > 0
    if use_palette_filter:
        print(f"🎨 Palette filter active with {len(palette_hexes)} hexes", file=sys.stderr, flush=True)
    
    for retry_attempt in range(max_retries + 1):
        try:
            # If retrying, recalculate final_vector with increased steering weight
            if retry_attempt > 0:
                print(f"🔄 Auto-extreme retry {retry_attempt}/{max_retries} (steering multiplier: {current_steering_multiplier:.1f}x)...", file=sys.stderr, flush=True)
                # Recalculate steering with increased weight
                retry_vector = base_vector * base_weight_scale
                for slider_key, slider_value in slider_values.items():
                    if abs(slider_value) < 0.01:
                        continue

                    slider_label_info = slider_labels.get(slider_key, {})
                    left_label = slider_label_info.get('left', 'left')
                    right_label = slider_label_info.get('right', 'right')
                    poles = generate_dynamic_poles(brand_brief, left_label, right_label)
                    pos_vector = model.encode(poles['pos'], convert_to_numpy=True)
                    neg_vector = model.encode(poles['neg'], convert_to_numpy=True)
                    axis_vector = pos_vector - neg_vector

                    # Apply increased steering weight (same formula as initial, but multiplied)
                    base_weight = 5.0 * current_steering_multiplier  # Increased base weight
                    abs_slider = abs(slider_value)
                    extreme_boost = 1.0 + (abs_slider ** 2) * 4.0  # Same boost formula
                    steering_weight = base_weight * extreme_boost
                    if abs_slider > 0.8:  # Same threshold
                        extreme_multiplier = 2.0 + (abs_slider - 0.8) * 5.0  # Same multiplier formula
                        steering_weight *= extreme_multiplier
                    if abs_slider < 0.30:
                        steering_weight *= (abs_slider / 0.30)

                    neg_keywords = get_opposite_keywords(slider_key, slider_value, slider_tuning_meta)
                    neg_boost_vector = None
                    neg_boost_weight = 0.0
                    if neg_keywords:
                        neg_boost_weight = 0.6 * abs_slider
                        neg_boost_vector = model.encode(" ".join(neg_keywords), convert_to_numpy=True)

                    steering_contribution = axis_vector * slider_value * steering_weight
                    if neg_boost_vector is not None and neg_boost_weight > 0:
                        steering_contribution = steering_contribution - (neg_boost_vector * neg_boost_weight)

                    retry_vector = retry_vector + steering_contribution

                # Normalize retry vector
                retry_norm = np.linalg.norm(retry_vector)
                if retry_norm > 0:
                    retry_vector = retry_vector / retry_norm
                query_vector = retry_vector
            else:
                query_vector = final_vector

            # Increase top_k significantly to ensure we have enough results after filtering and exclusion
            # With 2,700 images total, we need to query more to get enough in each category
            top_k = 500  # Increased from 200 to 500 to get more results
            query_kwargs = {
                "vector": query_vector.tolist(),
                "top_k": top_k,
                "include_metadata": True
            }
            if use_palette_filter:
                query_kwargs["filter"] = {
                    "hex_codes": {"$in": palette_hexes}
                }

            results = index.query(**query_kwargs)

            print(f"✅ Query complete: {len(results.matches)} results found (queried top_k={top_k})", file=sys.stderr, flush=True)

            # Filter results by category namespace if specified (before auto-extreme check)
            allowed_categories = CATEGORY_NAMESPACE_MAP.get(category_type, [])
            if allowed_categories:
                filtered_matches = []
                for match in results.matches:
                    cat = match.metadata.get('category', '') if match.metadata else ''
                    if any(allowed in cat or cat in allowed for allowed in allowed_categories):
                        filtered_matches.append(match)
                results.matches = filtered_matches
                print(f"📊 Filtered to {len(filtered_matches)} results in category: {category_type}", file=sys.stderr, flush=True)

                if len(filtered_matches) == 0 and retry_attempt < max_retries:
                    print(f"⚠️ No results after filtering, increasing steering weight...", file=sys.stderr, flush=True)
                    current_steering_multiplier *= retry_multiplier
                    continue

            # Remove locked image IDs from candidate results
            if locked_image_ids:
                before_lock_filter = len(results.matches)
                results.matches = [m for m in results.matches if m.id not in locked_image_ids]
                if before_lock_filter != len(results.matches):
                    print(f"🔒 Filtered out {before_lock_filter - len(results.matches)} locked images", file=sys.stderr, flush=True)

            # If palette filter caused empty results, retry once without it
            if use_palette_filter and len(results.matches) == 0 and retry_attempt < max_retries:
                print("⚠️ Palette filter yielded no results; disabling palette filter and retrying...", file=sys.stderr, flush=True)
                use_palette_filter = False
                continue

            # Track first query's top result for comparison
            if retry_attempt == 0 and results.matches:
                first_query_top_id = results.matches[0].id
                print(f"📌 First query top result ID: {first_query_top_id}", file=sys.stderr, flush=True)

            # Check if we got a different image (auto-extreme check) - after filtering
            if results.matches:
                current_top_id = results.matches[0].id

                # Check against previous result (exclude_image_id) if provided
                # Also check against first query result to ensure we're making progress
                comparison_id = previous_result_id if previous_result_id else first_query_top_id

                if comparison_id and current_top_id == comparison_id:
                    if retry_attempt < max_retries:
                        print(f"⚠️ Same image returned (ID: {current_top_id} vs {comparison_id}), increasing steering weight...", file=sys.stderr, flush=True)
                        current_steering_multiplier *= retry_multiplier
                        print(f"🔄 New steering multiplier: {current_steering_multiplier:.1f}x", file=sys.stderr, flush=True)
                        continue  # Retry with increased weight
                    print(f"⚠️ Same image returned after {max_retries} retries. Using result anyway.", file=sys.stderr, flush=True)
                else:
                    print(f"✅ Different image returned (ID: {current_top_id} vs {comparison_id})", file=sys.stderr, flush=True)
                    if retry_attempt > 0:
                        print(f"✅ Auto-extreme succeeded after {retry_attempt} retry(ies)", file=sys.stderr, flush=True)

            # Break out of retry loop if we got results
            break

        except Exception as e:
            if retry_attempt < max_retries:
                print(f"⚠️ Query failed, retrying with increased steering: {e}", file=sys.stderr, flush=True)
                current_steering_multiplier *= retry_multiplier
                continue
            raise
    
    try:
        
        # Debug: Log top result similarity scores to measure steering impact
        if results.matches and len(results.matches) > 0:
            top_scores = [match.score for match in results.matches[:5]]
            print(f"📊 Top 5 similarity scores: {[f'{s:.4f}' for s in top_scores]}", file=sys.stderr, flush=True)
            print(f"📊 Score range: {top_scores[0]:.4f} (top) to {top_scores[-1]:.4f} (5th)", file=sys.stderr, flush=True)
            if slider_count > 0:
                print(f"📊 Steering active: {slider_count} slider(s) with total magnitude {total_steering_magnitude:.4f}", file=sys.stderr, flush=True)
            else:
                print(f"📊 No steering applied (all sliders neutral)", file=sys.stderr, flush=True)
        
        # Category filtering already done in retry loop, but check if we have results
        if len(results.matches) == 0:
            allowed_categories = CATEGORY_NAMESPACE_MAP.get(category_type, [])
            print(f"⚠️ WARNING: No results in category {category_type} after filtering!", file=sys.stderr, flush=True)
            print(f"⚠️ Allowed categories: {allowed_categories}", file=sys.stderr, flush=True)
        
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
        top_scores = [float(r.score) for r in results.matches[:5]] if results.matches else []
        log_data = {
            "location": "refine_category.py:410", 
            "message": "Query results", 
            "data": {
                "result_count": len(results.matches), 
                "top_5_ids": top_result_ids, 
                "top_5_scores": top_scores,
                "top_score": float(results.matches[0].score) if results.matches else None,
                "steering_applied": slider_count > 0,
                "slider_count": slider_count,
                "total_steering_magnitude": float(total_steering_magnitude),
                "steering_weight": "2.5-7.5 (dynamic with extreme boost)"
            }, 
            "timestamp": int(__import__('time').time() * 1000), 
            "sessionId": "debug-session", 
            "runId": "run1", 
            "hypothesisId": "D"
        }
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

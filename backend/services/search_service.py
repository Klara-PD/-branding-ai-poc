import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from .model_service import get_model, get_index


CATEGORY_NAMESPACE_MAP = {
    "colors": ["brand_color_mood"],
    "typography": ["typography"],
    "logo": ["logo_geometry"],
    "illustration": ["illustration"],
    "photo_model": ["photography/models", "models"],
    "photo_product": ["photography/products", "products"],
    "photo_environment": ["photography/environments", "environments"],
}


def generate_dynamic_poles(brand_brief: str, left_label: str, right_label: str) -> Dict[str, str]:
    pos_pole = f"{brand_brief} more {right_label.lower()}"
    neg_pole = f"{brand_brief} more {left_label.lower()}"
    return {"pos": pos_pole, "neg": neg_pole}


def compute_tuning_intensity(slider_values: Dict[str, float]) -> float:
    if not slider_values:
        return 0.0
    abs_values = [abs(v) for v in slider_values.values()]
    return float(sum(abs_values) / max(len(abs_values), 1))


def compute_brief_weight(tuning_intensity: float) -> float:
    # Exponential decay from 1.0 down to 0.3 as intensity increases
    return max(0.3, float(np.exp(-1.2 * tuning_intensity)))


def get_palette_for_direction(slider_key: str, slider_value: float, tuning_meta: Dict[str, Any]) -> List[str]:
    meta = tuning_meta.get(slider_key, {}) if isinstance(tuning_meta, dict) else {}
    if slider_value > 0:
        return meta.get("rightPalettes", []) or []
    if slider_value < 0:
        return meta.get("leftPalettes", []) or []
    return []


def get_metadata_filters(slider_key: str, slider_value: float, tuning_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    meta = tuning_meta.get(slider_key, {}) if isinstance(tuning_meta, dict) else {}
    raw_filters = []
    if slider_value > 0:
        raw_filters = meta.get("rightFilters", []) or []
    elif slider_value < 0:
        raw_filters = meta.get("leftFilters", []) or []

    compiled_filters: List[Dict[str, Any]] = []
    for filt in raw_filters:
        if not isinstance(filt, dict):
            continue
        field = filt.get("field")
        values = filt.get("values")
        if not field or not values:
            continue
        if not isinstance(values, list):
            values = [values]
        compiled_filters.append({field: {"$in": values}})
    return compiled_filters


def resolve_image_path(current_image_path: Optional[str], project_root: Path) -> Optional[Path]:
    if not current_image_path:
        return None
    if current_image_path.startswith("/api/images/"):
        relative_path = current_image_path.replace("/api/images/", "")
        return project_root / relative_path
    if current_image_path.startswith("data/"):
        return project_root / current_image_path
    if current_image_path.startswith("/"):
        return Path(current_image_path)
    return project_root / current_image_path


def format_results(matches) -> Dict[str, Any]:
    return {
        "results": [
            {"id": match.id, "score": match.score, "metadata": match.metadata or {}}
            for match in matches
        ],
        "count": len(matches),
    }


def search_mood_boards(
    brand_brief: str, 
    index_name: Optional[str] = None, 
    top_k: int = 200,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search mood boards. If category is specified, filter to that category only.
    Otherwise, query all categories with balanced distribution.
    """
    model = get_model()
    index = get_index(index_name)

    query_vector = model.encode(brand_brief, convert_to_numpy=True).tolist()
    
    # If specific category requested, query just that category
    if category:
        print(f"🔍 Searching category: {category} with query: {brand_brief[:60]}...")
        try:
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter={"category": {"$eq": category}}
            )
            print(f"✅ Found {len(results.matches)} results for {category}")
            return format_results(results.matches)
        except Exception as e:
            print(f"❌ Error querying category {category}: {e}")
            return {"results": [], "count": 0, "error": str(e)}
    
    # No category specified - query all categories with balanced distribution
    category_targets = {
        "brand_color_mood": 30,
        "typography": 25,
        "logo_geometry": 30,
        "illustration": 25,
        "photography/models": 30,
        "photography/products": 30,
        "photography/environments": 30,
    }
    
    all_results = []
    
    for cat, target_count in category_targets.items():
        try:
            cat_results = index.query(
                vector=query_vector,
                top_k=target_count,
                include_metadata=True,
                filter={"category": {"$eq": cat}}
            )
            all_results.extend(cat_results.matches)
        except Exception as e:
            print(f"Warning: Failed to query category {cat}: {e}")
            continue
    
    # Sort by score and remove duplicates
    seen_ids = set()
    unique_results = []
    for match in sorted(all_results, key=lambda x: x.score, reverse=True):
        if match.id not in seen_ids:
            seen_ids.add(match.id)
            unique_results.append(match)
    
    return format_results(unique_results[:top_k])


def refine_category(
    brand_brief: str,
    category_type: str,
    slider_values: Dict[str, float],
    slider_labels: Dict[str, Dict[str, str]],
    slider_tuning_meta: Dict[str, Any],
    locked_image_ids: List[str],
    current_image_path: Optional[str],
    current_image_id: Optional[str],
    project_root: Path,
    index_name: Optional[str] = None,
) -> Dict[str, Any]:
    model = get_model()
    index = get_index(index_name)

    # Base vector from image (if provided) else from brief
    base_vector = None
    resolved_path = resolve_image_path(current_image_path, project_root)
    if resolved_path and resolved_path.exists():
        try:
            img = Image.open(resolved_path)
            base_vector = model.encode(img, convert_to_numpy=True)
        except Exception:
            base_vector = None

    if base_vector is None:
        base_vector = model.encode(brand_brief, convert_to_numpy=True)

    base_vector_norm = np.linalg.norm(base_vector)
    tuning_intensity = compute_tuning_intensity(slider_values)
    brief_weight = compute_brief_weight(tuning_intensity)
    final_vector = base_vector * brief_weight

    total_steering_magnitude = 0.0
    slider_count = 0
    per_slider_weights = {}

    for slider_key, slider_value in slider_values.items():
        if abs(slider_value) < 0.01:
            continue

        slider_label_info = slider_labels.get(slider_key, {})
        left_label = slider_label_info.get("left", "left")
        right_label = slider_label_info.get("right", "right")
        poles = generate_dynamic_poles(brand_brief, left_label, right_label)
        pos_vector = model.encode(poles["pos"], convert_to_numpy=True)
        neg_vector = model.encode(poles["neg"], convert_to_numpy=True)
        # Contrast enhancement: push away from negative pole
        axis_vector = pos_vector - (0.5 * neg_vector)

        base_weight = 5.0
        abs_slider = abs(slider_value)
        extreme_boost = 1.0 + (abs_slider ** 2) * 4.0
        steering_weight = base_weight * extreme_boost
        if abs_slider > 0.8:
            extreme_multiplier = 2.0 + (abs_slider - 0.8) * 5.0
            steering_weight *= extreme_multiplier
        if abs_slider < 0.30:
            steering_weight *= (abs_slider / 0.30)

        steering_contribution = axis_vector * slider_value * steering_weight
        per_slider_weights[slider_key] = {
            "slider_value": float(slider_value),
            "steering_weight": float(steering_weight),
        }

        steering_magnitude = np.linalg.norm(steering_contribution)
        total_steering_magnitude += steering_magnitude
        slider_count += 1
        final_vector = final_vector + steering_contribution

    # Normalize final_vector
    vector_norm = np.linalg.norm(final_vector)
    if vector_norm > 0:
        final_vector = final_vector / vector_norm

    # Build palette filter from tuning meta (all tuning)
    palette_hexes = []
    for slider_key, slider_value in slider_values.items():
        if abs(slider_value) < 0.30:
            continue
        palette_hexes.extend(get_palette_for_direction(slider_key, slider_value, slider_tuning_meta))
    palette_hexes = list({h.upper() for h in palette_hexes if isinstance(h, str)})
    use_palette_filter = len(palette_hexes) > 0

    # Build metadata filters for sliders > 70%
    metadata_filters = []
    for slider_key, slider_value in slider_values.items():
        if abs(slider_value) < 0.70:
            continue
        metadata_filters.extend(get_metadata_filters(slider_key, slider_value, slider_tuning_meta))
    use_metadata_filter = len(metadata_filters) > 0

    # Auto-extreme retry logic
    previous_result_id = current_image_id
    first_query_top_id = None
    max_retries = 4
    retry_multiplier = 2.5
    current_steering_multiplier = 1.0

    results = None
    for retry_attempt in range(max_retries + 1):
        try:
            if retry_attempt > 0:
                retry_vector = base_vector * brief_weight
                for slider_key, slider_value in slider_values.items():
                    if abs(slider_value) < 0.01:
                        continue

                    slider_label_info = slider_labels.get(slider_key, {})
                    left_label = slider_label_info.get("left", "left")
                    right_label = slider_label_info.get("right", "right")
                    poles = generate_dynamic_poles(brand_brief, left_label, right_label)
                    pos_vector = model.encode(poles["pos"], convert_to_numpy=True)
                    neg_vector = model.encode(poles["neg"], convert_to_numpy=True)
                    axis_vector = pos_vector - (0.5 * neg_vector)

                    base_weight = 5.0 * current_steering_multiplier
                    abs_slider = abs(slider_value)
                    extreme_boost = 1.0 + (abs_slider ** 2) * 4.0
                    steering_weight = base_weight * extreme_boost
                    if abs_slider > 0.8:
                        extreme_multiplier = 2.0 + (abs_slider - 0.8) * 5.0
                        steering_weight *= extreme_multiplier
                    if abs_slider < 0.30:
                        steering_weight *= (abs_slider / 0.30)

                    steering_contribution = axis_vector * slider_value * steering_weight

                    retry_vector = retry_vector + steering_contribution

                retry_norm = np.linalg.norm(retry_vector)
                if retry_norm > 0:
                    retry_vector = retry_vector / retry_norm
                query_vector = retry_vector
            else:
                query_vector = final_vector

            allowed_categories = CATEGORY_NAMESPACE_MAP.get(category_type, [])

            query_kwargs = {
                "vector": query_vector.tolist(),
                "top_k": 500,
                "include_metadata": True,
            }
            # Metadata + palette filters (boost when sliders > 70%)
            filter_obj = None
            if use_palette_filter:
                filter_obj = {"hex_codes": {"$in": palette_hexes}}
            if use_metadata_filter:
                meta_or = {"$or": metadata_filters} if len(metadata_filters) > 1 else metadata_filters[0]
                filter_obj = {"$and": [filter_obj, meta_or]} if filter_obj else meta_or
            if allowed_categories:
                category_filter = {"category": {"$in": allowed_categories}}
                filter_obj = {"$and": [filter_obj, category_filter]} if filter_obj else category_filter
            if filter_obj:
                query_kwargs["filter"] = filter_obj

            results = index.query(**query_kwargs)

            # If filters are too strict, relax them before category filtering
            if len(results.matches) == 0 and retry_attempt < max_retries:
                if use_metadata_filter:
                    use_metadata_filter = False
                    continue
                if use_palette_filter:
                    use_palette_filter = False
                    continue

            # Category filtering (guard for mixed metadata)
            if allowed_categories:
                filtered_matches = []
                for match in results.matches:
                    cat = match.metadata.get("category", "") if match.metadata else ""
                    if any(allowed in cat or cat in allowed for allowed in allowed_categories):
                        filtered_matches.append(match)
                results.matches = filtered_matches

                if len(filtered_matches) == 0 and retry_attempt < max_retries:
                    if use_metadata_filter or use_palette_filter:
                        use_metadata_filter = False
                        use_palette_filter = False
                        continue
                    current_steering_multiplier *= retry_multiplier
                    continue

            # Remove locked IDs
            if locked_image_ids:
                results.matches = [m for m in results.matches if m.id not in locked_image_ids]

            if use_metadata_filter and len(results.matches) == 0 and retry_attempt < max_retries:
                use_metadata_filter = False
                continue
            if use_palette_filter and len(results.matches) == 0 and retry_attempt < max_retries:
                use_palette_filter = False
                continue

            if retry_attempt == 0 and results.matches:
                first_query_top_id = results.matches[0].id

            if results.matches:
                current_top_id = results.matches[0].id
                comparison_id = previous_result_id if previous_result_id else first_query_top_id
                if comparison_id and current_top_id == comparison_id:
                    if retry_attempt < max_retries:
                        current_steering_multiplier *= retry_multiplier
                        continue

            break
        except Exception:
            if retry_attempt < max_retries:
                current_steering_multiplier *= retry_multiplier
                continue
            raise

    formatted = format_results(results.matches if results else [])
    formatted["debug"] = {
        "final_vector_formula": "normalize( brief_weight * base_vector + Σ( axis_vector_i * slider_value_i * steering_weight_i ) )",
        "brief_weight": round(brief_weight, 3),
        "tuning_intensity": round(tuning_intensity, 3),
        "palette_filter_active": use_palette_filter,
        "palette_hex_count": len(palette_hexes),
        "metadata_filter_active": use_metadata_filter,
        "category_filter": CATEGORY_NAMESPACE_MAP.get(category_type, []),
        "slider_count": slider_count,
        "total_steering_magnitude": float(total_steering_magnitude),
        "per_slider_weights": per_slider_weights,
    }
    return formatted

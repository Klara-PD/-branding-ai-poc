import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def _cache_dir(project_root: Path) -> Path:
    return project_root / "backend" / "cache"


def _embeddings_path(project_root: Path) -> Path:
    return _cache_dir(project_root) / "embeddings.npy"


def _metadata_path(project_root: Path) -> Path:
    return _cache_dir(project_root) / "metadata.json"


def _ids_path(project_root: Path) -> Path:
    return _cache_dir(project_root) / "ids.json"


def _hash_file(path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _infer_category(relative_path: Path) -> Optional[str]:
    parts = list(relative_path.parts)
    if not parts:
        return None
    # Expect "data/<category>/..."
    if parts[0] != "data":
        return None
    if len(parts) < 2:
        return None
    category_root = parts[1]
    if category_root in {"brand_color_mood", "typography", "logo_geometry", "illustration"}:
        return category_root
    if category_root == "photography" and len(parts) >= 3:
        return f"photography/{parts[2]}"
    return category_root


def _extract_dominant_colors(image_path: Path, num_colors: int = 5) -> List[str]:
    try:
        img = Image.open(image_path)
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        img = img.convert("RGB")
        colors = img.getcolors(150 * 150)
        if not colors:
            return []
        colors_sorted = sorted(colors, key=lambda x: x[0], reverse=True)[:num_colors]
        hex_colors = ["#%02x%02x%02x" % color for _, color in colors_sorted]
        return [hex_color.upper() for hex_color in hex_colors]
    except Exception:
        return []


def load_cache(project_root: Path) -> Optional[Tuple[np.ndarray, List[str], List[Dict[str, Any]]]]:
    embeddings_file = _embeddings_path(project_root)
    metadata_file = _metadata_path(project_root)
    ids_file = _ids_path(project_root)
    if not (embeddings_file.exists() and metadata_file.exists() and ids_file.exists()):
        return None
    embeddings = np.load(embeddings_file)
    with open(metadata_file, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    with open(ids_file, "r", encoding="utf-8") as handle:
        ids = json.load(handle)
    return embeddings, ids, metadata


def build_cache(project_root: Path, model) -> Tuple[np.ndarray, List[str], List[Dict[str, Any]]]:
    data_root = project_root / "data"
    if not data_root.exists():
        raise FileNotFoundError(f"Data directory not found at {data_root}")

    cache_dir = _cache_dir(project_root)
    cache_dir.mkdir(parents=True, exist_ok=True)

    embeddings: List[np.ndarray] = []
    ids: List[str] = []
    metadata: List[Dict[str, Any]] = []

    for image_path in data_root.rglob("*"):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        relative_path = image_path.relative_to(project_root)
        category = _infer_category(relative_path)
        if not category:
            continue
        image_id = _hash_file(image_path)
        try:
            img = Image.open(image_path)
            vector = model.encode(img, convert_to_numpy=True)
        except Exception:
            continue
        vector_norm = np.linalg.norm(vector)
        if vector_norm > 0:
            vector = vector / vector_norm

        meta: Dict[str, Any] = {
            "file_path": str(relative_path),
            "category": category,
            "filename": image_path.name,
            "md5_hash": image_id,
        }
        if category == "brand_color_mood":
            hex_codes = _extract_dominant_colors(image_path)
            if hex_codes:
                meta["hex_codes"] = hex_codes

        embeddings.append(vector.astype(np.float32))
        ids.append(image_id)
        metadata.append(meta)

    if not embeddings:
        raise RuntimeError("No embeddings generated; check data directory.")

    embedding_matrix = np.vstack(embeddings)
    np.save(_embeddings_path(project_root), embedding_matrix)
    with open(_metadata_path(project_root), "w", encoding="utf-8") as handle:
        json.dump(metadata, handle)
    with open(_ids_path(project_root), "w", encoding="utf-8") as handle:
        json.dump(ids, handle)

    return embedding_matrix, ids, metadata


def update_cache(project_root: Path, model) -> Tuple[np.ndarray, List[str], List[Dict[str, Any]], int]:
    cached = load_cache(project_root)
    if cached is None:
        embeddings, ids, metadata = build_cache(project_root, model)
        return embeddings, ids, metadata, len(ids)

    embeddings, ids, metadata = cached
    existing_ids = set(ids)
    data_root = project_root / "data"
    if not data_root.exists():
        return embeddings, ids, metadata, 0

    new_embeddings: List[np.ndarray] = []
    new_ids: List[str] = []
    new_metadata: List[Dict[str, Any]] = []

    for image_path in data_root.rglob("*"):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        image_id = _hash_file(image_path)
        if image_id in existing_ids:
            continue
        relative_path = image_path.relative_to(project_root)
        category = _infer_category(relative_path)
        if not category:
            continue
        try:
            img = Image.open(image_path)
            vector = model.encode(img, convert_to_numpy=True)
        except Exception:
            continue
        vector_norm = np.linalg.norm(vector)
        if vector_norm > 0:
            vector = vector / vector_norm

        meta: Dict[str, Any] = {
            "file_path": str(relative_path),
            "category": category,
            "filename": image_path.name,
            "md5_hash": image_id,
        }
        if category == "brand_color_mood":
            hex_codes = _extract_dominant_colors(image_path)
            if hex_codes:
                meta["hex_codes"] = hex_codes

        new_embeddings.append(vector.astype(np.float32))
        new_ids.append(image_id)
        new_metadata.append(meta)

    if new_embeddings:
        updated_embeddings = np.vstack([embeddings, np.vstack(new_embeddings)])
        updated_ids = ids + new_ids
        updated_metadata = metadata + new_metadata
        np.save(_embeddings_path(project_root), updated_embeddings)
        with open(_metadata_path(project_root), "w", encoding="utf-8") as handle:
            json.dump(updated_metadata, handle)
        with open(_ids_path(project_root), "w", encoding="utf-8") as handle:
            json.dump(updated_ids, handle)
        return updated_embeddings, updated_ids, updated_metadata, len(new_ids)

    return embeddings, ids, metadata, 0


def get_cache(project_root: Path, model) -> Tuple[np.ndarray, List[str], List[Dict[str, Any]]]:
    cached = load_cache(project_root)
    if cached is not None:
        return cached
    return build_cache(project_root, model)


def search_cache(
    query_vector: np.ndarray,
    embeddings: np.ndarray,
    metadata: List[Dict[str, Any]],
    ids: List[str],
    top_k: int = 5000,
) -> List[Dict[str, Any]]:
    if embeddings.size == 0:
        return []
    vector = query_vector.astype(np.float32)
    vector_norm = np.linalg.norm(vector)
    if vector_norm > 0:
        vector = vector / vector_norm
    scores = embeddings @ vector
    top_k = min(top_k, embeddings.shape[0])
    idx = np.argpartition(-scores, top_k - 1)[:top_k]
    idx = idx[np.argsort(-scores[idx])]
    results = []
    for i in idx:
        results.append(
            {
                "id": ids[i],
                "score": float(scores[i]),
                "metadata": metadata[i] or {},
            }
        )
    return results

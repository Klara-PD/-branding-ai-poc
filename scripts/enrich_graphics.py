#!/usr/bin/env python3
"""
Graphics Enrichment Script - AI Metadata Generation for Colors, Logos, and Illustrations

Uses OpenAI's gpt-4o-mini Vision to generate rich, category-specific metadata
for graphics assets. Handles three categories with specialized system prompts:
- Colors: Merge mode (appends semantic_vibe to existing color_analysis.json)
- Logos: Standard mode (creates/updates logo_metadata.json)
- Illustrations: Standard mode (creates/updates illustration_metadata.json)
"""

import os
import sys
import json
import base64
import time
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

# Asset configuration with system prompts
ASSET_CONFIG = [
    # {
    #     "folder": "brand_color_mood",
    #     "json_path": "data/color_analysis.json",
    #     "mode": "merge",  # Special logic: Update existing key
    #     "system_prompt": """You are a Color Theorist. Analyze ONLY the color palette.
    # Describe:
    # - The dominant colors (specific names like ochre, teal, charcoal).
    # - The harmony (monochromatic, complementary, triadic).
    # - The emotional temperature (warm, cool, neutral).
    # - The energy (calm, vibrant, aggressive, corporate).
    # CONSTRAINT: Do NOT describe objects or people. Focus ONLY on the color psychology."""
    # },
    {
        "folder": "logo_geometry",
        "json_path": "data/logo_metadata.json",
        "mode": "standard",
        "system_prompt": """You are a specialist assistant that helps users write high-quality metadata for logos.
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
    },
    {
        "folder": "illustration",
        "json_path": "data/illustration_metadata.json",
        "mode": "standard",
        "system_prompt": """You are a specialist assistant that helps users write high-quality metadata for illustrations.
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
    },
    {
        "folder": "photography/environments",
        "json_path": "data/photography_metadata.json",
        "mode": "standard",
        "system_prompt": """You are a specialist assistant that helps users write high-quality, technical metadata for photography. 

Analyze the image and return a JSON object with exactly twelve fields.

### CRITICAL CONSTRAINTS (DO NOT IGNORE):

1. **NO Specific Colors:** Never mention actual color names. Describe the palette's nature (e.g., 'high-chroma', 'desaturated', 'monochromatic', 'warm-biased').

2. **NO Specific Content Details:** Never mention subjects (e.g., 'person', 'beach', 'architecture'). Describe ONLY the photographic execution and visual characteristics.

3. **NO Scene Description:** Focus ONLY on HOW it was captured (lens choice, lighting, depth of field, grain).

4. **NO Text Content:** If text appears, describe only its typographic integration or blur level.

5. **NO Fluff:** Provide only technical and atmospheric analysis.

### FIELD DEFINITIONS:

- **description:** Technical analysis of the photographic execution and post-processing (1-2 sentences combining lighting, composition, and visual characteristics).

- **product_type:** Type of products/objects visible (e.g., 'cylindrical beverage containers', 'rectangular packaging', 'organic produce items').

- **environment_elements:** List of environmental elements present (e.g., 'sliced organic fruit, small circular condiment vessels, layered fast-food items, and a vertically-slatted furniture element').

- **surface_and_texture:** Description of surfaces and textures visible (e.g., 'high-vibrance smooth tabletop adjacent to a textured vertical wall').

- **lighting_setup:** Description of the lighting arrangement (e.g., 'harsh, direct overhead light creating high-luminance highlights', 'soft, diffused natural lighting').

- **shadow_character:** Description of shadow qualities (e.g., 'short, hard-edged directional shadows with high density', 'soft, diffused shadows with low contrast').

- **materiality:** Description of materials visible (e.g., 'metallic aluminum, organic pulpy fibers, and matte paper-based elements').

- **shot_angle:** Camera angle perspective (e.g., 'high-angle perspective', 'eye-level', 'low-angle', 'overhead').

- **visual_era:** Visual period/style (e.g., 'contemporary-pop commercial', 'vintage-retro', 'minimalist-modern').

- **spatial_arrangement:** How elements are arranged in space (e.g., 'organized dynamic clutter with overlapping focal points', 'minimalist centered composition').

- **visual_style_tags:** Array of 5 hyphenated technical tags (e.g., ["hard-light", "commercial-maximalism", "material-contrast", "high-chroma-palette", "top-down-framing"]).

- **mood_tone:** The emotional resonance (e.g., 'vibrant, social, and high-energy', 'calm and minimal').

### OUTPUT FORMAT (JSON ONLY):

{
  "description": "Technical analysis of the photographic execution and post-processing.",
  "product_type": "Type of products/objects visible",
  "environment_elements": "List of environmental elements present",
  "surface_and_texture": "Description of surfaces and textures",
  "lighting_setup": "Description of the lighting arrangement",
  "shadow_character": "Description of shadow qualities",
  "materiality": "Description of materials visible",
  "shot_angle": "Camera angle perspective",
  "visual_era": "Visual period/style",
  "spatial_arrangement": "How elements are arranged in space",
  "visual_style_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "mood_tone": "The emotional resonance"
}"""
    },
    {
        "folder": "photography/models",
        "json_path": "data/photography_metadata.json",
        "mode": "standard",
        "system_prompt": """You are a specialist assistant that helps users write high-quality, high-dimensional metadata for human subjects and characters. 
Analyze the individual(s) and return a JSON object with exactly twelve fields.

### CRITICAL CONSTRAINTS (DO NOT IGNORE):
1. **NO Clothing or Accessories:** Do not mention fabrics, colors, or items of dress.
2. **NO Action or Pose:** Do not describe what the subject is doing.
3. **NO Scene/Background:** Focus entirely on the person as an isolated entity.
4. **NO Specific Colors:** Describe tonal nature (e.g., 'warm-undertone', 'high-contrast features') without naming color labels.
5. **Focus ONLY on the 'Who':** Describe physical architecture, genetic heritage, and character archetype.

### FIELD DEFINITIONS:
- **description:** Detailed technical summary combining physical architecture, bone structure, and overall presence. MUST be comprehensive and specific, combining multiple physical characteristics in a single, detailed sentence (minimum 15-20 words). Examples: 'Androgynous figure with sharp, chiseled bone structure and an intense, stoic gaze' or 'Strong, grounded facial architecture with high surface clarity and classical proportions'. Always include: physical form type + bone structure details + gaze/presence. Be specific and detailed, not generic.
- **demographics:** Estimated age range and perceived ethnic heritage/ancestry (e.g., 'Adult (20s-30s), Northern European heritage').
- **gender:** Perceived gender presentation (e.g., 'masculine', 'feminine', 'androgynous', 'gender-fluid', 'non-binary').
- **facial_architecture:** Detailed bone structure and feature definitions with specific terminology. Must include multiple specific features (e.g., 'High, prominent cheekbones, sharp jawline, and deep-set piercing eyes').
- **skin_and_body_detail:** Detailed surface quality and physique type with specific descriptors. Must include both texture and physique details (e.g., 'Porcelain-smooth texture with an elongated, slender, and statuesque physique').
- **hair_character:** Detailed texture, growth, and styling nature with specific descriptors (e.g., 'Fine, straight texture, jaw-length with a sharp, blunt-cut character').
- **gaze_direction:** Psychological connection with specific descriptors (e.g., 'Direct-engagement, confrontational', 'Averted, introspective').
- **facial_symmetry:** Degree of regularity with specific terminology (e.g., 'High-symmetry with sharp-angularity', 'Asymmetrical-unique').
- **sub_culture_alignment:** The aesthetic 'tribe' or vibe (e.g., 'Avant-garde / gender-fluid', 'Minimalist-chic', 'Street-raw', 'Heritage-classic').
- **character_energy:** The internal 'vibe' with specific descriptors (e.g., 'Stoic and authoritative', 'Vulnerable and contemplative').
- **persona_style:** The innate archetype (e.g., 'The Rebel', 'The Ingenue', 'The Sage', 'The Titan').
- **visual_identity_tags:** Five specific hyphenated keywords focusing on physical/character traits (e.g., ["androgynous", "sharp-jawline", "statuesque", "stoic-gaze", "avant-garde-features"]).

### EXAMPLE OUTPUTS (for reference):
Example 1:
{
  "description": "Androgynous figure with sharp, chiseled bone structure and an intense, stoic gaze.",
  "demographics": "Adult (20s-30s), Northern European heritage.",
  "gender": "androgynous",
  "facial_architecture": "High, prominent cheekbones, sharp jawline, and deep-set piercing eyes.",
  "skin_and_body_detail": "Porcelain-smooth texture with an elongated, slender, and statuesque physique.",
  "hair_character": "Fine, straight texture, jaw-length with a sharp, blunt-cut character.",
  "gaze_direction": "Direct-engagement, confrontational.",
  "facial_symmetry": "High-symmetry with sharp-angularity.",
  "sub_culture_alignment": "Avant-garde / gender-fluid.",
  "character_energy": "Stoic and authoritative.",
  "persona_style": "The Rebel.",
  "visual_identity_tags": ["androgynous", "sharp-jawline", "statuesque", "stoic-gaze", "avant-garde-features"]
}

Example 2:
{
  "description": "Strong, grounded facial architecture with high surface clarity and classical proportions.",
  "demographics": "Adult (late 20s), African heritage.",
  "gender": "masculine",
  "facial_architecture": "Square, defined mandible with a broad nasal structure and full, symmetrical features.",
  "skin_and_body_detail": "Deep-toned, porcelain-smooth skin with a healthy, natural sheen.",
  "hair_character": "Short-cropped, high-density texture with a precise, linear hairline.",
  "gaze_direction": "Direct-engagement, intense and searching.",
  "facial_symmetry": "Near-perfect classical symmetry.",
  "sub_culture_alignment": "Heritage-classic / art-studio.",
  "character_energy": "Authoritative and present.",
  "persona_style": "The Sage.",
  "visual_identity_tags": ["direct-gaze", "classical-symmetry", "square-jawline", "deep-toned-skin", "authoritative-presence"]
}

### OUTPUT FORMAT (JSON ONLY):
{
  "description": "Detailed analysis combining physical architecture, bone structure, and overall presence.",
  "demographics": "Age range and heritage",
  "gender": "Gender presentation",
  "facial_architecture": "Detailed bone structure with specific terminology",
  "skin_and_body_detail": "Detailed texture and physique with specific descriptors",
  "hair_character": "Detailed hair nature",
  "gaze_direction": "Gaze type with specific descriptors",
  "facial_symmetry": "Symmetry description with specific terminology",
  "sub_culture_alignment": "Aesthetic tribe/sub-culture",
  "character_energy": "Internal energy with specific descriptors",
  "persona_style": "Archetype",
  "visual_identity_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}"""
    },
    {
        "folder": "typography",
        "json_path": "data/typography_metadata.json",
        "mode": "standard",
        "system_prompt": """You are a high-level Typographic System Architect. Your goal is to audit the entire typographic ecosystem within an image. 
Analyze the image as a structural DNA map for a vector-native AI application.

### STRATEGIC CONSTRAINTS (DO NOT IGNORE):
1. **Inventory First:** You MUST first define the total number of unique typefaces identified.
2. **Per-Face Weight Analysis:** For each identified typeface, you MUST specify the number of distinct weights (e.g., Bold, Regular, Light) and styles observed.
3. **Anatomy Before Labeling:** Describe the physical architecture (terminals, axis, x-height, contrast) BEFORE suggesting font matches.
4. **NO Specific Colors:** Describe the palette's nature (e.g., 'tonal-gradient', 'monochromatic') without naming color labels.
5. **Visual Treatments Only:** Focus on technical effects like shadows, bevels, or textures (e.g., 'extruded-3D', 'offset drop-shadow').
6. **NO Text Content:** Focus only on form; never quote the words.
7. **CRITICAL - Role Field:** The "role" field MUST be a SINGLE value only. Choose ONE: "heading", "accent", "body", or "brand-mark". Do NOT use multiple values separated by "|".
8. **CRITICAL - Terminal Style:** The "terminal_style" field MUST use SPECIFIC descriptive phrases, not generic single words. Examples: "rounded-pill", "razor-sharp serif", "beveled-cut", "flat-horizontal cuts", "rounded brush-tip exits". NEVER use just "rounded", "sharp", or "serif" alone.
9. **CRITICAL - Overall Layout Strategy:** Must be a detailed, technical 1-2 sentence description using precise typographic terminology. Describe compositional approach, weight relationships, and spatial logic. Use terms like "juxtaposition", "hierarchy", "structural", "kinetic", "rigid", "extreme weight", "balances".
10. **CRITICAL - Hierarchy Strategy & Pairing Note:** Must be detailed and technical. Use specific terminology like "juxtaposition", "static", "sharp", "anchors", "fluid", "manual energy", "clinical precision", "structural friction". Be specific about how typefaces interact.

### OUTPUT FORMAT (JSON ONLY):

{
  "system_audit": {
    "total_typefaces_identified": "Integer",
    "overall_layout_strategy": "Detailed technical summary of hierarchy and spatial logic using precise typographic terminology."
  },
  "typeface_profiles": [
    {
      "role": "heading | accent | body | brand-mark (CHOOSE ONE ONLY)",
      "morphology_category": "humanist | geometric | grotesque | slab | script | display",
      "weights_and_styles_count": "e.g., 2 weights (Bold, Regular) + 1 italic style",
      "construction_type": "standard-typography | illustrated-custom",
      "google_font_equivalents": ["Niche Match 1", "Niche Match 2"],
      "morphological_dna": {
        "stroke_contrast": "monolinear | high-contrast | modulated",
        "axis_and_stress": "e.g., vertical-modernist axis | oblique-humanist stress",
        "terminal_style": "MUST be specific descriptive phrase: rounded-pill, razor-sharp serif, beveled-cut, flat-horizontal cuts, rounded brush-tip exits",
        "x_height_ratio": "e.g., high-modernist, classical-low",
        "negative_space": "e.g., open-apertures, tight-counters"
      },
      "visual_treatments": {
        "effects": "e.g., offset drop-shadow, inner-bevel, distressed-texture",
        "gradient_logic": "e.g., vertical tonal-shift, linear luminance-fade"
      },
      "rhythm_and_pace": "e.g., staccato/tight tracking | legato/fluid-continuity"
    }
  ],
  "typographic_relationships": {
    "pairing_contrast": "high | medium | low",
    "hierarchy_strategy": "Detailed technical description: e.g., extreme scale difference / weight juxtaposition / style and scale juxtaposition",
    "integration_logic": "e.g., grid-locked / overlapping / staggered-baseline",
    "pairing_note": "Detailed technical analysis of the synergy or friction between the layers using precise terminology."
  },
  "technical_markers": {
    "sub_culture_alignment": "e.g., Swiss-Modernism, Brutalist, Tech-Minimal",
    "modular_logic": "grid-based construction | organic/free-form flow",
    "optical_intent": "high-detail-display | functional-small-scale"
  },
  "visual_style_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "mood_tone": "The psychological impact and brand voice."
}"""
    },
    {
        "folder": "photography/products",
        "json_path": "data/photography_metadata.json",
        "mode": "standard",
        "system_prompt": """You are a specialist assistant that helps users write high-quality, technical metadata for product photography and mockups. 

Analyze the image and return a JSON object with exactly twelve fields.

### CRITICAL CONSTRAINTS (DO NOT IGNORE):

1. **NO Specific Colors:** Never mention actual color names. Describe the palette's nature (e.g., 'high-chroma', 'neutral-toned', 'monochromatic', 'earth-biased', 'desaturated').

2. **NO Specific Product Names:** Do not name brands or specific commercial products. Describe only the category or geometric form (e.g., 'cylindrical container' instead of 'soda can').

3. **NO Specific Content Details:** Never describe specific items visible. Use ONLY generic, broad categories:
   - Clothing/garments → 'fashion items' or 'apparel pieces'
   - Food (NEVER say 'salad', 'fruit', 'chocolate', 'lemon', etc.) → 'food items' or 'organic food elements' or 'edible elements'
   - Books/magazines/print → 'printed materials' or 'print items'
   - Packaging/containers → 'packaging elements' or 'container types'
   - Plants/botanical → 'botanical elements' or 'organic plant matter'
   - Hands/body parts → 'human body elements' or 'anthropomorphic elements'
   - Furniture/tables → 'furniture elements' or 'surface elements'
   Always use the MOST GENERIC category term possible. NEVER mention specific items like 'lemon', 't-shirt', 'book', 'hand', 'table', 'salad', 'chocolate', 'jacket', 'bottle', etc. Use only broad categories.

4. **NO Text Content:** If text appears, describe only its typographic style (e.g., 'bold sans-serif', 'minimalist branding', 'condensed slab-serif') without quoting the content.

5. **Focus on Environment & Lighting:** Provide detailed descriptions of the props, surfaces, lighting quality, and shadow physics.

6. **NO Marketing Hype:** Avoid subjective adjectives like 'stunning' or 'beautiful'. Use technical and material-focused terminology.

7. **Mockup vs Real Product:** If the image shows a mockup (digital placement on surface), indicate this. If it shows a real photographed product, indicate this.

### FIELD DEFINITIONS:

- **description:** Technical summary of the object's interaction with its environment and lighting. Must be detailed and specific, combining multiple elements. Use ONLY generic categories - NEVER describe specific items (no 'salad', 'chocolate', 'jacket', 'hand', 'lemon', etc.). If it's a mockup, mention 'mockup' or 'digital placement'. (e.g., 'Commercial arrangement featuring multiple metallic containers integrated into a high-contrast social environment with sharp shadow definition').

- **product_type:** The generic category/form of the main subject. Use broad categories: 'fashion item', 'printed material', 'packaging/container', 'food item', 'beverage container', 'apparel piece', 'textile product', 'consumer good', 'electronic device mockup', etc. If it's a mockup (digital placement), include 'mockup' in the description (e.g., 'packaging mockup', 'print mockup'). Never describe specific items like 't-shirt' (use 'fashion item'), 'salad' (use 'food item'), 'book' (use 'printed material').

- **environment_elements:** Detailed list of props and surrounding objects using ONLY GENERIC CATEGORIES. Use commas to separate items. NEVER mention specific items - use ONLY broad categories:
   - Instead of 'sliced lemon', 'orange', 'fruit', 'salad', 'chocolate', 'candy' → 'organic food elements' or 'food items' or 'edible elements'
   - Instead of 't-shirts', 'jackets', 'clothing', 'apparel' → 'fashion items' or 'apparel pieces'
   - Instead of 'books', 'magazines', 'print' → 'printed materials'
   - Instead of 'hands', 'arms', 'fingers' → 'human body elements' or 'anthropomorphic elements'
   - Instead of 'table', 'chair', 'cart', 'bag' → 'furniture elements' or 'surface elements' or 'carrying elements'
   Use ONLY generic descriptors: 'organic food elements', 'geometric props', 'textile layers', 'printed materials', 'packaging items', 'furniture elements', 'botanical elements', 'human body elements', etc. (e.g., 'organic food elements, small circular container elements, layered food items, and a vertically-slatted furniture element').

- **surface_and_texture:** The physical properties of the base surface with specific descriptors (e.g., 'high-vibrance smooth tabletop adjacent to a textured vertical wall').

- **lighting_setup:** The quality, direction, and source of light with specific details (e.g., 'harsh, direct overhead light creating high-luminance highlights').

- **shadow_character:** The physical nature of the shadows with specific descriptors (e.g., 'short, hard-edged directional shadows with high density').

- **materiality:** The physical finishes of all objects with specific descriptors, comma-separated (e.g., 'metallic aluminum, organic pulpy fibers, and matte paper-based elements').

- **shot_angle:** The camera perspective (e.g., 'high-angle perspective', 'top-down bird's-eye', 'low-angle heroic', 'straight-on eye-level').

- **visual_era:** The design period referenced (e.g., 'contemporary-pop commercial', 'contemporary-minimal', 'mid-century-modern', 'retro-commercial').

- **spatial_arrangement:** The compositional structure with specific descriptors (e.g., 'organized dynamic clutter with overlapping focal points').

- **visual_style_tags:** Five technical/aesthetic hyphenated keywords for vector indexing (e.g., ["hard-light", "commercial-maximalism", "material-contrast", "high-chroma-palette", "top-down-framing"]).

- **mood_tone:** The commercial or atmospheric resonance (e.g., 'vibrant, social, and high-energy', 'serene and clinical').

### EXAMPLE OUTPUTS (for reference):
Example 1 - Real Product:
{
  "description": "Commercial arrangement featuring multiple metallic containers integrated into a high-contrast social environment with sharp shadow definition.",
  "product_type": "beverage containers",
  "environment_elements": "organic food elements, small circular container elements, layered food items, and a vertically-slatted furniture element",
  "surface_and_texture": "high-vibrance smooth tabletop adjacent to a textured vertical wall",
  "lighting_setup": "harsh, direct overhead light creating high-luminance highlights",
  "shadow_character": "short, hard-edged directional shadows with high density",
  "materiality": "metallic aluminum, organic pulpy fibers, and matte paper-based elements",
  "shot_angle": "high-angle perspective",
  "visual_era": "contemporary-pop commercial",
  "spatial_arrangement": "organized dynamic clutter with overlapping focal points",
  "visual_style_tags": ["hard-light", "commercial-maximalism", "material-contrast", "high-chroma-palette", "top-down-framing"],
  "mood_tone": "vibrant, social, and high-energy"
}

Example 2 - Mockup (if applicable):
{
  "description": "Digital mockup placement of printed material on textured surface with simulated lighting and shadow interaction.",
  "product_type": "print mockup",
  "environment_elements": "textured surface element and simulated background context",
  ...
}

### OUTPUT FORMAT (JSON ONLY):

{
  "description": "Technical analysis of the setup.",
  "product_type": "Main object category",
  "environment_elements": "Props and environmental details",
  "surface_and_texture": "Surface character",
  "lighting_setup": "Light quality and source",
  "shadow_character": "Nature of shadows",
  "materiality": "Surface finishes",
  "shot_angle": "Camera perspective",
  "visual_era": "Aesthetic era",
  "spatial_arrangement": "Composition style",
  "visual_style_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "mood_tone": "Commercial vibe"
}"""
    }
]

def get_user_prompt(folder_name: str) -> str:
    """Get appropriate user prompt based on folder type"""
    if folder_name == "logo_geometry":
        return "Analyze this image and return a JSON object with 'description', 'logo_type', 'style_character', 'visual_era', 'visual_style_tags', and 'brand_voice' fields."
    elif folder_name == "illustration":
        return "Analyze this image and return a JSON object with 'description', 'content_category', 'style_character', 'visual_era', 'audience_appeal', 'visual_style_tags', and 'mood_tone' fields."
    elif folder_name == "typography":
        return "Analyze this typography image and return a JSON object with 'system_audit', 'typeface_profiles', 'typographic_relationships', 'technical_markers', 'visual_style_tags', and 'mood_tone' fields. Ensure system_audit has 'total_typefaces_identified' and 'overall_layout_strategy', typeface_profiles is an array of typeface objects with all required fields, typographic_relationships has 'pairing_contrast', 'hierarchy_strategy', 'integration_logic', and 'pairing_note', and technical_markers has 'sub_culture_alignment', 'modular_logic', and 'optical_intent'."
    elif folder_name == "photography/environments":
        return "Analyze this image and return a JSON object with 'description', 'product_type', 'environment_elements', 'surface_and_texture', 'lighting_setup', 'shadow_character', 'materiality', 'shot_angle', 'visual_era', 'spatial_arrangement', 'visual_style_tags', and 'mood_tone' fields."
    elif folder_name == "photography/models":
        return "Analyze this image and return a JSON object with 'description', 'demographics', 'gender', 'facial_architecture', 'skin_and_body_detail', 'hair_character', 'gaze_direction', 'facial_symmetry', 'sub_culture_alignment', 'character_energy', 'persona_style', and 'visual_identity_tags' fields."
    elif folder_name == "photography/products":
        return "Analyze this image and return a JSON object with 'description', 'product_type', 'environment_elements', 'surface_and_texture', 'lighting_setup', 'shadow_character', 'materiality', 'shot_angle', 'visual_era', 'spatial_arrangement', 'visual_style_tags', and 'mood_tone' fields."
    elif folder_name.startswith("photography/"):
        return "Analyze this image and return a JSON object with the required fields."
    else:
        return "Analyze this image according to your expertise and provide a detailed description."

USER_PROMPT = "Analyze this image and return a JSON object with the required fields."  # Default, will be overridden per category


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


def analyze_image(client: OpenAI, image_path: Path, system_prompt: str, user_prompt: str = None, provider: str = 'openrouter', max_retries: int = 3, required_fields: List[str] = None, max_tokens: int = 400) -> Optional[dict]:
    """Analyze a single image using Vision API with category-specific prompt and retry logic.
    Returns a dictionary if JSON parsing succeeds, or None if parsing fails.
    
    Args:
        required_fields: List of required field names to validate in the JSON response.
                         If None, will attempt to parse without strict validation.
        max_tokens: Maximum tokens for API response (default 400, typography needs more)"""
    for attempt in range(max_retries):
        try:
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
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt if user_prompt else USER_PROMPT
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
                max_tokens=max_tokens,
                temperature=0.8,
            )
            
            response_text = response.choices[0].message.content
            if not response_text:
                print(f"\n⚠️  Empty response from API for {image_path.name}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
            response_text = response_text.strip()
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    # Extract JSON from markdown code block
                    lines = response_text.split('\n')
                    json_start = None
                    json_end = None
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        if stripped.startswith("```json") or (stripped.startswith("```") and json_start is None):
                            json_start = i + 1
                        elif stripped == "```" and json_start is not None:
                            json_end = i
                            break
                    if json_start is not None:
                        if json_end is not None:
                            response_text = '\n'.join(lines[json_start:json_end])
                        else:
                            # No closing ``` found, take everything after opening
                            response_text = '\n'.join(lines[json_start:])
                
                parsed_json = json.loads(response_text)
                # Validate that it has the expected fields (if required_fields provided)
                if required_fields:
                    if isinstance(parsed_json, dict) and all(key in parsed_json for key in required_fields):
                        return parsed_json
                    else:
                        # Missing required fields, return None to trigger retry or error
                        missing = [f for f in required_fields if f not in parsed_json]
                        print(f"\n⚠️  JSON response missing required fields for {image_path.name}: {missing}")
                        return None
                else:
                    # No validation required, return as-is
                    return parsed_json if isinstance(parsed_json, dict) else None
            except json.JSONDecodeError as e:
                # If JSON parsing fails, return None
                print(f"\n⚠️  Failed to parse JSON response for {image_path.name}: {e}")
                if response_text:
                    print(f"   Raw response (first 500 chars): {response_text[:500]}")
                else:
                    print(f"   Raw response: (empty or None)")
                return None
            
        except Exception as e:
            error_str = str(e)
            
            # Check for rate limit errors
            if '403' in error_str or 'rate limit' in error_str.lower() or 'limit exceeded' in error_str.lower():
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 2^attempt seconds
                    wait_time = 2 ** attempt
                    print(f"\n⚠️  Rate limit hit for {image_path.name}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"\n❌ Rate limit exceeded for {image_path.name} after {max_retries} attempts")
                    return None
            else:
                # Other errors - don't retry
                print(f"\n⚠️  Error analyzing {image_path.name}: {e}")
                return None
    
    return None


def load_color_data(color_data_folder: Path) -> Dict:
    """Load all JSON files from color_data folder for merge mode"""
    if not color_data_folder.exists():
        print(f"⚠️  Color data folder not found: {color_data_folder}")
        return {}
    
    color_data = {}
    json_files = list(color_data_folder.glob('*.json'))
    
    if not json_files:
        print(f"⚠️  No JSON files found in {color_data_folder}")
        return {}
    
    print(f"   Loading {len(json_files)} color JSON files...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                entry = json.load(f)
            
            # Use filename from JSON as key, or derive from JSON filename
            filename = entry.get('filename')
            if not filename:
                # Derive from JSON filename (e.g., color_00228.json -> color_00228.png)
                filename = json_file.stem + '.png'
            
            color_data[filename] = entry
            
        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}")
            continue
    
    return color_data


def find_image_for_color(color_filename: str, images_folder: Path) -> Optional[Path]:
    """Find the corresponding image file for a color JSON entry"""
    # Try exact match first
    image_path = images_folder / color_filename
    if image_path.exists():
        return image_path
    
    # Try without extension variations
    stem = Path(color_filename).stem
    for ext in IMAGE_EXTENSIONS:
        image_path = images_folder / f"{stem}{ext}"
        if image_path.exists():
            return image_path
        image_path = images_folder / f"{stem}{ext.upper()}"
        if image_path.exists():
            return image_path
    
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


def process_merge_mode(client: OpenAI, config: Dict, project_root: Path, provider: str):
    """Process colors in merge mode: append semantic_vibe to existing color_analysis.json"""
    folder_name = config["folder"]
    json_path = config["json_path"]
    system_prompt = config["system_prompt"]
    
    print(f"\n{'=' * 70}")
    print(f"Processing {folder_name} (MERGE MODE)")
    print(f"{'=' * 70}")
    
    # Load existing color_analysis.json if it exists
    output_file = project_root / json_path
    existing_data = {}
    
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
            print(f"📂 Found existing {json_path}: {len(existing_data)} entries")
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing {json_path}: {e}")
            existing_data = {}
    
    # Load color JSON files from color_data folder
    color_data_folder = project_root / 'data' / folder_name / 'color_data'
    color_data = load_color_data(color_data_folder)
    
    if not color_data:
        print(f"❌ No color data found. Skipping {folder_name}")
        return
    
    # Merge color_data into existing_data (color_data takes precedence for missing entries)
    # This ensures we have all entries, even if color_analysis.json was incomplete
    for color_filename, color_entry in color_data.items():
        if color_filename in existing_data:
            # Preserve existing_data fields, but update with any new fields from color_data
            # This ensures we don't lose any existing semantic_vibe or other fields
            existing_entry = existing_data[color_filename]
            # Only update fields that don't exist in existing_data
            for key, value in color_entry.items():
                if key not in existing_entry:
                    existing_entry[key] = value
        else:
            # New entry from color_data
            existing_data[color_filename] = color_entry
    
    # Get images folder
    images_folder = project_root / 'data' / folder_name
    
    # Match color data to images and process
    images_to_process = []
    for color_filename, color_entry in existing_data.items():
        image_path = find_image_for_color(color_filename, images_folder)
        if image_path:
            # Check if semantic_vibe already exists
            if 'semantic_vibe' not in color_entry:
                images_to_process.append((image_path, color_filename, color_entry))
    
    if not images_to_process:
        print(f"✅ All colors already have semantic_vibe!")
        # Still save to ensure all entries are in the consolidated file
        with open(output_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        return
    
    print(f"🔍 Processing {len(images_to_process)} colors that need semantic_vibe...")
    
    processed_count = 0
    error_count = 0
    
    # Process with progress bar
    for image_path, color_filename, color_entry in tqdm(images_to_process, desc=f"[{folder_name}]", unit="img"):
        description = analyze_image(client, image_path, system_prompt, provider=provider)
        
        if description:
            # Append semantic_vibe to existing entry (preserve all other fields)
            color_entry['semantic_vibe'] = description
            existing_data[color_filename] = color_entry
            processed_count += 1
            
            # Save incrementally every 10 images
            if processed_count % 10 == 0:
                with open(output_file, 'w') as f:
                    json.dump(existing_data, f, indent=2)
        else:
            error_count += 1
        
        # Small delay between requests to avoid rate limits (0.5 seconds)
        time.sleep(0.5)
    
    # Final save
    print(f"💾 Saving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"✅ Complete: {processed_count} processed, {error_count} errors")
    print(f"📊 Total entries in {json_path}: {len(existing_data)}")


def process_standard_mode(client: OpenAI, config: Dict, project_root: Path, provider: str):
    """Process logos/illustrations/photography in standard mode: create/update metadata JSON"""
    folder_name = config["folder"]
    json_path = config["json_path"]
    system_prompt = config["system_prompt"]
    
    print(f"\n{'=' * 70}")
    print(f"Processing {folder_name} (STANDARD MODE)")
    print(f"{'=' * 70}")
    
    # Get images folder - handle subfolders (e.g., photography/environments)
    images_folder = project_root / 'data' / folder_name
    if not images_folder.exists():
        print(f"⚠️  Folder not found: {images_folder}")
        return
    
    # Get all images
    image_files = get_images_from_folder(images_folder)
    if not image_files:
        print(f"⚠️  No images found in {images_folder}")
        return
    
    print(f"📁 Found {len(image_files)} images")
    
    # Load existing metadata if file exists
    output_file = project_root / json_path
    existing_metadata = {}
    
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                existing_metadata = json.load(f)
            print(f"📂 Found existing {json_path}: {len(existing_metadata)} entries")
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing {json_path}: {e}")
            existing_metadata = {}
    else:
        print(f"📂 Creating new {json_path}")
    
    # Filter out already processed images
    images_to_process = [
        img for img in image_files 
        if img.name not in existing_metadata
    ]
    
    if not images_to_process:
        print(f"✅ All images already processed!")
        return
    
    print(f"🔍 Processing {len(images_to_process)} new images...")
    
    metadata = existing_metadata.copy()
    processed_count = 0
    error_count = 0
    consecutive_rate_limit_errors = 0
    max_consecutive_rate_limit_errors = 10  # Increased to allow more retries
    
    # Determine required fields based on folder type
    if folder_name == "logo_geometry":
        required_fields = ['description', 'logo_type', 'style_character', 'visual_era', 'visual_style_tags', 'brand_voice']
    elif folder_name == "illustration":
        required_fields = ['description', 'content_category', 'style_character', 'visual_era', 'audience_appeal', 'visual_style_tags', 'mood_tone']
    elif folder_name == "typography":
        required_fields = ['system_audit', 'typeface_profiles', 'typographic_relationships', 'technical_markers', 'visual_style_tags', 'mood_tone']
    elif folder_name == "photography/environments":
        required_fields = ['description', 'product_type', 'environment_elements', 'surface_and_texture', 'lighting_setup', 'shadow_character', 'materiality', 'shot_angle', 'visual_era', 'spatial_arrangement', 'visual_style_tags', 'mood_tone']
    elif folder_name == "photography/models":
        required_fields = ['description', 'demographics', 'gender', 'facial_architecture', 'skin_and_body_detail', 'hair_character', 'gaze_direction', 'facial_symmetry', 'sub_culture_alignment', 'character_energy', 'persona_style', 'visual_identity_tags']
    elif folder_name == "photography/products":
        required_fields = ['description', 'product_type', 'environment_elements', 'surface_and_texture', 'lighting_setup', 'shadow_character', 'materiality', 'shot_angle', 'visual_era', 'spatial_arrangement', 'visual_style_tags', 'mood_tone']
    elif folder_name.startswith("photography/"):
        required_fields = None
    else:
        required_fields = None  # No strict validation for other types
    
    # Get user prompt for this category
    user_prompt = get_user_prompt(folder_name)
    
    # Determine max_tokens based on folder type (typography needs more tokens for complex nested structure)
    max_tokens = 2000 if folder_name == "typography" else 400
    
    # Process with progress bar
    for image_path in tqdm(images_to_process, desc=f"[{folder_name}]", unit="img"):
        analysis_result = analyze_image(client, image_path, system_prompt, user_prompt=user_prompt, provider=provider, required_fields=required_fields, max_tokens=max_tokens)
        
        if analysis_result:
            # Build metadata entry based on folder type
            # For typography, use overall_layout_strategy as description
            if folder_name == "typography":
                description = analysis_result.get("system_audit", {}).get("overall_layout_strategy", "")
            else:
                description = analysis_result.get("description", "")
            
            entry = {
                "filename": image_path.name,
                "description": description,
                "file_path": str(image_path.relative_to(project_root)),
                "category": folder_name
            }
            
            # Add fields specific to logo, illustration, typography, or photography
            if folder_name == "logo_geometry":
                entry.update({
                    "logo_type": analysis_result.get("logo_type", ""),
                    "style_character": analysis_result.get("style_character", ""),
                    "visual_era": analysis_result.get("visual_era", ""),
                    "visual_style_tags": analysis_result.get("visual_style_tags", []),
                    "brand_voice": analysis_result.get("brand_voice", "")
                })
            elif folder_name == "illustration":
                entry.update({
                    "content_category": analysis_result.get("content_category", ""),
                    "style_character": analysis_result.get("style_character", ""),
                    "visual_era": analysis_result.get("visual_era", ""),
                    "audience_appeal": analysis_result.get("audience_appeal", ""),
                    "visual_style_tags": analysis_result.get("visual_style_tags", []),
                    "mood_tone": analysis_result.get("mood_tone", "")
                })
            elif folder_name == "typography":
                # Typography has complex nested structure - preserve entire analysis_result
                entry.update({
                    "system_audit": analysis_result.get("system_audit", {}),
                    "typeface_profiles": analysis_result.get("typeface_profiles", []),
                    "typographic_relationships": analysis_result.get("typographic_relationships", {}),
                    "technical_markers": analysis_result.get("technical_markers", {}),
                    "visual_style_tags": analysis_result.get("visual_style_tags", []),
                    "mood_tone": analysis_result.get("mood_tone", "")
                })
            elif folder_name == "photography/environments":
                # Extract subfolder name (e.g., "environments", "models", "products")
                subfolder = folder_name.split("/")[-1]
                entry.update({
                    "subfolder": subfolder,
                    "product_type": analysis_result.get("product_type", ""),
                    "environment_elements": analysis_result.get("environment_elements", ""),
                    "surface_and_texture": analysis_result.get("surface_and_texture", ""),
                    "lighting_setup": analysis_result.get("lighting_setup", ""),
                    "shadow_character": analysis_result.get("shadow_character", ""),
                    "materiality": analysis_result.get("materiality", ""),
                    "shot_angle": analysis_result.get("shot_angle", ""),
                    "visual_era": analysis_result.get("visual_era", ""),
                    "spatial_arrangement": analysis_result.get("spatial_arrangement", ""),
                    "visual_style_tags": analysis_result.get("visual_style_tags", []),
                    "mood_tone": analysis_result.get("mood_tone", "")
                })
            elif folder_name == "photography/models":
                # Extract subfolder name
                subfolder = folder_name.split("/")[-1]
                entry.update({
                    "subfolder": subfolder,
                    "demographics": analysis_result.get("demographics", ""),
                    "gender": analysis_result.get("gender", ""),
                    "facial_architecture": analysis_result.get("facial_architecture", ""),
                    "skin_and_body_detail": analysis_result.get("skin_and_body_detail", ""),
                    "hair_character": analysis_result.get("hair_character", ""),
                    "gaze_direction": analysis_result.get("gaze_direction", ""),
                    "facial_symmetry": analysis_result.get("facial_symmetry", ""),
                    "sub_culture_alignment": analysis_result.get("sub_culture_alignment", ""),
                    "character_energy": analysis_result.get("character_energy", ""),
                    "persona_style": analysis_result.get("persona_style", ""),
                    "visual_identity_tags": analysis_result.get("visual_identity_tags", [])
                })
            elif folder_name == "photography/products":
                # Extract subfolder name
                subfolder = folder_name.split("/")[-1]
                entry.update({
                    "subfolder": subfolder,
                    "product_type": analysis_result.get("product_type", ""),
                    "environment_elements": analysis_result.get("environment_elements", ""),
                    "surface_and_texture": analysis_result.get("surface_and_texture", ""),
                    "lighting_setup": analysis_result.get("lighting_setup", ""),
                    "shadow_character": analysis_result.get("shadow_character", ""),
                    "materiality": analysis_result.get("materiality", ""),
                    "shot_angle": analysis_result.get("shot_angle", ""),
                    "visual_era": analysis_result.get("visual_era", ""),
                    "spatial_arrangement": analysis_result.get("spatial_arrangement", ""),
                    "visual_style_tags": analysis_result.get("visual_style_tags", []),
                    "mood_tone": analysis_result.get("mood_tone", "")
                })
            elif folder_name.startswith("photography/"):
                # Extract subfolder name
                subfolder = folder_name.split("/")[-1]
                entry.update({
                    "subfolder": subfolder
                })
                # Add all fields from result
                entry.update(analysis_result)
            else:
                # Generic fallback - include all fields from result
                entry.update(analysis_result)
            
            metadata[image_path.name] = entry
            processed_count += 1
            consecutive_rate_limit_errors = 0  # Reset counter on success
            
            # Save incrementally every 10 images
            if processed_count % 10 == 0:
                with open(output_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
        else:
            error_count += 1
            consecutive_rate_limit_errors += 1
            
            # If too many consecutive errors, likely rate limit - stop and save progress
            if consecutive_rate_limit_errors >= max_consecutive_rate_limit_errors:
                print(f"\n⚠️  Too many consecutive errors ({consecutive_rate_limit_errors}). Likely rate limit hit.")
                print(f"💾 Saving progress ({processed_count} images processed so far)...")
                with open(output_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"⏸️  Stopping early. You can resume later - already processed images will be skipped.")
                break
        
        # Delay between requests - longer for illustrations to avoid rate limits
        # Increased to 3 seconds to better handle rate limits
        delay = 3.0 if folder_name == "illustration" else 0.5
        time.sleep(delay)
    
    # Final save
    print(f"💾 Saving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Complete: {processed_count} processed, {error_count} errors")
    print(f"📊 Total entries in {json_path}: {len(metadata)}")


def main():
    print("=" * 70)
    print("Graphics Enrichment - AI Metadata Generation")
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
        
        # Count total images to process
        total_images = 0
        configs_to_process = ASSET_CONFIG
        
        # If --illustrations-only flag, only process illustrations
        if '--illustrations-only' in sys.argv:
            configs_to_process = [c for c in ASSET_CONFIG if c["folder"] == "illustration"]
            print("\n📌 Processing ONLY illustrations (--illustrations-only flag)")
        
        for config in configs_to_process:
            folder_name = config["folder"]
            folder_path = project_root / 'data' / folder_name
            
            if config["mode"] == "merge":
                # For merge mode, count images that need processing
                color_data_folder = project_root / 'data' / folder_name / 'color_data'
                if color_data_folder.exists():
                    color_data = load_color_data(color_data_folder)
                    images_folder = project_root / 'data' / folder_name
                    for color_filename, color_entry in color_data.items():
                        if 'semantic_vibe' not in color_entry:
                            image_path = find_image_for_color(color_filename, images_folder)
                            if image_path:
                                total_images += 1
            else:
                # For standard mode, count unprocessed images
                if folder_path.exists():
                    image_files = get_images_from_folder(folder_path)
                    output_file = project_root / config["json_path"]
                    existing_metadata = {}
                    if output_file.exists():
                        try:
                            with open(output_file, 'r') as f:
                                existing_metadata = json.load(f)
                        except:
                            pass
                    images_to_process = [img for img in image_files if img.name not in existing_metadata]
                    total_images += len(images_to_process)
        
        if total_images == 0:
            print("\n✅ All assets already processed!")
            return
        
        print(f"\n📊 Total images to process: {total_images}")
        
        # Estimate costs
        cost_estimate = estimate_cost(total_images)
        print(f"\n💰 Cost Estimate:")
        print(f"   Estimated cost: ${cost_estimate['estimated_total']:.2f}")
        print(f"   (Approximate - actual cost may vary)")
        
        # Confirm before proceeding
        num_categories = len(configs_to_process)
        print(f"\n⚠️  This will process {total_images} images across {num_categories} category/categories.")
        if '--yes' not in sys.argv:
            response = input("Continue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled.")
                sys.exit(0)
        else:
            print("🚀 Auto-confirmed (--yes flag provided)")
        
        # Process each category (or only illustrations if --illustrations-only flag)
        if '--illustrations-only' in sys.argv:
            # Process only illustrations
            illustration_config = next((c for c in ASSET_CONFIG if c["folder"] == "illustration"), None)
            if illustration_config:
                process_standard_mode(client, illustration_config, project_root, provider)
            else:
                print("❌ Illustration config not found")
        else:
            # Process all categories
            for config in ASSET_CONFIG:
                if config["mode"] == "merge":
                    process_merge_mode(client, config, project_root, provider)
                else:
                    process_standard_mode(client, config, project_root, provider)
        
        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        for config in ASSET_CONFIG:
            output_file = project_root / config["json_path"]
            if output_file.exists():
                with open(output_file, 'r') as f:
                    metadata = json.load(f)
                print(f"📊 {config['folder']}: {len(metadata)} total entries in {config['json_path']}")
        
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

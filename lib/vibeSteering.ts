/**
 * Vibe Steering Configuration
 * 
 * Defines slider configurations for 7 distinct categories.
 * Each category has exactly 3 sliders with labelLeft and labelRight.
 * Slider values range from -1 to 1.
 */

export interface SliderConfig {
  key: string;
  labelLeft: string;
  labelRight: string;
}

export interface CategorySliders {
  [categoryKey: string]: SliderConfig[];
}

export const CATEGORY_SLIDERS: CategorySliders = {
  // Colors
  colors: [
    { key: 'warm_cool', labelLeft: 'Warm', labelRight: 'Cool' },
    { key: 'pastel_neon', labelLeft: 'Pastel', labelRight: 'Neon' },
    { key: 'dark_bright', labelLeft: 'Dark', labelRight: 'Bright' },
  ],

  // Typography (Fonts)
  typography: [
    { key: 'serif_sans', labelLeft: 'Serif', labelRight: 'Sans' },
    { key: 'light_bold', labelLeft: 'Light', labelRight: 'Bold' },
    { key: 'condensed_extended', labelLeft: 'Condensed', labelRight: 'Extended' },
  ],

  // Logo
  logo: [
    { key: 'typographic_iconic', labelLeft: 'Typographic', labelRight: 'Iconic' },
    { key: 'geometric_organic', labelLeft: 'Geometric', labelRight: 'Organic' },
    { key: 'minimal_detailed', labelLeft: 'Minimal', labelRight: 'Detailed' },
  ],

  // Illustration
  illustration: [
    { key: 'flat_3d', labelLeft: 'Flat', labelRight: '3D' },
    { key: 'abstract_literal', labelLeft: 'Abstract', labelRight: 'Literal' },
    { key: 'digital_handdrawn', labelLeft: 'Digital', labelRight: 'Hand-Drawn' },
  ],

  // Photo_Model
  photo_model: [
    { key: 'staged_candid', labelLeft: 'Staged', labelRight: 'Candid' },
    { key: 'portrait_fullbody', labelLeft: 'Portrait', labelRight: 'Full Body' },
    { key: 'direct_gaze_looking_away', labelLeft: 'Direct Gaze', labelRight: 'Looking Away' },
  ],

  // Photo_Product
  photo_product: [
    { key: 'studio_clean_contextual', labelLeft: 'Studio Clean', labelRight: 'Contextual' },
    { key: 'soft_light_hard_light', labelLeft: 'Soft Light', labelRight: 'Hard Light' },
    { key: 'macro_full_object', labelLeft: 'Macro', labelRight: 'Full Object' },
  ],

  // Photo_Environment
  photo_environment: [
    { key: 'interior_exterior', labelLeft: 'Interior', labelRight: 'Exterior' },
    { key: 'urban_nature', labelLeft: 'Urban', labelRight: 'Nature' },
    { key: 'day_night', labelLeft: 'Day', labelRight: 'Night' },
  ],
};

/**
 * Maps category keys from UI to backend category types
 */
export const CATEGORY_TYPE_MAP: Record<string, string> = {
  'brand_color_mood': 'colors',
  'typography': 'typography',
  'logo_geometry': 'logo',
  'illustration': 'illustration',
  'models': 'photo_model',
  'products': 'photo_product',
  'environments': 'photo_environment',
};

/**
 * Maps slider values to keywords for vector arithmetic
 * Returns keywords to add to the search query based on slider values
 */
export function getSliderKeywords(
  categoryType: string,
  sliderValues: Record<string, number>
): string[] {
  const keywords: string[] = [];

  switch (categoryType) {
    case 'colors':
      if (sliderValues.warm_cool > 0) keywords.push('cool tones, icy, blue-based');
      if (sliderValues.warm_cool < 0) keywords.push('warm tones, golden, orange-based');
      if (sliderValues.pastel_neon > 0) keywords.push('neon, vibrant, electric');
      if (sliderValues.pastel_neon < 0) keywords.push('pastel, soft, muted');
      if (sliderValues.dark_bright > 0) keywords.push('bright, luminous, high-key');
      if (sliderValues.dark_bright < 0) keywords.push('dark, shadowy, low-key');
      break;

    case 'typography':
      if (sliderValues.serif_sans > 0) keywords.push('sans-serif, modern, geometric');
      if (sliderValues.serif_sans < 0) keywords.push('serif, traditional, classical');
      if (sliderValues.light_bold > 0) keywords.push('bold, heavy, strong');
      if (sliderValues.light_bold < 0) keywords.push('light, thin, delicate');
      if (sliderValues.condensed_extended > 0) keywords.push('extended, wide, spacious');
      if (sliderValues.condensed_extended < 0) keywords.push('condensed, narrow, tight');
      break;

    case 'logo':
      if (sliderValues.typographic_iconic > 0) keywords.push('iconic, symbol, mark');
      if (sliderValues.typographic_iconic < 0) keywords.push('typographic, wordmark, letterform');
      if (sliderValues.geometric_organic > 0) keywords.push('organic, flowing, natural');
      if (sliderValues.geometric_organic < 0) keywords.push('geometric, structured, angular');
      if (sliderValues.minimal_detailed > 0) keywords.push('detailed, ornate, complex');
      if (sliderValues.minimal_detailed < 0) keywords.push('minimal, simple, clean');
      break;

    case 'illustration':
      if (sliderValues.flat_3d > 0) keywords.push('3D, dimensional, depth');
      if (sliderValues.flat_3d < 0) keywords.push('flat, two-dimensional, graphic');
      if (sliderValues.abstract_literal > 0) keywords.push('literal, representational, realistic');
      if (sliderValues.abstract_literal < 0) keywords.push('abstract, conceptual, symbolic');
      if (sliderValues.digital_handdrawn > 0) keywords.push('hand-drawn, sketchy, organic');
      if (sliderValues.digital_handdrawn < 0) keywords.push('digital, vector, precise');
      break;

    case 'photo_model':
      if (sliderValues.staged_candid > 0) keywords.push('lifestyle, caught in the moment, natural');
      if (sliderValues.staged_candid < 0) keywords.push('studio lighting, posed, fashion editorial');
      if (sliderValues.portrait_fullbody > 0) keywords.push('full body, environmental portrait');
      if (sliderValues.portrait_fullbody < 0) keywords.push('close-up portrait, face focus');
      if (sliderValues.direct_gaze_looking_away > 0) keywords.push('looking away, contemplative, indirect');
      if (sliderValues.direct_gaze_looking_away < 0) keywords.push('direct gaze, eye contact, engaging');
      break;

    case 'photo_product':
      if (sliderValues.studio_clean_contextual > 0) keywords.push('contextual, lifestyle, in-use');
      if (sliderValues.studio_clean_contextual < 0) keywords.push('studio clean, white background, isolated');
      if (sliderValues.soft_light_hard_light > 0) keywords.push('hard light, dramatic shadows, contrast');
      if (sliderValues.soft_light_hard_light < 0) keywords.push('soft light, diffused, even');
      if (sliderValues.macro_full_object > 0) keywords.push('full object, product shot, complete view');
      if (sliderValues.macro_full_object < 0) keywords.push('macro, detail, close-up');
      break;

    case 'photo_environment':
      if (sliderValues.interior_exterior > 0) keywords.push('exterior, outdoor, outside');
      if (sliderValues.interior_exterior < 0) keywords.push('interior, indoor, inside');
      if (sliderValues.urban_nature > 0) keywords.push('nature, natural, wilderness');
      if (sliderValues.urban_nature < 0) keywords.push('urban, city, metropolitan');
      if (sliderValues.day_night > 0) keywords.push('night, nocturnal, dark');
      if (sliderValues.day_night < 0) keywords.push('day, daylight, bright');
      break;
  }

  return keywords;
}

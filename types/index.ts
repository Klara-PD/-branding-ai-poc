export type LLMModel = "gpt-4o" | "claude-3-5-sonnet";

export interface DiscoveryFormData {
  businessName: string;
  location: string;
  targetAudience: string;
  styleDescription: string;
  systemInstructions: string;
  selectedModel: LLMModel;
}

export interface VisualDNA {
  brand_color_mood: {
    avoid: string[];
    visual_prompt: string; // Natural language visual narrative for CLIP
  };
  typography_voice: {
    avoid: string[];
    visual_prompt: string; // Natural language visual narrative for CLIP
  };
  logo_geometry_essence: {
    avoid: string[];
    visual_prompt: string; // Natural language visual narrative for CLIP
  };
  photography_cinematic_world: {
    avoid: string[];
    visual_prompt: string; // Natural language visual narrative for CLIP (combines all subcategories)
  };
  illustration_style_medium: {
    avoid: string[];
    visual_prompt: string; // Natural language visual narrative for CLIP
  };
}

export interface CreativeBrief {
  visualDNA: VisualDNA;
}

export interface BrandIdentityKit {
  logoUrl: string | null;
  assets: string[]; // Array of 4 image URLs
  isLoadingLogo: boolean;
  isLoadingAssets: boolean;
}

export interface InspirationItem {
  id: string;
  score: number;
  metadata: {
    file_path?: string;
    category?: string;
    filename?: string;
    colors_data?: string; // Stringified JSON from Pinecone
    hex_codes?: string[]; // Direct hex codes (if available)
    [key: string]: any;
  };
  // Parsed color data (extracted from metadata)
  palette?: string[]; // Array of hex codes
  accessibility?: {
    aaa_pairs?: Array<{
      bg_hex: string;
      fg_hex: string;
      wcag_level: string;
      contrast_ratio: number;
    }>;
  };
}

export type Step = 1 | 2 | 3 | 4;

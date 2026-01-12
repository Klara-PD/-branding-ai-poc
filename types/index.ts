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
    descriptors: string[];
    avoid: string[];
  };
  typography_voice: {
    descriptors: string[];
    avoid: string[];
  };
  logo_geometry_essence: {
    descriptors: string[];
    avoid: string[];
  };
  photography_cinematic_world: {
    backgrounds: string[];
    models: string[];
    products: string[];
    lighting: string[];
    avoid: string[];
  };
  illustration_style_medium: {
    descriptors: string[];
    avoid: string[];
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

export type Step = 1 | 2 | 3 | 4;

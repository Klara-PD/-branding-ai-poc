/**
 * AI SDK Structure for Branding Playground
 * 
 * This file contains the integration with Vercel AI SDK and Replicate.
 * Replicate API calls for logo and asset generation are active.
 * Creative brief generation still uses mock data (can be extended with AI SDK).
 */

import { createOpenAI } from '@ai-sdk/openai';
import { generateText, streamText } from 'ai';
import Replicate from 'replicate';

import type {
  DiscoveryFormData,
  CreativeBrief,
  BrandIdentityKit,
  LLMModel,
  VisualDNA,
} from "@/types";

/**
 * Generate a Visual DNA creative brief based on discovery form data
 * 
 * @param formData - The discovery form data (includes systemInstructions)
 * @param model - The LLM model to use
 * @param apiKeys - API keys for the providers
 * @returns A Visual DNA creative brief object
 */
export async function generateCreativeBrief(
  formData: DiscoveryFormData,
  model: LLMModel,
  apiKeys: {
    openrouter?: string;
    replicate?: string;
  }
): Promise<CreativeBrief> {
  console.log('🤖 [AI] Generating Creative Brief with model:', model);

  if (!apiKeys.openrouter) {
    console.error('❌ [AI] No OpenRouter API key provided');
    throw new Error('OpenRouter API key is required. Please add your API key in Settings.');
  }

  // Validate API key format
  if (!apiKeys.openrouter.startsWith('sk-or-v1-')) {
    console.warn('⚠️ [AI] API key format may be incorrect. Expected format: sk-or-v1-...');
  }
  
  console.log('🔑 [AI] API key prefix:', apiKeys.openrouter.substring(0, 15) + '...');

  // Map model to OpenRouter model name
  const openRouterModel = model === 'gpt-4o' 
    ? 'openai/gpt-4o' 
    : 'anthropic/claude-3.5-sonnet';

  console.log('✅ [AI] Using OpenRouter with model:', openRouterModel);

  try {
    // Use OpenAI SDK with OpenRouter's base URL
    // OpenRouter requires HTTP-Referer and X-Title headers
    // We need to use a custom fetch to add these headers
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
    
    const openai = createOpenAI({
      apiKey: apiKeys.openrouter,
      baseURL: 'https://openrouter.ai/api/v1',
      fetch: async (url, options = {}) => {
        // Add required OpenRouter headers
        const headers = new Headers(options.headers);
        headers.set('HTTP-Referer', appUrl);
        headers.set('X-Title', 'Branding AI POC');
        
        return fetch(url, {
          ...options,
          headers,
        });
      },
    });

    // Build prompt from form data
    // Note: formData may have brandBrief in styleDescription if using combined input
    const brandInfo = formData.styleDescription || formData.businessName || '';
    
    const prompt = `Based on the following brand information, generate a Visual DNA:

Brand: ${formData.businessName || 'Brand'}
Target Audience: ${formData.targetAudience || brandInfo}
Style Description: ${formData.styleDescription || brandInfo}

CRITICAL: For each category, you MUST provide ONLY:
- "visual_prompt" - A full descriptive sentence (2-3 sentences) that tells a visual story with context
- "avoid" - A list of 5 keywords to avoid

The "visual_prompt" should be a natural language description that CLIP can understand. Include:
- Context about the brand/industry (e.g., "coffee shop", "tech startup", "fashion brand")
- Visual style and mood
- Specific aesthetic qualities
- Cultural or design references when relevant

DO NOT include "descriptors", "keywords", or "tags" fields. Only provide "visual_prompt" and "avoid".

Example:
- BAD: {"descriptors": ["warm", "terracotta", "sunny"], "visual_prompt": "..."}
- GOOD: {"visual_prompt": "A warm and inviting color palette featuring terracotta oranges and sunny yellows, inspired by Barcelona architecture and morning light filtering through Mediterranean cafes.", "avoid": ["cold", "minimalist", "corporate"]}

Output MUST be valid JSON matching this exact structure:
{
  "brand_color_mood": {
    "avoid": ["5 keywords to avoid"],
    "visual_prompt": "A full descriptive sentence (2-3 sentences) about the color mood with brand context"
  },
  "typography_voice": {
    "avoid": ["5 keywords to avoid"],
    "visual_prompt": "A full descriptive sentence (2-3 sentences) about typography style with brand context"
  },
  "logo_geometry_essence": {
    "avoid": ["5 keywords to avoid"],
    "visual_prompt": "A full descriptive sentence (2-3 sentences) about logo style with brand context"
  },
  "photography_cinematic_world": {
    "avoid": ["5 keywords to avoid"],
    "visual_prompt": "A full descriptive sentence (2-3 sentences) combining backgrounds, models, products, and lighting into one cohesive visual narrative with brand context"
  },
  "illustration_style_medium": {
    "avoid": ["5 keywords to avoid"],
    "visual_prompt": "A full descriptive sentence (2-3 sentences) about illustration style with brand context"
  }
}

Return ONLY the JSON object, no markdown, no explanations.`;

    console.log('📤 [AI] Sending request to OpenRouter with model:', openRouterModel);
    console.log('📝 [AI] Prompt length:', prompt.length, 'characters');

    const { text } = await generateText({
      model: openai(openRouterModel),
      system: formData.systemInstructions,
      prompt: prompt,
      temperature: 0.7,
      maxTokens: 2000,
    });

    console.log('📝 [AI] Raw response received, parsing JSON...');
    
    // Extract JSON from response (handle markdown code blocks if present)
    let jsonText = text.trim();
    if (jsonText.startsWith('```json')) {
      jsonText = jsonText.replace(/^```json\n?/, '').replace(/\n?```$/, '');
    } else if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/^```\n?/, '').replace(/\n?```$/, '');
    }
    
    const visualDNA = JSON.parse(jsonText) as VisualDNA;
    console.log('✅ [AI] JSON parsed successfully');
    return { visualDNA };
  } catch (error: any) {
    console.error('❌ [AI] Error generating Creative Brief:', error);
    console.error('❌ [AI] Error details:', {
      message: error.message,
      cause: error.cause,
      stack: error.stack,
      response: error.response,
      status: error.status,
      statusCode: error.statusCode,
    });
    
    // Check for specific OpenRouter error patterns
    const errorMessage = error.message || '';
    const errorString = JSON.stringify(error).toLowerCase();
    
    // Provide more specific error messages
    if (errorMessage.includes('User not found') || errorMessage.includes('401') || errorString.includes('unauthorized')) {
      console.error('❌ [AI] OpenRouter authentication failed. Checking API key...');
      console.error('❌ [AI] API key present:', !!apiKeys.openrouter);
      console.error('❌ [AI] API key prefix:', apiKeys.openrouter?.substring(0, 10) || 'N/A');
      throw new Error('OpenRouter API key is invalid or expired. Please verify your API key is correct and active.');
    }
    if (errorMessage.includes('429') || errorString.includes('rate limit')) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }
    if (errorMessage.includes('model') || errorString.includes('model not found')) {
      throw new Error(`Model ${openRouterModel} is not available. Please try a different model.`);
    }
    if (errorMessage.includes('402') || errorString.includes('payment')) {
      throw new Error('OpenRouter account requires payment. Please add credits to your account.');
    }
    
    // Log the full error for debugging
    console.error('❌ [AI] Full error object:', error);
    throw new Error(`Failed to generate Creative Brief: ${errorMessage || 'Unknown error'}`);
  }
}

/**
 * Generate logo using Replicate (flux-1.1-pro)
 * 
 * @param logoGeometryEssence - The logo geometry essence descriptors
 * @param replicateApiKey - Replicate API key
 * @returns Logo image URL
 */
export async function generateLogo(
  logoGeometryEssence: string[],
  replicateApiKey?: string
): Promise<string | null> {
  // Return null if no API key (will show placeholder)
  if (!replicateApiKey) {
    console.warn("Replicate API key not provided, skipping logo generation");
    return null;
  }

  try {
    const replicate = new Replicate({
      auth: replicateApiKey,
    });

    // Create prompt from logo geometry essence descriptors
    const prompt = logoGeometryEssence
      .slice(0, 10) // Use first 10 descriptors
      .join(", ");
    
    const finalPrompt = `${prompt}, clean, solid flat background, professional logo design, minimalist, high quality`;

    const output = await replicate.run(
      "black-forest-labs/flux-1.1-pro",
      {
        input: {
          prompt: finalPrompt,
          aspect_ratio: "1:1",
          output_format: "png",
          output_quality: 95,
        },
      }
    );

    // Replicate returns an array of URLs
    if (Array.isArray(output) && output.length > 0) {
      return output[0] as string;
    }

    return null;
  } catch (error) {
    console.error("Error generating logo:", error);
    return null;
  }
}

/**
 * Generate brand mockup images using Replicate (flux-1.1-pro)
 * 
 * @param photographyCinematicWorld - The photography cinematic world descriptors
 * @param replicateApiKey - Replicate API key
 * @returns Array of 4 image URLs
 */
export async function generateBrandAssets(
  photographyCinematicWorld: {
    backgrounds: string[];
    models: string[];
    products: string[];
    lighting: string[];
  },
  replicateApiKey?: string
): Promise<string[]> {
  // Return empty array if no API key (will show placeholders)
  if (!replicateApiKey) {
    console.warn("Replicate API key not provided, skipping asset generation");
    return [];
  }

  try {
    const replicate = new Replicate({
      auth: replicateApiKey,
    });

    const prompts = [
      // Combine different elements for variety
      `${photographyCinematicWorld.backgrounds[0]}, ${photographyCinematicWorld.lighting[0]}, ${photographyCinematicWorld.products[0]}, professional brand photography, high quality`,
      `${photographyCinematicWorld.backgrounds[1]}, ${photographyCinematicWorld.lighting[1]}, ${photographyCinematicWorld.models[0]}, cinematic brand photography, high quality`,
      `${photographyCinematicWorld.backgrounds[2]}, ${photographyCinematicWorld.lighting[2]}, ${photographyCinematicWorld.products[1]}, premium brand mockup, high quality`,
      `${photographyCinematicWorld.backgrounds[3]}, ${photographyCinematicWorld.lighting[3]}, ${photographyCinematicWorld.models[1]}, elegant brand photography, high quality`,
    ];

    const imageUrls: string[] = [];

    for (const prompt of prompts) {
      try {
        const output = await replicate.run(
          "black-forest-labs/flux-1.1-pro",
          {
            input: {
              prompt: prompt,
              aspect_ratio: "16:9",
              output_format: "png",
              output_quality: 95,
            },
          }
        );

        if (Array.isArray(output) && output.length > 0) {
          imageUrls.push(output[0] as string);
        }
      } catch (error) {
        console.error("Error generating asset:", error);
        // Continue with other prompts
      }
    }

    return imageUrls;
  } catch (error) {
    console.error("Error in generateBrandAssets:", error);
    return [];
  }
}

/**
 * Generate brand identity kit (logo + assets)
 * Automatically triggers after creative brief is generated
 * 
 * @param creativeBrief - The generated creative brief
 * @param replicateApiKey - Replicate API key
 * @returns Brand identity kit with logo and assets
 */
export async function generateBrandKit(
  creativeBrief: CreativeBrief
): Promise<BrandIdentityKit> {
  // Call Next.js API route (server-side)
  // API key is now on the backend
  try {
    const response = await fetch('/api/generate-brand-kit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        creativeBrief,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to generate brand kit');
    }

    const data = await response.json();
    return data;
  } catch (error: any) {
    console.error('Error generating brand kit:', error);
    return {
      logoUrl: null,
      assets: [],
      isLoadingLogo: false,
      isLoadingAssets: false,
    };
  }
}

/**
 * Get model provider based on selected model
 */
export function getModelProvider(model: LLMModel) {
  switch (model) {
    case "gpt-4o":
      return "openai";
    case "claude-3-5-sonnet":
      return "anthropic";
    default:
      return "openai";
  }
}

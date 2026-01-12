import { NextRequest, NextResponse } from 'next/server';
import { generateCreativeBrief } from '@/lib/ai';
import type { DiscoveryFormData, LLMModel } from '@/types';

/**
 * API Route: POST /api/generate-creative-brief
 * 
 * Generates a Visual DNA Creative Brief using OpenAI or Anthropic
 */

export async function POST(request: NextRequest) {
  console.log('🚀 [API] /api/generate-creative-brief - Request received');
  
  try {
    const body = await request.json();
    const { formData } = body;

    if (!formData) {
      console.error('❌ [API] Invalid request: formData is required');
      return NextResponse.json(
        { error: 'formData is required' },
        { status: 400 }
      );
    }

    const { businessName, systemInstructions, selectedModel } = formData as DiscoveryFormData;

    if (!businessName || !systemInstructions || !selectedModel) {
      console.error('❌ [API] Invalid request: Missing required fields');
      return NextResponse.json(
        { error: 'businessName, systemInstructions, and selectedModel are required' },
        { status: 400 }
      );
    }

    // Get API key from environment variables (backend)
    const openRouterApiKey = process.env.OPENROUTER_API_KEY;
    
    if (!openRouterApiKey) {
      console.error('❌ [API] OPENROUTER_API_KEY not found in environment');
      return NextResponse.json(
        { error: 'OpenRouter API key not configured on server' },
        { status: 500 }
      );
    }

    console.log('📝 [API] Generating Creative Brief for:', businessName);
    console.log('🤖 [API] Using model:', selectedModel);
    console.log('🔑 [API] OpenRouter API key found in environment');

    console.log('🤖 [API] Calling generateCreativeBrief...');
    const creativeBrief = await generateCreativeBrief(
      formData as DiscoveryFormData,
      selectedModel as LLMModel,
      { openrouter: openRouterApiKey }
    );

    console.log('✅ [API] Creative Brief generated successfully');
    console.log('📊 [API] Visual DNA categories:', Object.keys(creativeBrief.visualDNA));

    return NextResponse.json(creativeBrief);
  } catch (error: any) {
    console.error('❌ [API] Error generating creative brief:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to generate creative brief', details: error.stack },
      { status: 500 }
    );
  }
}

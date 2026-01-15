import { NextRequest, NextResponse } from 'next/server';
import Replicate from 'replicate';

export async function POST(request: NextRequest) {
  try {
    const { creativeBrief } = await request.json();

    // Get Replicate API key from environment variables (backend)
    const replicateApiKey = process.env.REPLICATE_API_TOKEN;
    
    if (!replicateApiKey) {
      console.warn('⚠️ [API] REPLICATE_API_TOKEN not found in environment');
      // Return empty results if no API key (graceful degradation)
      return NextResponse.json({
        logoUrl: null,
        assets: [],
        isLoadingLogo: false,
        isLoadingAssets: false,
      });
    }

    if (!creativeBrief || !creativeBrief.visualDNA) {
      return NextResponse.json(
        { error: 'creativeBrief with visualDNA is required' },
        { status: 400 }
      );
    }

    const replicate = new Replicate({
      auth: replicateApiKey,
    });

    const logoGeometryEssence = creativeBrief.visualDNA.logo_geometry_essence.visual_prompt;
    const photographyCinematicWorld = creativeBrief.visualDNA.photography_cinematic_world.visual_prompt;

    // Generate logo
    let logoUrl: string | null = null;
    try {
      const finalLogoPrompt = `${logoGeometryEssence}, clean, solid flat background, professional logo design, minimalist, high quality`;

      const logoOutput = await replicate.run(
        'black-forest-labs/flux-1.1-pro',
        {
          input: {
            prompt: finalLogoPrompt,
            aspect_ratio: '1:1',
            output_format: 'png',
            output_quality: 95,
          },
        }
      );

      if (Array.isArray(logoOutput) && logoOutput.length > 0) {
        logoUrl = logoOutput[0] as string;
      }
    } catch (error: any) {
      console.error('Error generating logo:', error);
    }

    // Generate assets (4 images)
    const assets: string[] = [];
    const assetPrompts = [
      `${photographyCinematicWorld}, professional brand photography, high quality`,
      `${photographyCinematicWorld}, cinematic brand photography, high quality`,
      `${photographyCinematicWorld}, premium brand mockup, high quality`,
      `${photographyCinematicWorld}, elegant brand photography, high quality`,
    ];

    for (const prompt of assetPrompts) {
      try {
        const output = await replicate.run(
          'black-forest-labs/flux-1.1-pro',
          {
            input: {
              prompt: prompt,
              aspect_ratio: '16:9',
              output_format: 'png',
              output_quality: 95,
            },
          }
        );

        if (Array.isArray(output) && output.length > 0) {
          assets.push(output[0] as string);
        }
      } catch (error: any) {
        console.error('Error generating asset:', error);
        // Continue with other prompts
      }
    }

    return NextResponse.json({
      logoUrl,
      assets,
      isLoadingLogo: false,
      isLoadingAssets: false,
    });
  } catch (error: any) {
    console.error('Error generating brand kit:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to generate brand kit' },
      { status: 500 }
    );
  }
}

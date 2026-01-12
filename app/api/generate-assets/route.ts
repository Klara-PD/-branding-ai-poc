import { NextRequest, NextResponse } from 'next/server';
import Replicate from 'replicate';

export async function POST(request: NextRequest) {
  try {
    const { photographyCinematicWorld, replicateApiKey } = await request.json();

    if (!replicateApiKey) {
      return NextResponse.json(
        { error: 'Replicate API key is required' },
        { status: 400 }
      );
    }

    if (!photographyCinematicWorld) {
      return NextResponse.json(
        { error: 'photographyCinematicWorld object is required' },
        { status: 400 }
      );
    }

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
          imageUrls.push(output[0] as string);
        }
      } catch (error: any) {
        console.error('Error generating asset:', error);
        // Continue with other prompts
      }
    }

    return NextResponse.json({ assets: imageUrls });
  } catch (error: any) {
    console.error('Error in generate-assets:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to generate assets' },
      { status: 500 }
    );
  }
}

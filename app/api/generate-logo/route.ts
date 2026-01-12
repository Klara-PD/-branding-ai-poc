import { NextRequest, NextResponse } from 'next/server';
import Replicate from 'replicate';

export async function POST(request: NextRequest) {
  try {
    const { logoGeometryEssence, replicateApiKey } = await request.json();

    if (!replicateApiKey) {
      return NextResponse.json(
        { error: 'Replicate API key is required' },
        { status: 400 }
      );
    }

    if (!logoGeometryEssence || !Array.isArray(logoGeometryEssence)) {
      return NextResponse.json(
        { error: 'logoGeometryEssence array is required' },
        { status: 400 }
      );
    }

    const replicate = new Replicate({
      auth: replicateApiKey,
    });

    // Create prompt from logo geometry essence descriptors
    const prompt = logoGeometryEssence
      .slice(0, 10) // Use first 10 descriptors
      .join(', ');

    const finalPrompt = `${prompt}, clean, solid flat background, professional logo design, minimalist, high quality`;

    const output = await replicate.run(
      'black-forest-labs/flux-1.1-pro',
      {
        input: {
          prompt: finalPrompt,
          aspect_ratio: '1:1',
          output_format: 'png',
          output_quality: 95,
        },
      }
    );

    // Replicate returns an array of URLs
    if (Array.isArray(output) && output.length > 0) {
      return NextResponse.json({ logoUrl: output[0] });
    }

    return NextResponse.json({ logoUrl: null });
  } catch (error: any) {
    console.error('Error generating logo:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to generate logo' },
      { status: 500 }
    );
  }
}

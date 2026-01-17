import { NextRequest, NextResponse } from 'next/server';
import { join } from 'path';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { existsSync } from 'fs';

/**
 * API Route: POST /api/refine-category
 * 
 * Refines search results for a specific category using vibe steering sliders.
 * 
 * Request body:
 * {
 *   brandBrief: string,
 *   categoryType: 'colors' | 'typography' | 'logo' | 'illustration' | 'photo_model' | 'photo_product' | 'photo_environment',
 *   sliderValues: { [sliderKey: string]: number }, // -1 to 1
 *   originalCategory: string, // e.g., 'brand_color_mood', 'models', etc.
 *   currentImagePath?: string, // Optional: path to current image to use as base for tuning
 * }
 */

export async function POST(request: NextRequest) {
  console.log('🎛️ [API] /api/refine-category - Request received');
  
  try {
    const { brandBrief, categoryType, sliderValues, sliderLabels, sliderTuningMeta, lockedImageIds, originalCategory, currentImagePath, currentImageId } = await request.json();

    if (!brandBrief || typeof brandBrief !== 'string') {
      return NextResponse.json(
        { error: 'brandBrief is required' },
        { status: 400 }
      );
    }

    if (!categoryType || !sliderValues) {
      return NextResponse.json(
        { error: 'categoryType and sliderValues are required' },
        { status: 400 }
      );
    }

    console.log('📝 [API] Category type:', categoryType);
    console.log('🎚️ [API] Slider values:', JSON.stringify(sliderValues));
    console.log('🔍 [API] Request details:', {
      hasCurrentImagePath: !!currentImagePath,
      currentImagePath,
      currentImageId,
      willExclude: !!currentImageId
    });
    if (currentImagePath) {
      console.log('🖼️ [API] Using current image as base:', currentImagePath);
    } else {
      console.log('📝 [API] No image path provided, using brand brief as base');
    }

    // Get environment variables
    const pineconeApiKey = process.env.PINECONE_API_KEY;
    const pineconeIndexName = process.env.PINECONE_INDEX_NAME || 'branding-playground';

    if (!pineconeApiKey) {
      return NextResponse.json(
        { error: 'Pinecone API key not configured' },
        { status: 500 }
      );
    }

    // Create temporary file for brand brief (still needed as fallback)
    const tempDir = join(process.cwd(), 'tmp');
    if (!existsSync(tempDir)) {
      await mkdir(tempDir, { recursive: true });
    }

    const tempFile = join(tempDir, `refine-${categoryType}-${Date.now()}.txt`);
    await writeFile(tempFile, brandBrief, 'utf-8');

    // Prepare slider values as JSON string
    const sliderValuesJson = JSON.stringify(sliderValues);
    
    // Prepare slider labels as JSON string (for dynamic pole generation)
    const sliderLabelsJson = sliderLabels ? JSON.stringify(sliderLabels) : '{}';
    const sliderTuningMetaJson = sliderTuningMeta ? JSON.stringify(sliderTuningMeta) : '{}';
    const lockedImageIdsJson = lockedImageIds ? JSON.stringify(lockedImageIds) : '[]';

    // Resolve image path if provided (convert API path to filesystem path)
    let resolvedImagePath = null;
    if (currentImagePath) {
      // If path starts with /api/images/, convert to actual file path
      if (currentImagePath.startsWith('/api/images/')) {
        const relativePath = currentImagePath.replace('/api/images/', '');
        resolvedImagePath = join(process.cwd(), relativePath);
      } else if (currentImagePath.startsWith('data/')) {
        resolvedImagePath = join(process.cwd(), currentImagePath);
      } else {
        // Assume it's already a full path or relative to project root
        resolvedImagePath = currentImagePath.startsWith('/') 
          ? currentImagePath 
          : join(process.cwd(), currentImagePath);
      }
      
      // Verify image exists
      console.log('🔍 [API] Image path resolution:', {
        originalPath: currentImagePath,
        resolvedPath: resolvedImagePath,
        exists: existsSync(resolvedImagePath)
      });
      if (!existsSync(resolvedImagePath)) {
        console.warn('⚠️ [API] Image path does not exist, falling back to brand brief:', resolvedImagePath);
        resolvedImagePath = null;
      } else {
        console.log('✅ [API] Image path verified, will use image embedding');
      }
    }

    const fastapiUrl = process.env.FASTAPI_URL || 'http://127.0.0.1:8001';
    console.log('🐍 [API] Calling FastAPI for vector-based refinement...');
    if (resolvedImagePath) {
      console.log('🧮 [API] Using image embedding as base vector with slider adjustments');
    } else {
      console.log('🧮 [API] Using brand brief as base vector with slider adjustments');
    }

    console.log('🔍 [API] FastAPI payload ready');

    const response = await fetch(`${fastapiUrl}/refine-category`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brandBrief,
        categoryType,
        sliderValues,
        sliderLabels,
        sliderTuningMeta,
        lockedImageIds: JSON.parse(lockedImageIdsJson),
        currentImagePath: resolvedImagePath ? resolvedImagePath.toString() : null,
        currentImageId,
        indexName: pineconeIndexName,
      }),
    });

    try {
      await unlink(tempFile);
    } catch (err) {
      // Ignore cleanup errors
    }

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      console.error('❌ [API] FastAPI error:', result);
      return NextResponse.json(
        { error: 'Failed to refine search', details: result },
        { status: 500 }
      );
    }

    console.log('✅ [API] Vector-based refinement complete:', result.results?.length || 0, 'results');
    console.log('📊 [API] Top result ID:', result.results?.[0]?.id);
    console.log('📊 [API] Excluded image ID:', currentImageId);
    console.log('📊 [API] Results are different:', result.results?.[0]?.id !== currentImageId);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('❌ [API] Unexpected error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

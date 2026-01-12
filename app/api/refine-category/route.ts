import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { join } from 'path';
import { writeFile, unlink, mkdir, appendFile } from 'fs/promises';
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
    const { brandBrief, categoryType, sliderValues, originalCategory, currentImagePath, currentImageId } = await request.json();

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
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/04912701-0df3-44bf-a263-0763cdbf7869',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'refine-category/route.ts:87',message:'Image path resolution',data:{originalPath:currentImagePath,resolvedPath:resolvedImagePath,pathExists:existsSync(resolvedImagePath)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion
      
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

    // Call Python script for vector-based refinement
    const pythonScript = join(process.cwd(), 'scripts', 'refine_category.py');
    const pythonPath = join(process.cwd(), 'venv', 'bin', 'python3');
    
    console.log('🐍 [API] Calling Python script for vector-based refinement...');
    if (resolvedImagePath) {
      console.log('🧮 [API] Using image embedding as base vector with slider adjustments');
    } else {
      console.log('🧮 [API] Using brand brief as base vector with slider adjustments');
    }

    // Build command arguments: [script, brief_file, category_type, slider_values, api_key, index_name, image_path?, exclude_id?]
    const args = [
      pythonScript, 
      tempFile, 
      categoryType, 
      sliderValuesJson, 
      pineconeApiKey, 
      pineconeIndexName
    ];
    
    if (resolvedImagePath) {
      args.push(resolvedImagePath);
      console.log('📤 [API] Passing image path to Python script:', resolvedImagePath);
    }
    
    // Pass current image ID to exclude from results (if provided)
    if (currentImageId) {
      args.push(currentImageId);
      console.log('📤 [API] Passing image ID to exclude:', currentImageId);
    } else {
      console.log('⚠️ [API] No image ID to exclude - currentImageId is:', currentImageId);
    }
    
    console.log('🔍 [API] Python script arguments count:', args.length);

    return new Promise((resolve) => {
      const python = spawn(
        pythonPath,
        args,
        {
        cwd: process.cwd(),
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
      });

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error('🐍 [PYTHON ERROR]', data.toString().trim());
      });

      python.on('close', async (code) => {
        try {
          await unlink(tempFile);
        } catch (err) {
          // Ignore cleanup errors
        }

        if (code !== 0) {
          console.error('❌ [API] Python script failed with code:', code);
          resolve(
            NextResponse.json(
              { error: 'Failed to refine search', details: stderr },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const result = JSON.parse(stdout);
          console.log('✅ [API] Vector-based refinement complete:', result.results?.length || 0, 'results');
          console.log('📊 [API] Top result ID:', result.results?.[0]?.id);
          console.log('📊 [API] Excluded image ID:', currentImageId);
          console.log('📊 [API] Results are different:', result.results?.[0]?.id !== currentImageId);
          
          // #region agent log - Server-side file logging
          try {
            const logDir = join(process.cwd(), '.cursor');
            const logFile = join(logDir, 'debug.log');
            const logEntry = JSON.stringify({
              location: 'refine-category/route.ts:169',
              message: 'API response prepared',
              data: {
                resultCount: result.results?.length || 0,
                topResultId: result.results?.[0]?.id,
                topResultPath: result.results?.[0]?.metadata?.file_path,
                excludedImageId: currentImageId,
                resultsAreDifferent: result.results?.[0]?.id !== currentImageId,
                categoryType,
                hasImagePath: !!resolvedImagePath,
              },
              timestamp: Date.now(),
              sessionId: 'debug-session',
              runId: 'run2',
              hypothesisId: 'D'
            }) + '\n';
            await appendFile(logFile, logEntry);
          } catch (logErr) {
            // Ignore logging errors
          }
          // #endregion

          // Results are already filtered by category in the Python script
          resolve(NextResponse.json(result));
        } catch (parseError) {
          console.error('❌ [API] Failed to parse Python output:', parseError);
          resolve(
            NextResponse.json(
              { error: 'Failed to parse results', details: stdout },
              { status: 500 }
            )
          );
        }
      });

      python.on('error', async (error) => {
        console.error('❌ [API] Failed to spawn Python process:', error);
        try {
          await unlink(tempFile);
        } catch (err) {
          // Ignore cleanup errors
        }
        resolve(
          NextResponse.json(
            { error: 'Failed to execute Python script', details: error.message },
            { status: 500 }
          )
        );
      });
    });
  } catch (error: any) {
    console.error('❌ [API] Unexpected error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

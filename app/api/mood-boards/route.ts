import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { join } from 'path';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { existsSync } from 'fs';

/**
 * API Route: POST /api/mood-boards
 * 
 * Connection Flow:
 * 1. Frontend (Step1Discovery) calls this endpoint with user's brief
 * 2. This endpoint calls Python script to encode brief with CLIP
 * 3. Python script queries Pinecone with CLIP vector
 * 4. Results returned to frontend
 */

export async function POST(request: NextRequest) {
  console.log('🚀 [API] /api/mood-boards - Request received');
  
  try {
    const { brandBrief, categories } = await request.json();

    if (!brandBrief || typeof brandBrief !== 'string') {
      console.error('❌ [API] Invalid request: brandBrief is required');
      return NextResponse.json(
        { error: 'brandBrief is required' },
        { status: 400 }
      );
    }

    console.log('📝 [API] Brand brief received:', brandBrief.substring(0, 100) + '...');
    console.log('📂 [API] Categories:', categories || 'all');

    // Get environment variables
    const pineconeApiKey = process.env.PINECONE_API_KEY;
    const pineconeIndexName = process.env.PINECONE_INDEX_NAME || 'branding-playground';

    if (!pineconeApiKey) {
      console.error('❌ [API] PINECONE_API_KEY not found in environment');
      return NextResponse.json(
        { error: 'Pinecone API key not configured' },
        { status: 500 }
      );
    }

    console.log('🔑 [API] Pinecone API key found');
    console.log('📊 [API] Pinecone index:', pineconeIndexName);

    // Create temporary file for brief
    const tempDir = join(process.cwd(), 'tmp');
    if (!existsSync(tempDir)) {
      await mkdir(tempDir, { recursive: true });
    }

    const tempFile = join(tempDir, `brief-${Date.now()}.txt`);
    await writeFile(tempFile, brandBrief, 'utf-8');

    console.log('💾 [API] Temporary file created:', tempFile);

    // Call Python script to search Pinecone with CLIP
    const pythonScript = join(process.cwd(), 'scripts', 'search_pinecone.py');
    const pythonPath = join(process.cwd(), 'venv', 'bin', 'python3');
    
    console.log('🐍 [API] Calling Python script:', pythonScript);
    console.log('🔍 [API] CLIP Encoding started...');

    return new Promise((resolve) => {
      const python = spawn(pythonPath, [pythonScript, tempFile, pineconeApiKey, pineconeIndexName], {
        cwd: process.cwd(),
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
      });

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        // Log Python output in real-time
        console.log('🐍 [PYTHON]', output.trim());
      });

      python.stderr.on('data', (data) => {
        const error = data.toString();
        stderr += error;
        console.error('🐍 [PYTHON ERROR]', error.trim());
      });

      python.on('close', async (code) => {
        // Clean up temp file
        try {
          await unlink(tempFile);
        } catch (err) {
          // Ignore cleanup errors
        }

        if (code !== 0) {
          console.error('❌ [API] Python script failed with code:', code);
          console.error('❌ [API] Error output:', stderr);
          resolve(
            NextResponse.json(
              { error: 'Failed to search Pinecone', details: stderr },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const result = JSON.parse(stdout);
          console.log('✅ [API] Pinecone Querying... - Results received');
          console.log('📊 [API] Number of results:', result.results?.length || 0);
          console.log('✅ [API] API Response Sent');

          resolve(NextResponse.json(result));
        } catch (parseError) {
          console.error('❌ [API] Failed to parse Python output:', parseError);
          console.error('❌ [API] Raw output:', stdout);
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

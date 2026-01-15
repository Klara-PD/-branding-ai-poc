import { NextRequest, NextResponse } from 'next/server';
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

    const fastapiUrl = process.env.FASTAPI_URL || 'http://127.0.0.1:8001';
    console.log('🐍 [API] Calling FastAPI:', fastapiUrl);
    console.log('🔍 [API] CLIP Encoding started...');

    const response = await fetch(`${fastapiUrl}/mood-boards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brandBrief,
        indexName: pineconeIndexName,
        topK: 200,
      }),
    });

    // Clean up temp file
    try {
      await unlink(tempFile);
    } catch (err) {
      // Ignore cleanup errors
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('❌ [API] FastAPI error:', errorData);
      return NextResponse.json(
        { error: 'Failed to search Pinecone', details: errorData },
        { status: 500 }
      );
    }

    const result = await response.json();
    console.log('✅ [API] Pinecone Querying... - Results received');
    console.log('📊 [API] Number of results:', result.results?.length || 0);
    console.log('✅ [API] API Response Sent');

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('❌ [API] Unexpected error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

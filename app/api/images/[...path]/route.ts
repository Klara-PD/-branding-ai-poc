import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

/**
 * API Route: GET /api/images/[...path]
 * 
 * Serves images from the data/ directory
 * Security: Only serves files from data/ directory
 */

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params;
    const filePath = path.join('/');
    
    // Security: Only allow files from data/ directory
    if (!filePath.startsWith('data/')) {
      console.error(`[IMAGE API] Invalid path (doesn't start with data/): ${filePath}`);
      return NextResponse.json(
        { error: 'Invalid path' },
        { status: 400 }
      );
    }

    // Prevent directory traversal
    if (filePath.includes('..')) {
      console.error(`[IMAGE API] Invalid path (contains ..): ${filePath}`);
      return NextResponse.json(
        { error: 'Invalid path' },
        { status: 400 }
      );
    }

    const fullPath = join(process.cwd(), filePath);

    // Double check the path is still within data/ directory
    const dataDir = join(process.cwd(), 'data');
    if (!fullPath.startsWith(dataDir)) {
      console.error(`[IMAGE API] Invalid path (outside data dir): ${filePath} -> ${fullPath}`);
      return NextResponse.json(
        { error: 'Invalid path' },
        { status: 400 }
      );
    }

    if (!existsSync(fullPath)) {
      console.error(`[IMAGE API] File not found: ${filePath} -> ${fullPath}`);
      return NextResponse.json(
        { error: 'File not found', path: filePath },
        { status: 404 }
      );
    }

    // Read the image file
    const imageBuffer = await readFile(fullPath);
    
    // Determine content type from file extension
    const ext = filePath.split('.').pop()?.toLowerCase();
    let contentType = 'image/png';
    if (ext === 'jpg' || ext === 'jpeg') contentType = 'image/jpeg';
    else if (ext === 'webp') contentType = 'image/webp';
    else if (ext === 'gif') contentType = 'image/gif';

    return new NextResponse(imageBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    });
  } catch (error: any) {
    console.error('[IMAGE API] Error serving image:', error);
    console.error('[IMAGE API] Error details:', {
      message: error?.message,
      code: error?.code,
      path: error?.path,
      stack: error?.stack,
    });
    return NextResponse.json(
      { error: 'Failed to serve image', details: error?.message },
      { status: 500 }
    );
  }
}

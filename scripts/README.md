# Pinecone Image Upload Script

This script uploads images from the data directory structure to Pinecone vector database using CLIP embeddings.

## Setup

### 1. Install Python Dependencies

```bash
pip install python-dotenv pinecone sentence-transformers tqdm pillow
```

**Dependencies:**
- `python-dotenv` - Load environment variables from .env.local
- `pinecone` - Pinecone Python client (v3+)
- `sentence-transformers` - CLIP model for image embeddings
- `tqdm` - Progress bars
- `pillow` (PIL) - Image processing

### 2. Environment Variables

Make sure your `.env.local` file contains:

```bash
PINECONE_API_KEY=your_api_key_here
PINECONE_INDEX_NAME=branding-playground  # Optional, defaults to "branding-playground"
```

### 3. Add Images to Data Folders

Place your images in the following directories:

- `data/brand_color_mood/`
- `data/typography/`
- `data/logo_geometry/`
- `data/photography/models/`
- `data/photography/products/`
- `data/photography/environments/`
- `data/illustration/`

**Supported image formats:** JPG, JPEG, PNG, WEBP, BMP, TIFF, TIF

### 4. Run the Script

```bash
python3 scripts/upload_to_pinecone.py
```

Or make it executable and run directly:

```bash
chmod +x scripts/upload_to_pinecone.py
./scripts/upload_to_pinecone.py
```

## Features

- **MD5 Deduplication**: Uses MD5 hashing to prevent duplicate uploads
- **CLIP Embeddings**: Uses `clip-ViT-B-32` model to generate 512-dimension embeddings
- **Progress Tracking**: Shows progress bars for processing and uploading
- **Metadata**: Includes `file_path`, `category`, `filename`, and `md5_hash` in metadata
- **Batch Upload**: Uploads vectors in batches of 100 for efficiency
- **Error Handling**: Robust error handling and informative messages

## Output

The script will:
1. Scan all data directories for images
2. Generate CLIP embeddings for each image
3. Check for duplicates using MD5 hashes
4. Upload vectors to Pinecone with metadata
5. Display final statistics

## Notes

- The script automatically creates the Pinecone index if it doesn't exist
- Index dimension is set to 512 (CLIP-ViT-B-32 embedding size)
- Uses cosine similarity metric
- Serverless deployment on AWS us-east-1

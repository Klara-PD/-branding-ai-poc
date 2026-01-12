# Branding AI POC - System Status Audit

**Last Updated:** January 2025  
**Project:** Branding Playground POC - Multi-step Brand Identity Generation Tool

---

## 1. Current State

### 1.1 Backend Architecture

#### **Next.js API Routes** (Not FastAPI)
The backend uses **Next.js API Routes** (serverless functions), not FastAPI:

- **`/api/generate-creative-brief`** (`app/api/generate-creative-brief/route.ts`)
  - Generates Visual DNA Creative Brief using OpenRouter API (GPT-4o or Claude 3.5 Sonnet)
  - Reads `OPENROUTER_API_KEY` from `.env.local`
  - Returns `CreativeBrief` with `VisualDNA` structure

- **`/api/mood-boards`** (`app/api/mood-boards/route.ts`)
  - Searches Pinecone vector database for inspiration images
  - Calls Python script (`scripts/search_pinecone.py`) with CLIP encoding
  - Reads `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` from `.env.local`
  - Returns top 200 results with metadata (file_path, category, filename, md5_hash)

- **`/api/generate-brand-kit`** (`app/api/generate-brand-kit/route.ts`)
  - Generates logo and brand assets using Replicate API (flux-1.1-pro model)
  - Reads `REPLICATE_API_TOKEN` from `.env.local`
  - Returns `BrandIdentityKit` with logoUrl and assets array

- **`/api/images/[...path]`** (`app/api/images/[...path]/route.ts`)
  - Serves static image files from `data/` directory
  - Security: Only allows files from `data/` directory
  - Returns image buffers with proper Content-Type headers

#### **Python Scripts** (Not FastAPI Server)

- **`scripts/upload_to_pinecone.py`**
  - Uploads images from `data/` folders to Pinecone vector database
  - Uses CLIP model (`clip-ViT-B-32`) for 512-dim embeddings
  - Stores metadata: `file_path`, `category`, `filename`, `md5_hash`
  - For `brand_color_mood` category: Also extracts/stores `hex_codes` and `contrast_rating`

- **`scripts/search_pinecone.py`**
  - Called by `/api/mood-boards` route
  - Encodes search query with CLIP
  - Queries Pinecone and returns top 200 results with metadata

#### **Pinecone Vector Database**

- **Index Name:** `brandpoc` (configurable via `PINECONE_INDEX_NAME` in `.env.local`)
- **Embedding Model:** CLIP-ViT-B-32 (512 dimensions)
- **Metadata Stored:**
  - `file_path`: Relative path from project root (e.g., `data/brand_color_mood/image.png`)
  - `category`: One of: `brand_color_mood`, `typography`, `logo_geometry`, `illustration`, `photography/models`, `photography/products`, `photography/environments`
  - `filename`: Image filename
  - `md5_hash`: MD5 hash for deduplication
  - `hex_codes`: Array of hex color codes (only for `brand_color_mood` category)
  - `contrast_rating`: Contrast rating (only for `brand_color_mood` category)

### 1.2 Frontend Architecture

#### **Step 1: Discovery** (`components/steps/Step1Discovery.tsx`)
- ✅ User input: Single "Brand Brief" textarea
- ✅ Model selector: GPT-4o or Claude 3.5 Sonnet (via OpenRouter)
- ✅ Calls `/api/generate-creative-brief`
- ✅ Stores `CreativeBrief` in context

#### **Step 2: The Brief** (`components/steps/Step2CreativeBrief.tsx`)
- ✅ Displays Visual DNA structure:
  - Brand Color Mood
  - Typography Voice
  - Logo Geometry Essence
  - Photography Cinematic World (Backgrounds, Models, Products, Lighting)
  - Illustration Style Medium
- ✅ Shows descriptors and "Avoid" keywords

#### **Step 3: Inspiration** (`components/steps/Step3Inspiration.tsx`)
- ✅ Fetches inspiration images from `/api/mood-boards`
- ✅ Groups results by category (strict matching)
- ✅ Displays images:
  - **Color**: 1 image
  - **Typography**: 1 image (expected to be empty - folder is empty)
  - **Logo**: 1 image
  - **Illustration**: 1 image
  - **Photography**:
    - Environment: 1 image
    - Product: 1 image
    - Model: 1-4 images
- ✅ Images served via `/api/images/[...path]` route
- ⚠️ **Missing**: Hex codes from color images are NOT displayed or passed to Step 4

#### **Step 4: Brand Identity Kit** (`components/steps/Step4BrandKit.tsx`)
- ✅ Auto-triggers generation when `creativeBrief` is available
- ✅ Calls `/api/generate-brand-kit` (which uses Replicate API)
- ✅ Displays:
  - Primary Brand Logo (generated via Replicate)
  - Brand Assets Gallery (4 images, generated via Replicate)
- ⚠️ **Missing**: Color palette from Step 3 hex codes
- ⚠️ **Missing**: Typography samples
- ⚠️ **Missing**: Connection to Step 3 inspiration results

### 1.3 Data Structure

#### **Types** (`types/index.ts`)

```typescript
interface DiscoveryFormData {
  businessName: string;
  brandBrief: string;
  systemInstructions: string;
  selectedModel: LLMModel;
}

interface VisualDNA {
  brand_color_mood: { descriptors: string[]; avoid: string[]; };
  typography_voice: { descriptors: string[]; avoid: string[]; };
  logo_geometry_essence: { descriptors: string[]; avoid: string[]; };
  photography_cinematic_world: {
    backgrounds: string[]; models: string[]; products: string[]; lighting: string[]; avoid: string[];
  };
  illustration_style_medium: { descriptors: string[]; avoid: string[]; };
}

interface CreativeBrief {
  visualDNA: VisualDNA;
}

interface BrandIdentityKit {
  logoUrl: string | null;
  assets: string[];
  isLoadingLogo: boolean;
  isLoadingAssets: boolean;
}
```

**⚠️ Missing Types:**
- No type for color palette (hex codes)
- No type for storing Step 3 inspiration results with hex codes
- No connection between Step 3 results and Step 4 brand kit

---

## 2. Data Flow

### 2.1 Image Upload Flow (data/ → Pinecone)

```
1. Images placed in data/ folders:
   - data/brand_color_mood/
   - data/typography/
   - data/logo_geometry/
   - data/photography/models/
   - data/photography/products/
   - data/photography/environments/
   - data/illustration/

2. Run: python3 scripts/upload_to_pinecone.py

3. Upload script process:
   a. Scans data/ folders for images
   b. Generates CLIP embeddings (512-dim vectors) using clip-ViT-B-32
   c. For brand_color_mood images:
      - Attempts to match with color_palettes_tagged.json (if available)
      - Extracts hex_codes and contrast_rating
      - Falls back to extracting dominant colors from image if no JSON match
   d. Creates metadata object:
      {
        file_path: "data/brand_color_mood/image.png",
        category: "brand_color_mood",
        filename: "image.png",
        md5_hash: "...",
        hex_codes: ["#FF0000", "#00FF00", ...],  // Only for brand_color_mood
        contrast_rating: "AAA"  // Only for brand_color_mood
      }
   e. Uploads vector to Pinecone with metadata

4. Result: Images are searchable in Pinecone with CLIP embeddings
```

### 2.2 Image Retrieval Flow (Pinecone → UI)

```
1. User completes Step 1 → Creative Brief generated with VisualDNA

2. Step 3 loads → Fetches inspiration images:
   a. Frontend: components/steps/Step3Inspiration.tsx
   b. Calls: POST /api/mood-boards
      Body: { brandBrief: "combined descriptors from VisualDNA" }
   
3. Backend: /api/mood-boards route:
   a. Creates temporary file with search query
   b. Spawns: python3 scripts/search_pinecone.py <brief_file> <api_key> <index_name>
   
4. Python script (search_pinecone.py):
   a. Loads CLIP model (clip-ViT-B-32)
   b. Encodes search query text → 512-dim vector
   c. Queries Pinecone: index.query(vector=query_vector, top_k=200, include_metadata=True)
   d. Returns JSON with results array:
      {
        results: [
          {
            id: "...",
            score: 0.95,
            metadata: {
              file_path: "data/brand_color_mood/image.png",
              category: "brand_color_mood",
              filename: "image.png",
              hex_codes: ["#FF0000", "#00FF00", ...],  // Present but NOT used
              contrast_rating: "AAA"  // Present but NOT used
            }
          },
          ...
        ],
        count: 200
      }
   
5. Frontend receives results:
   a. Groups results by category (strict matching)
   b. Limits images per category (1 for Color/Logo/Illustration, 1 for Environment/Product, 4 for Model)
   c. For each image, generates URL: /api/images/${file_path}
   d. Displays images in UI
   
6. Image serving:
   a. Browser requests: GET /api/images/data/brand_color_mood/image.png
   b. API route reads file from filesystem
   c. Returns image buffer with Content-Type header
```

### 2.3 Current Gap: Hex Codes Not Used

**⚠️ Critical Issue:** 
- Hex codes are extracted and stored in Pinecone metadata
- Hex codes are returned in Step 3 API response
- **BUT:** Hex codes are NOT:
  - Displayed in Step 3 UI
  - Passed to Step 4
  - Used in brand kit generation

**Current Code:**
- `Step3Inspiration.tsx` receives `hex_codes` in `result.metadata.hex_codes`
- But the component doesn't read or display them
- No connection between Step 3 results and Step 4

---

## 3. Pending Tasks

### 3.1 Step 4 Integration with Step 3 Data

#### **Priority: HIGH**

**Missing Features:**

1. **Color Palette Display** (Step 4)
   - Extract hex codes from Step 3 Color inspiration results
   - Display color palette/swatches in Step 4
   - Show hex codes, color names (optional), and contrast ratings

2. **Typography Samples** (Step 4)
   - Currently: Step 4 doesn't display typography
   - Needed: Typography samples based on Step 2 VisualDNA descriptors
   - Could use: Google Fonts API or custom font rendering

3. **Connection Between Steps**
   - Currently: Step 3 and Step 4 are disconnected
   - Needed: Pass Step 3 inspiration results (especially color hex codes) to Step 4
   - Solution: Store Step 3 results in context or pass via props

4. **Brand Kit Enhancement**
   - Currently: Only shows logo and 4 asset images (generated via Replicate)
   - Needed: 
     - Color palette section
     - Typography section
     - Logo variations (if applicable)
     - Brand guidelines summary

### 3.2 Step 3 Enhancements

#### **Priority: MEDIUM**

1. **Display Hex Codes** (Step 3 - Color section)
   - Show color swatches with hex codes
   - Display contrast ratings
   - Allow user to view/select colors

2. **Export Functionality**
   - Allow users to export inspiration images
   - Export color palette as CSS/JSON

### 3.3 Data Flow Improvements

#### **Priority: LOW**

1. **Caching**
   - Cache Pinecone search results
   - Cache image files (currently served fresh each time)

2. **Error Handling**
   - Better error messages for missing images
   - Fallback images for empty categories

3. **Performance**
   - Optimize image loading (lazy loading, thumbnails)
   - Batch image requests

---

## 4. Next Technical Steps

### **Recommended Priority Order:**

#### **Step 1: Extract and Store Hex Codes from Step 3** (IMMEDIATE)
1. Update `Step3Inspiration.tsx` to:
   - Extract `hex_codes` from Color category results
   - Store hex codes in state or context
   - Display color swatches in Step 3 (optional but recommended)

2. Update `BrandingContext` to:
   - Store Step 3 inspiration results (including hex codes)
   - Make hex codes available to Step 4

#### **Step 2: Display Color Palette in Step 4** (HIGH PRIORITY)
1. Update `Step4BrandKit.tsx` to:
   - Read hex codes from context (from Step 3)
   - Display color palette section with swatches
   - Show hex codes and contrast ratings

2. Create color palette component:
   - Color swatch grid
   - Hex code labels
   - Copy-to-clipboard functionality

#### **Step 3: Add Typography Section to Step 4** (HIGH PRIORITY)
1. Map Step 2 VisualDNA typography descriptors to fonts:
   - Use Google Fonts API or font matching logic
   - Display typography samples

2. Add typography section to Step 4:
   - Font family display
   - Sample text rendering
   - Font weights/styles

#### **Step 4: Enhanced Brand Kit Layout** (MEDIUM PRIORITY)
1. Redesign Step 4 layout:
   - Color Palette section
   - Typography section
   - Logo section (existing)
   - Assets section (existing)
   - Brand Guidelines summary

---

## 5. Environment Configuration

### **Required Environment Variables** (`.env.local`)

```bash
# OpenRouter API (for Creative Brief generation)
OPENROUTER_API_KEY=sk-or-v1-...

# Pinecone (for image search)
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=brandpoc

# Replicate (for logo/asset generation)
REPLICATE_API_TOKEN=r8_...
```

### **Data Folders**

```
data/
├── brand_color_mood/     (779 images)
├── typography/            (0 images - empty)
├── logo_geometry/         (1,082 images)
├── illustration/          (245 images)
└── photography/
    ├── models/            (331 images)
    ├── products/          (32 images)
    └── environments/      (276 images)
```

### **Dependencies**

**Node.js:**
- Next.js 16.1.1
- React 19.2.3
- Vercel AI SDK
- Framer Motion
- Shadcn UI components

**Python:**
- python-dotenv
- pinecone (v3+)
- sentence-transformers (CLIP model)
- tqdm
- pillow (PIL)

---

## 6. Technical Debt & Notes

1. **No FastAPI:** The user mentioned FastAPI, but the project uses Next.js API Routes (serverless functions). Python scripts are called via `spawn`, not as a FastAPI server.

2. **Color Metadata:** Hex codes are extracted and stored but not currently used in the UI. This is the main gap to address.

3. **Step 3 → Step 4 Connection:** Steps are currently disconnected. Need to pass data via context or state management.

4. **Typography Folder:** Empty (0 images). Step 3 correctly shows empty state. Step 4 should handle typography differently (using fonts, not images).

5. **Image Serving:** Currently serves images directly from filesystem. Could be optimized with CDN or caching layer.

---

## 7. Summary

**What Works:**
- ✅ Step 1: Creative Brief generation (OpenRouter)
- ✅ Step 2: Visual DNA display
- ✅ Step 3: Inspiration images from Pinecone (with fallback logic)
- ✅ Step 4: Logo and asset generation (Replicate)
- ✅ Image upload to Pinecone with CLIP embeddings
- ✅ Image serving from `data/` directory
- ✅ Color hex codes extraction and storage in Pinecone

**What's Missing:**
- ⚠️ Hex codes display in Step 3
- ⚠️ Hex codes passed to Step 4
- ⚠️ Color palette display in Step 4
- ⚠️ Typography section in Step 4
- ⚠️ Connection between Step 3 results and Step 4 brand kit

**Next Immediate Step:**
Extract hex codes from Step 3 Color results and store them in context, then display them in Step 4 as a color palette section.

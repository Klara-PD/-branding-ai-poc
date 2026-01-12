# Connection Flow: Frontend → Backend → CLIP → Pinecone

This document explains how the frontend connects to the backend, and how the backend uses CLIP to query Pinecone.

## 🔗 Connection Points

### 1. **Frontend → Backend API** (Step 1 Discovery)

**File:** `components/steps/Step1Discovery.tsx`

**Connection Point:**
- **Location:** `handleSubmit` function (line ~32)
- **Action:** When user clicks "Generate Creative Brief" button
- **Method:** `POST /api/mood-boards`
- **Request Body:**
  ```json
  {
    "brandBrief": "User's brand brief text..."
  }
  ```

**Code:**
```typescript
const response = await fetch('/api/mood-boards', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ brandBrief: brandBrief.trim() }),
});
```

**Logging:**
- `console.log('🌐 [FRONTEND] Calling POST /api/mood-boards...')`
- `console.log('✅ [FRONTEND] API response received...')`

**Network Tab:**
- You should see `POST /api/mood-boards` in the Network tab with status "pending" while the request is in progress

---

### 2. **Backend API → Python Script** (Next.js API Route)

**File:** `app/api/mood-boards/route.ts`

**Connection Point:**
- **Location:** `POST` handler function (line ~17)
- **Action:** Receives request from frontend, spawns Python process
- **Method:** Spawns Python subprocess with `spawn(pythonPath, [pythonScript, tempFile, apiKey, indexName])`

**Code:**
```typescript
const python = spawn(pythonPath, [
  'scripts/search_pinecone.py',
  tempFile,           // Path to temporary file containing brief
  pineconeApiKey,     // Pinecone API key
  pineconeIndexName,  // Pinecone index name
]);
```

**Logging:**
- `console.log('🚀 [API] /api/mood-boards - Request received')`
- `console.log('🔍 [API] CLIP Encoding started...')`
- `console.log('🐍 [API] Calling Python script...')`
- `console.log('✅ [API] Pinecone Querying... - Results received')`
- `console.log('✅ [API] API Response Sent')`

**Terminal Output:**
- All logging appears in the Next.js dev server terminal
- Python script output is captured and logged in real-time

---

### 3. **Python Script → CLIP Model** (CLIP Encoding)

**File:** `scripts/search_pinecone.py`

**Connection Point:**
- **Location:** `main()` function (line ~27)
- **Action:** Loads CLIP model and encodes the brief text
- **Method:** `SentenceTransformer('clip-ViT-B-32')` and `model.encode(brand_brief)`

**Code:**
```python
model = SentenceTransformer('clip-ViT-B-32')
query_vector = model.encode(brand_brief, convert_to_numpy=True).tolist()
```

**Logging:**
- `print("🔍 CLIP Encoding started", flush=True)`
- `print("🤖 Loading CLIP model (clip-ViT-B-32)...", flush=True)`
- `print("✅ CLIP model loaded", flush=True)`
- `print("🔢 Encoding brief with CLIP...", flush=True)`
- `print(f"✅ CLIP encoding complete: {len(query_vector)} dimensions", flush=True)`

**Terminal Output:**
- Appears in Next.js dev server terminal (captured from Python stdout)

---

### 4. **Python Script → Pinecone** (Vector Query)

**File:** `scripts/search_pinecone.py`

**Connection Point:**
- **Location:** `main()` function (line ~77)
- **Action:** Queries Pinecone with the CLIP-encoded vector
- **Method:** `index.query(vector=query_vector, top_k=20, include_metadata=True)`

**Code:**
```python
pc = Pinecone(api_key=api_key)
index = pc.Index(index_name)
results = index.query(
    vector=query_vector,
    top_k=20,
    include_metadata=True
)
```

**Logging:**
- `print("🌲 Connecting to Pinecone...", flush=True)`
- `print(f"✅ Connected to Pinecone index: {index_name}", flush=True)`
- `print("🔍 Pinecone Querying...", flush=True)`
- `print(f"✅ Query complete: {len(results.matches)} results found", flush=True)`

**Terminal Output:**
- Appears in Next.js dev server terminal (captured from Python stdout)

---

### 5. **Backend API → Frontend** (Response)

**File:** `app/api/mood-boards/route.ts`

**Connection Point:**
- **Location:** `POST` handler function (line ~90-100)
- **Action:** Returns JSON response to frontend
- **Method:** `NextResponse.json(result)`

**Code:**
```typescript
const result = JSON.parse(stdout);
resolve(NextResponse.json(result));
```

**Response Format:**
```json
{
  "results": [
    {
      "id": "vector-id-123",
      "score": 0.85,
      "metadata": {
        "file_path": "data/logo_geometry/image.png",
        "category": "logo_geometry",
        "filename": "image.png",
        "md5_hash": "abc123..."
      }
    },
    ...
  ],
  "count": 20
}
```

**Logging:**
- `console.log('📊 [API] Number of results:', result.results?.length || 0)`
- `console.log('✅ [API] API Response Sent')`

---

## 📊 Complete Flow Diagram

```
User clicks "Generate Creative Brief" (Step 1)
    ↓
[FRONTEND] POST /api/mood-boards
    ↓ console.log('🌐 [FRONTEND] Calling POST...')
    ↓
[API ROUTE] Receives request
    ↓ console.log('🚀 [API] Request received')
    ↓ console.log('🔍 [API] CLIP Encoding started...')
    ↓
[API ROUTE] Spawns Python subprocess
    ↓ console.log('🐍 [API] Calling Python script...')
    ↓
[PYTHON] Loads CLIP model
    ↓ print("🤖 Loading CLIP model...")
    ↓ print("✅ CLIP model loaded")
    ↓
[PYTHON] Encodes brief with CLIP
    ↓ print("🔢 Encoding brief with CLIP...")
    ↓ print("✅ CLIP encoding complete: 512 dimensions")
    ↓
[PYTHON] Connects to Pinecone
    ↓ print("🌲 Connecting to Pinecone...")
    ↓ print("✅ Connected to Pinecone index")
    ↓
[PYTHON] Queries Pinecone
    ↓ print("🔍 Pinecone Querying...")
    ↓ print("✅ Query complete: 20 results found")
    ↓
[PYTHON] Returns JSON to stdout
    ↓
[API ROUTE] Parses JSON from Python
    ↓ console.log('✅ [API] Pinecone Querying... - Results received')
    ↓ console.log('📊 [API] Number of results: 20')
    ↓
[API ROUTE] Returns JSON to frontend
    ↓ console.log('✅ [API] API Response Sent')
    ↓
[FRONTEND] Receives response
    ↓ console.log('✅ [FRONTEND] API response received')
    ↓
User sees results (or proceeds to next step)
```

---

## 🔍 How to Verify It's Working

1. **Frontend Network Tab:**
   - Open browser DevTools → Network tab
   - Click "Generate Creative Brief" button
   - Look for `POST /api/mood-boards` request
   - Status should show "pending" while processing, then "200" when complete

2. **Backend Terminal:**
   - Check Next.js dev server terminal
   - You should see logs like:
     ```
     🚀 [API] /api/mood-boards - Request received
     🔍 [API] CLIP Encoding started...
     🐍 [API] Calling Python script...
     🔍 CLIP Encoding started
     🤖 Loading CLIP model (clip-ViT-B-32)...
     ✅ CLIP model loaded
     🔢 Encoding brief with CLIP...
     ✅ CLIP encoding complete: 512 dimensions
     🌲 Connecting to Pinecone...
     ✅ Connected to Pinecone index: branding-playground
     🔍 Pinecone Querying...
     ✅ Query complete: 20 results found
     ✅ [API] Pinecone Querying... - Results received
     📊 [API] Number of results: 20
     ✅ [API] API Response Sent
     ```

3. **Frontend Console:**
   - Open browser DevTools → Console tab
   - You should see logs like:
     ```
     🌐 [FRONTEND] Calling POST /api/mood-boards with brief: ...
     ✅ [FRONTEND] API response received
     📊 [FRONTEND] Number of results: 20
     ```

---

## 🐛 Troubleshooting

### Issue: No network request in Network tab
- **Check:** Is the button click handler calling `fetch()`?
- **Fix:** Verify `handleSubmit` is async and calls `fetch('/api/mood-boards')`

### Issue: API route returns 500 error
- **Check:** Is Python script executable? Does it have correct imports?
- **Fix:** Run `chmod +x scripts/search_pinecone.py` and verify Python dependencies

### Issue: No CLIP encoding logs
- **Check:** Is Python script being called? Is `sentence-transformers` installed?
- **Fix:** Check Python venv is activated and dependencies are installed

### Issue: No Pinecone query logs
- **Check:** Is `PINECONE_API_KEY` set? Is Pinecone index name correct?
- **Fix:** Verify `.env.local` has `PINECONE_API_KEY` and `PINECONE_INDEX_NAME`

### Issue: Results are empty
- **Check:** Is Pinecone index populated? Are vectors the correct dimensions?
- **Fix:** Run `scripts/upload_to_pinecone.py` to populate the index

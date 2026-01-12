# Branding Playground POC

A multi-step Next.js application for generating complete Brand Identity Kits based on business inputs. Built with Tailwind CSS, Shadcn UI, and Framer Motion.

## Features

- **Step 1 (Discovery)**: Input form for business details (name, location, target audience, style description) with AI model selector
- **Step 2 (The Brief)**: AI-generated creative brief with Brand Voice, Visual Language, and Core Values
- **Step 3 (Inspiration)**: 3-column gallery layout for Color & Texture, Logo & Marks, and Visual Photography (ready for Pinecone integration)
- **Step 4 (Brand Identity Kit)**: Professional Bento Grid layout displaying:
  - Primary Logo
  - Color Palette with hex codes
  - Typography samples
  - Brand in Action mockups (App, Packaging, Stationery)

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Styling**: Tailwind CSS v4
- **UI Components**: Shadcn UI
- **Animations**: Framer Motion
- **AI SDK**: Vercel AI SDK (structure ready for OpenAI, Anthropic, Replicate)
- **Language**: TypeScript

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Run the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
branding-ai-poc/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main page with step navigation
│   └── globals.css         # Global styles
├── components/
│   ├── steps/
│   │   ├── Step1Discovery.tsx      # Discovery form
│   │   ├── Step2CreativeBrief.tsx  # Creative brief display
│   │   ├── Step3Inspiration.tsx    # Inspiration gallery
│   │   └── Step4BrandKit.tsx       # Brand identity kit (Bento Grid)
│   ├── ui/                 # Shadcn UI components
│   ├── SettingsModal.tsx   # API keys settings
│   └── StepIndicator.tsx   # Step progress indicator
├── context/
│   └── BrandingContext.tsx # Global state management
├── lib/
│   ├── ai.ts              # AI SDK structure (ready for integration)
│   ├── mockData.ts        # Mock data for testing
│   └── utils.ts           # Utility functions
└── types/
    └── index.ts           # TypeScript types
```

## Current Implementation

The application currently uses **mock data** to demonstrate the full workflow. All steps are functional and the UI is complete.

### Mock Data Flow

1. **Step 1**: User fills out the discovery form and selects an AI model
2. **Step 2**: Displays a mock creative brief (stored in `lib/mockData.ts`)
3. **Step 3**: Shows placeholder galleries for inspiration sections
4. **Step 4**: Displays a complete mock brand identity kit

## Integrating Real AI APIs

To integrate real AI APIs:

1. **Add API Keys**: Click the Settings icon (⚙️) in the top right and enter your API keys for:
   - OpenAI (for GPT-4o)
   - Anthropic (for Claude 3.5 Sonnet)
   - Replicate (for image generation)

2. **Update AI Functions**: Edit `lib/ai.ts`:
   - Uncomment the AI SDK imports
   - Replace mock functions with actual API calls
   - Use the API keys from context: `useBranding().apiKeys`

3. **Example Integration**:
   ```typescript
   // In lib/ai.ts
   import { openai } from '@ai-sdk/openai';
   import { generateText } from 'ai';
   
   export async function generateCreativeBrief(...) {
     if (model === 'gpt-4o' && apiKeys.openai) {
       const { text } = await generateText({
         model: openai('gpt-4o', { apiKey: apiKeys.openai }),
         prompt: `Generate a creative brief for: ${formData.businessName}...`,
       });
       // Parse and return the brief
     }
   }
   ```

## Future Integrations

- **Pinecone Integration**: Connect Step 3 inspiration galleries to custom CLIP-based Pinecone indexes
- **Logo Generation**: Integrate image generation models (e.g., via Replicate) for logo creation
- **Color Extraction**: Automatically extract color palettes from style descriptions
- **Typography Recommendations**: AI-powered font pairing suggestions

## Development

- **Build**: `npm run build`
- **Start**: `npm start`
- **Lint**: `npm run lint`

## Design Notes

The final output (Step 4) features a professional "Bento Grid" layout with:
- Clean, minimalist boxes
- Sophisticated fashion-tech aesthetic
- Professional spacing and typography
- Ready for high-end design studio presentation

## License

MIT

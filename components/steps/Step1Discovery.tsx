"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useBranding } from "@/context/BrandingContext";
import type { DiscoveryFormData, LLMModel } from "@/types";
import { DEFAULT_SYSTEM_INSTRUCTIONS } from "@/lib/constants";
import { Loader2 } from "lucide-react";

export function Step1Discovery() {
  const { setFormData, setCurrentStep, setCreativeBrief } = useBranding();
  const [brandBrief, setBrandBrief] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<DiscoveryFormData>({
    businessName: "",
    location: "",
    targetAudience: "",
    styleDescription: "",
    systemInstructions: DEFAULT_SYSTEM_INSTRUCTIONS,
    selectedModel: "gpt-4o",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!brandBrief.trim()) {
      return;
    }

    setIsLoading(true);
    
    // Extract business name from brief (first line or use placeholder)
    const lines = brandBrief.trim().split('\n').filter(l => l.trim());
    const businessName = lines[0]?.trim() || "Brand";
    
    // Combine everything into the styleDescription and other fields
    const formData: DiscoveryFormData = {
      businessName: businessName,
      location: "", // Can be extracted from brief later if needed
      targetAudience: brandBrief, // Use full brief
      styleDescription: brandBrief, // Use full brief
      systemInstructions: data.systemInstructions,
      selectedModel: data.selectedModel,
    };
    
    setFormData(formData);

    // CONNECTION POINT: Frontend → Backend API
    // Call /api/generate-creative-brief to generate Creative Brief using OpenAI/Anthropic
    try {
      console.log('🌐 [FRONTEND] Calling POST /api/generate-creative-brief');
      console.log('📝 [FRONTEND] Model:', data.selectedModel);
      console.log('📝 [FRONTEND] Business:', businessName);
      // API keys are now on the backend - no need to pass them
      const response = await fetch('/api/generate-creative-brief', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          formData: formData,
        }),
      });

      console.log('📡 [FRONTEND] Response status:', response.status, response.statusText);

      if (!response.ok) {
        // Try to get error text first
        const errorText = await response.text();
        console.error('❌ [FRONTEND] API error response text:', errorText);
        
        let error;
        try {
          error = JSON.parse(errorText);
        } catch (parseError) {
          // If JSON parse fails, use the raw text
          error = { error: errorText || `HTTP ${response.status}: ${response.statusText}` };
        }
        
        console.error('❌ [FRONTEND] API error object:', error);
        throw new Error(error.error || error.message || `Failed to generate creative brief (${response.status})`);
      }

      const creativeBrief = await response.json();
      console.log('✅ [FRONTEND] Creative Brief received:', creativeBrief);
      console.log('📊 [FRONTEND] Visual DNA categories:', Object.keys(creativeBrief.visualDNA || {}));
      
      // Store the generated Creative Brief in context
      setCreativeBrief(creativeBrief);
    } catch (error: any) {
      console.error('❌ [FRONTEND] Failed to generate creative brief:', error);
      console.error('❌ [FRONTEND] Error details:', {
        message: error?.message,
        name: error?.name,
        stack: error?.stack,
      });
      // Don't proceed to next step if API call fails
      // User needs to add API key first
      alert(`Error: ${error.message}\n\nPlease add your API key in Settings (⚙️ icon).`);
      setIsLoading(false);
      return; // Stop here, don't go to Step 2
    }
    
    setIsLoading(false);
    setCurrentStep(2);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-2xl mx-auto space-y-8"
    >
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Discovery</h1>
        <p className="text-muted-foreground text-lg">
          Tell us about your business to begin crafting your brand identity
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="brandBrief">Brand Brief *</Label>
          <Textarea
            id="brandBrief"
            placeholder="Tell us about your brand... Include your business name, location, target audience, style description, and any other relevant details."
            value={brandBrief}
            onChange={(e) => setBrandBrief(e.target.value)}
            required
            rows={10}
            className="resize-none"
          />
          <p className="text-sm text-muted-foreground">
            Describe your business, target audience, location, style, and vision. The more detail you provide, the better we can craft your brand identity.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="systemInstructions">System Instructions *</Label>
          <Textarea
            id="systemInstructions"
            value={data.systemInstructions}
            onChange={(e) =>
              setData({ ...data, systemInstructions: e.target.value })
            }
            required
            rows={8}
            className="resize-none font-mono text-sm"
          />
          <p className="text-sm text-muted-foreground">
            Instructions for the AI model. This will be passed as the system message.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="model">AI Model *</Label>
          <Select
            value={data.selectedModel}
            onValueChange={(value: LLMModel) =>
              setData({ ...data, selectedModel: value })
            }
          >
            <SelectTrigger id="model" className="h-12">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt-4o">GPT-4o (OpenAI)</SelectItem>
              <SelectItem value="claude-3-5-sonnet">
                Claude 3.5 Sonnet (Anthropic)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button 
          type="submit" 
          size="lg" 
          className="w-full h-12 text-base"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            'Generate Creative Brief'
          )}
        </Button>
      </form>
    </motion.div>
  );
}

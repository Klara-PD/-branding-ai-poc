"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBranding } from "@/context/BrandingContext";
import { ImageIcon, Loader2, Sliders } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { CATEGORY_SLIDERS, CATEGORY_TYPE_MAP, type SliderConfig } from "@/lib/vibeSteering";

const inspirationSections = [
  {
    title: "Color",
    subtitle: "Brand Color Mood",
    category: "brand_color_mood",
    placeholder: "Visual references for color palettes and emotional temperature",
    imageCount: 1, // Only 1 image
  },
  {
    title: "Typography",
    subtitle: "Typography Voice",
    category: "typography",
    placeholder: "Letterform styles and typographic references",
    imageCount: 1, // Only 1 image
  },
  {
    title: "Logo",
    subtitle: "Logo Geometry Essence",
    category: "logo_geometry",
    placeholder: "Logo concepts and brand mark inspirations",
    imageCount: 1, // Only 1 image
  },
  {
    title: "Illustration",
    subtitle: "Illustration Style Medium",
    category: "illustration",
    placeholder: "Illustration techniques and artistic references",
    imageCount: 1, // Only 1 image
  },
];

const photographySubsections = [
  {
    title: "Environment",
    category: "environments",
    imageCount: 1, // Only 1 image
  },
  {
    title: "Product",
    category: "products",
    imageCount: 1, // Only 1 image
  },
  {
    title: "Model",
    category: "models",
    imageCount: 4, // 1-4 images
  },
];

interface InspirationResult {
  id: string;
  score: number;
  metadata: {
    file_path?: string;
    category?: string;
    filename?: string;
    [key: string]: any;
  };
}

export function Step3Inspiration() {
  const { setCurrentStep, creativeBrief, formData } = useBranding();
  const [results, setResults] = useState<Record<string, InspirationResult[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Vibe steering state: track slider values per category
  const [sliderValues, setSliderValues] = useState<Record<string, Record<string, number>>>({});
  const [isRefining, setIsRefining] = useState<Record<string, boolean>>({});
  const [refiningRequestId, setRefiningRequestId] = useState<Record<string, string>>({}); // Track request IDs to prevent race conditions
  const refiningRequestIdRef = useRef<Record<string, string>>({}); // Use ref for synchronous access
  const [popoverOpen, setPopoverOpen] = useState<Record<string, boolean>>({}); // Track popover open state

  useEffect(() => {
    if (!creativeBrief?.visualDNA) {
      return;
    }

    // Fetch inspiration images for each category
    const fetchInspiration = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Use visual_prompt if available (natural language), fallback to descriptors
        const { visualDNA } = creativeBrief;
        
        // Build search query: prioritize visual_prompt, fallback to descriptors
        const buildCategoryQuery = (category: any, fallbackDescriptors: string[]) => {
          if (category.visual_prompt) {
            return category.visual_prompt;
          }
          return fallbackDescriptors.slice(0, 5).join(", ");
        };
        
        const categoryQueries = [
          buildCategoryQuery(visualDNA.brand_color_mood, visualDNA.brand_color_mood.descriptors),
          buildCategoryQuery(visualDNA.typography_voice, visualDNA.typography_voice.descriptors),
          buildCategoryQuery(visualDNA.logo_geometry_essence, visualDNA.logo_geometry_essence.descriptors),
          buildCategoryQuery(
            visualDNA.photography_cinematic_world,
            [
              ...visualDNA.photography_cinematic_world.backgrounds.slice(0, 3),
              ...visualDNA.photography_cinematic_world.lighting.slice(0, 3),
            ]
          ),
          buildCategoryQuery(visualDNA.illustration_style_medium, visualDNA.illustration_style_medium.descriptors),
        ];
        
        const searchQuery = categoryQueries.join(". ");

        console.log('🔍 [Step3] Fetching inspiration images with query:', searchQuery.substring(0, 100));

        const response = await fetch('/api/mood-boards', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            brandBrief: searchQuery,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch inspiration images');
        }

        const data = await response.json();
        console.log('✅ [Step3] Received inspiration results:', data.count, 'images');

        // Group results by category - STRICT matching only
        const grouped: Record<string, InspirationResult[]> = {};
        
        // Initialize all categories
        inspirationSections.forEach(section => {
          grouped[section.category] = [];
        });
        photographySubsections.forEach(subsection => {
          grouped[subsection.category] = [];
        });

        if (data.results && Array.isArray(data.results)) {
          console.log('📊 [Step3] Total results from Pinecone:', data.results.length);
          
          // First pass: Group by exact category match
          data.results.forEach((result: InspirationResult) => {
            const category = result.metadata?.category;
            if (!category) {
              console.log('⚠️ [Step3] Result missing category:', result.id);
              return;
            }
            
            // STRICT category matching - exact matches only to prevent cross-contamination
            // Pinecone stores categories as: brand_color_mood, typography, logo_geometry, illustration,
            // photography/models, photography/products, photography/environments
            if (category === 'brand_color_mood') {
              grouped['brand_color_mood'].push(result);
            } else if (category === 'typography') {
              grouped['typography'].push(result);
            } else if (category === 'logo_geometry') {
              grouped['logo_geometry'].push(result);
            } else if (category === 'illustration') {
              grouped['illustration'].push(result);
            } else if (category === 'photography/environments' || category === 'environments') {
              grouped['environments'].push(result);
            } else if (category === 'photography/products' || category === 'products') {
              grouped['products'].push(result);
            } else if (category === 'photography/models' || category === 'models') {
              grouped['models'].push(result);
            } else {
              // Log unexpected categories for debugging
              console.log('⚠️ [Step3] Unexpected category:', category, 'from result:', result.id);
            }
          });
          
          // Log category distribution after first pass
          console.log('📊 [Step3] Category distribution (first pass):', 
            Object.keys(grouped).map(k => `${k}: ${grouped[k].length}`).join(', ')
          );
          
          // Second pass: Fill missing categories (except typography which is expected to be empty)
          // Use remaining results to fill categories that have no matches
          const usedResults = new Set<string>();
          Object.values(grouped).flat().forEach(r => usedResults.add(r.id));
          
          const unusedResults = data.results.filter(r => !usedResults.has(r.id));
          console.log('📊 [Step3] Unused results for fallback:', unusedResults.length);
          
          // Fill missing categories with best available results (except typography)
          inspirationSections.forEach(section => {
            if (section.category === 'typography') {
              // Typography is expected to be empty, skip it
              return;
            }
            if (!grouped[section.category] || grouped[section.category].length === 0) {
              console.log(`⚠️ [Step3] Category ${section.category} is empty, filling with fallback results`);
              // Take best unused results as fallback (top results not yet used)
              const fallback = unusedResults.slice(0, section.imageCount);
              grouped[section.category] = fallback;
              fallback.forEach(r => usedResults.add(r.id));
            }
          });
          
          photographySubsections.forEach(subsection => {
            if (!grouped[subsection.category] || grouped[subsection.category].length === 0) {
              console.log(`⚠️ [Step3] Category ${subsection.category} is empty, filling with fallback results`);
              const unusedNow = data.results.filter(r => !usedResults.has(r.id));
              const fallback = unusedNow.slice(0, subsection.imageCount);
              grouped[subsection.category] = fallback;
              fallback.forEach(r => usedResults.add(r.id));
            }
          });
          
          // Log final category distribution
          console.log('📊 [Step3] Final category distribution:', 
            Object.keys(grouped).map(k => `${k}: ${grouped[k].length}`).join(', ')
          );
        }

        // Limit images per category
        inspirationSections.forEach(section => {
          if (grouped[section.category]) {
            grouped[section.category] = grouped[section.category].slice(0, section.imageCount);
          }
        });
        
        photographySubsections.forEach(subsection => {
          if (grouped[subsection.category]) {
            grouped[subsection.category] = grouped[subsection.category].slice(0, subsection.imageCount);
          }
        });

        setResults(grouped);
        console.log('✅ [Step3] Grouped results:', Object.keys(grouped).map(k => `${k}: ${grouped[k].length}`));
      } catch (err: any) {
        console.error('❌ [Step3] Error fetching inspiration:', err);
        setError(err.message || 'Failed to load inspiration images');
      } finally {
        setIsLoading(false);
      }
    };

    fetchInspiration();
  }, [creativeBrief]);

  // Debug: Log when results change
  useEffect(() => {
    console.log('🔄 [Step3] Results state changed:', Object.keys(results).map(k => `${k}: ${results[k]?.length || 0} results`));
    Object.keys(results).forEach(category => {
      if (results[category]?.length > 0) {
        console.log(`  📸 ${category}: First image ID = ${results[category][0]?.id}, path = ${results[category][0]?.metadata?.file_path}`);
      }
    });
  }, [results]);

  const getImagePath = (result: InspirationResult) => {
    // Convert file_path to a local path or URL
    const filePath = result.metadata?.file_path;
    if (!filePath) return null;
    
    // Serve images from data/ directory via API route
    if (filePath.startsWith('data/')) {
      return `/api/images/${filePath}`;
    }
    
    return filePath;
  };

  // Initialize slider values for a category
  const initializeSliders = (categoryKey: string) => {
    if (!sliderValues[categoryKey]) {
      const categoryType = CATEGORY_TYPE_MAP[categoryKey];
      const sliders = CATEGORY_SLIDERS[categoryType] || [];
      const initialValues: Record<string, number> = {};
      sliders.forEach(slider => {
        initialValues[slider.key] = 0; // Start at neutral (0)
      });
      setSliderValues(prev => {
        const updated = { ...prev, [categoryKey]: initialValues };
        console.log(`🎚️ [Step3] Initialized sliders for ${categoryKey}:`, initialValues);
        return updated;
      });
    }
  };

  // Handle slider value change
  const handleSliderChange = (categoryKey: string, sliderKey: string, value: number[]) => {
    const newValue = value[0];
    setSliderValues(prev => {
      const updated = {
        ...prev,
        [categoryKey]: {
          ...(prev[categoryKey] || {}),
          [sliderKey]: newValue,
        },
      };
      console.log(`🎚️ [Step3] Slider ${categoryKey}.${sliderKey} changed to ${newValue}`);
      return updated;
    });
  };

  // Refine category with slider values
  const handleRefineCategory = async (categoryKey: string) => {
    const categoryType = CATEGORY_TYPE_MAP[categoryKey];
    if (!categoryType) {
      console.error('❌ [Step3] Unknown category type for:', categoryKey);
      return;
    }

    const currentSliders = sliderValues[categoryKey];
    if (!currentSliders) {
      console.error('❌ [Step3] No slider values for:', categoryKey);
      return;
    }

    // Prevent duplicate requests
    if (isRefining[categoryKey]) {
      console.warn('⚠️ [Step3] Refinement already in progress for:', categoryKey);
      return;
    }

    // Generate unique request ID to track this specific request
    // Use a more unique ID to avoid collisions
    const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    console.log('🆔 [Step3] Generated request ID:', requestId, 'for category:', categoryKey);
    
    // Update both state and ref for synchronous access
    refiningRequestIdRef.current[categoryKey] = requestId;
    setRefiningRequestId(prev => ({ ...prev, [categoryKey]: requestId }));
    setIsRefining(prev => ({ ...prev, [categoryKey]: true }));

    try {
      // Build search query from creative brief: use visual_prompt if available, fallback to descriptors
      const { visualDNA } = creativeBrief!;
      
      // Helper to get visual_prompt or fallback to descriptors
      const getCategoryPrompt = (category: any, fallbackDescriptors: string[]) => {
        if (category.visual_prompt) {
          return category.visual_prompt;
        }
        return fallbackDescriptors.slice(0, 5).join(", ");
      };
      
      // Build query for the specific category being refined
      let searchQuery = '';
      switch (categoryKey) {
        case 'brand_color_mood':
          searchQuery = getCategoryPrompt(visualDNA.brand_color_mood, visualDNA.brand_color_mood.descriptors);
          break;
        case 'typography':
          searchQuery = getCategoryPrompt(visualDNA.typography_voice, visualDNA.typography_voice.descriptors);
          break;
        case 'logo_geometry':
          searchQuery = getCategoryPrompt(visualDNA.logo_geometry_essence, visualDNA.logo_geometry_essence.descriptors);
          break;
        case 'illustration':
          searchQuery = getCategoryPrompt(visualDNA.illustration_style_medium, visualDNA.illustration_style_medium.descriptors);
          break;
        case 'environments':
        case 'products':
        case 'models':
          // For photography subcategories, use the main photography visual_prompt or combine subcategory descriptors
          if (visualDNA.photography_cinematic_world.visual_prompt) {
            searchQuery = visualDNA.photography_cinematic_world.visual_prompt;
          } else {
            const subcategoryDescriptors = 
              categoryKey === 'environments' ? visualDNA.photography_cinematic_world.backgrounds :
              categoryKey === 'products' ? visualDNA.photography_cinematic_world.products :
              visualDNA.photography_cinematic_world.models;
            searchQuery = subcategoryDescriptors.slice(0, 5).join(", ");
          }
          break;
        default:
          // Fallback: combine all descriptors
          searchQuery = [
            ...visualDNA.brand_color_mood.descriptors.slice(0, 5),
            ...visualDNA.typography_voice.descriptors.slice(0, 5),
            ...visualDNA.logo_geometry_essence.descriptors.slice(0, 5),
            ...visualDNA.photography_cinematic_world.backgrounds.slice(0, 3),
            ...visualDNA.photography_cinematic_world.lighting.slice(0, 3),
            ...visualDNA.illustration_style_medium.descriptors.slice(0, 5),
          ].join(", ");
      }

      console.log('🎛️ [Step3] Refining category:', categoryKey, 'with sliders:', currentSliders);

      // Get current image path for this category to use as base
      const currentImage = results[categoryKey]?.[0];
      console.log('🔍 [Step3] Current image for category:', categoryKey, {
        hasImage: !!currentImage,
        imageId: currentImage?.id,
        imagePath: currentImage?.metadata?.file_path,
        fullResult: currentImage
      });
      
      const currentImagePath = currentImage ? getImagePath(currentImage) : null;
      const currentImageId = currentImage?.id; // Store ID to exclude from results
      console.log('🔍 [Step3] Extracted values:', {
        currentImagePath,
        currentImageId,
        willExclude: !!currentImageId
      });
      
      if (currentImagePath) {
        console.log('🖼️ [Step3] Using current image as base for tuning:', currentImagePath);
      } else {
        console.warn('⚠️ [Step3] No current image path found, will use brand brief as base');
      }

      const response = await fetch('/api/refine-category', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brandBrief: searchQuery,
          categoryType,
          sliderValues: currentSliders,
          originalCategory: categoryKey,
          currentImagePath: currentImagePath, // Pass current image path to use as base
          currentImageId: currentImageId, // Pass current image ID to exclude from results
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to refine category');
      }

      const data = await response.json();
      console.log('✅ [Step3] Refined results:', data.count, 'images');
      console.log('✅ [Step3] Results array length:', data.results?.length || 0);
      console.log('✅ [Step3] First result:', data.results?.[0] ? {
        id: data.results[0].id,
        hasMetadata: !!data.results[0].metadata,
        file_path: data.results[0].metadata?.file_path,
        category: data.results[0].metadata?.category
      } : 'NO RESULTS');
      
      // Check if this request is still the latest one (prevent race conditions)
      // Use ref for synchronous access (state updates are async)
      const currentRequestId = refiningRequestIdRef.current[categoryKey];
      console.log('🆔 [Step3] Checking request ID:', {
        thisRequestId: requestId,
        currentRequestId: currentRequestId,
        match: currentRequestId === requestId,
        refContents: refiningRequestIdRef.current
      });
      
      if (currentRequestId !== requestId) {
        console.warn('⚠️ [Step3] Ignoring stale request result for:', categoryKey, {
          expectedRequestId: requestId,
          currentRequestId: currentRequestId,
          reason: 'Another refinement request was made after this one - ignoring this response'
        });
        // CRITICAL: Still clear refining state so UI doesn't stay in loading state
        setIsRefining(prev => ({ ...prev, [categoryKey]: false }));
        return;
      }
      
      console.log('✅ [Step3] Request ID matches, processing results:', requestId);
      
      const oldImageId = results[categoryKey]?.[0]?.id;
      const newImageId = data.results?.[0]?.id;
      const areDifferent = newImageId !== oldImageId;
      
      console.log('🔍 [Step3] Comparison:', {
        oldImageId,
        oldImagePath: results[categoryKey]?.[0]?.metadata?.file_path,
        newImageId,
        newImagePath: data.results?.[0]?.metadata?.file_path,
        excludedImageId: currentImageId,
        areDifferent,
        sameImage: !areDifferent,
        topResults: data.results?.slice(0, 5).map(r => ({ id: r.id, score: r.score, path: r.metadata?.file_path }))
      });
      
      if (!areDifferent && currentImageId) {
        console.warn('⚠️ [Step3] WARNING: New result has the same ID as old image!');
        console.warn('⚠️ [Step3] This means exclusion might not have worked, or query returned same image');
        console.warn('⚠️ [Step3] Check server logs for exclusion details');
      }

      // Update results for this category
      // CRITICAL: Only update if we have valid results with file_path, otherwise keep old image
      if (data.results && Array.isArray(data.results) && data.results.length > 0) {
        // Determine image count based on category
        let imageCount = 1;
        if (categoryKey === 'models') {
          imageCount = 4;
        }
        
        const updatedResults = data.results.slice(0, imageCount);
        console.log(`📊 [Step3] Received ${data.results.length} total results, using first ${updatedResults.length}`);
        console.log(`📊 [Step3] First result ID:`, updatedResults[0]?.id);
        console.log(`📊 [Step3] First result file_path:`, updatedResults[0]?.metadata?.file_path);
        console.log(`📊 [Step3] First result has valid path:`, !!updatedResults[0]?.metadata?.file_path);
        
        // Validate that results have valid file paths
        const validResults = updatedResults.filter(r => r.metadata?.file_path);
        console.log(`🔍 [Step3] Validation: ${updatedResults.length} total results, ${validResults.length} with file_path`);
        
        // CRITICAL CHECK: If no valid results, DO NOT update state - keep old image
        if (validResults.length === 0) {
          console.error('❌ [Step3] No valid results with file_path after filtering!');
          console.error('❌ [Step3] This means the query returned results but they have no file_path metadata');
          console.error('❌ [Step3] Raw results:', updatedResults.map(r => ({ 
            id: r.id, 
            hasMetadata: !!r.metadata,
            metadataKeys: r.metadata ? Object.keys(r.metadata) : [],
            file_path: r.metadata?.file_path 
          })));
          console.warn('⚠️ [Step3] Keeping existing image since no valid new results - NOT updating state');
          // CRITICAL: Don't update state - keep the old image visible
          setIsRefining(prev => ({ ...prev, [categoryKey]: false }));
          return;
        }
        
        // Use only valid results
        const finalResults = validResults.length < updatedResults.length ? validResults : updatedResults;
        if (finalResults.length < updatedResults.length) {
          console.warn(`⚠️ [Step3] Filtered out ${updatedResults.length - finalResults.length} results without file_path`);
        }
        
        // CRITICAL CHECK: Ensure we have at least 1 valid result before updating
        if (finalResults.length === 0) {
          console.error('❌ [Step3] finalResults is empty - this should not happen!');
          console.warn('⚠️ [Step3] Keeping existing image - NOT updating state');
          setIsRefining(prev => ({ ...prev, [categoryKey]: false }));
          return;
        }
        
        console.log(`✅ [Step3] Using ${finalResults.length} valid results with file_path`);
        console.log(`✅ [Step3] Will update state with new image: ${finalResults[0]?.metadata?.file_path}`);
        console.log(`✅ [Step3] About to call setResults - current state has:`, results[categoryKey]?.length || 0, 'images');
        
        // Force state update by creating a new object and new array
        // CRITICAL: Only update if we have valid results
        setResults(prev => {
          console.log(`🔄 [Step3] Inside setResults callback - prev state:`, {
            categoryKey,
            prevCount: prev[categoryKey]?.length || 0,
            finalResultsCount: finalResults.length,
            willUpdate: finalResults.length > 0 && !!finalResults[0]?.metadata?.file_path
          });
          // Double-check we have valid results before updating
          if (!finalResults || finalResults.length === 0) {
            console.error('❌ [Step3] Attempted to update state with empty finalResults - aborting!');
            console.error('❌ [Step3] Keeping existing results:', prev[categoryKey]?.length || 0, 'images');
            return prev; // Return unchanged state - this prevents gray box
          }
          
          // Verify first result has file_path
          if (!finalResults[0]?.metadata?.file_path) {
            console.error('❌ [Step3] First result missing file_path - aborting state update!');
            return prev; // Return unchanged state - this prevents gray box
          }
          
          // Create a completely new object to ensure React detects the change
          const newResults = {
            ...prev,
            [categoryKey]: finalResults.map(r => ({ ...r })), // Deep copy each result
          };
          console.log('✅ [Step3] State update successful:', {
            category: categoryKey,
            oldCount: prev[categoryKey]?.length || 0,
            newCount: newResults[categoryKey]?.length || 0,
            oldId: prev[categoryKey]?.[0]?.id,
            newId: newResults[categoryKey]?.[0]?.id,
            changed: newResults[categoryKey]?.[0]?.id !== prev[categoryKey]?.[0]?.id,
            newPath: newResults[categoryKey]?.[0]?.metadata?.file_path
          });
          // #region agent log
          fetch('http://127.0.0.1:7243/ingest/04912701-0df3-44bf-a263-0763cdbf7869',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'Step3Inspiration.tsx:393',message:'State update executed',data:{categoryKey,newFirstId:newResults[categoryKey]?.[0]?.id,prevFirstId:prev[categoryKey]?.[0]?.id,stateChanged:newResults[categoryKey]?.[0]?.id!==prev[categoryKey]?.[0]?.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          return newResults;
        });
      } else {
        console.warn('⚠️ [Step3] No results returned from refine-category');
        console.warn('⚠️ [Step3] Response data:', data);
        console.warn('⚠️ [Step3] This could mean:');
        console.warn('   - Query returned 0 results after category filtering');
        console.warn('   - Exclusion removed all results');
        console.warn('   - No images in database for this category');
        // CRITICAL: If no results, keep the old image instead of clearing it
        console.log('⚠️ [Step3] Keeping existing image since no new results - NOT updating state');
        // CRITICAL: Don't update state at all - keep the old image visible
        // The results state should remain unchanged
      }
    } catch (err: any) {
      // Only update error if this is still the latest request
      if (refiningRequestIdRef.current[categoryKey] === requestId) {
        console.error('❌ [Step3] Error refining category:', err);
        setError(err.message || 'Failed to refine category');
      }
    } finally {
      // Only clear refining state if this is still the latest request
      if (refiningRequestIdRef.current[categoryKey] === requestId) {
        setIsRefining(prev => ({ ...prev, [categoryKey]: false }));
      }
    }
  };

  // Get sliders for a category
  const getSlidersForCategory = (categoryKey: string): SliderConfig[] => {
    const categoryType = CATEGORY_TYPE_MAP[categoryKey];
    return CATEGORY_SLIDERS[categoryType] || [];
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-7xl mx-auto space-y-8"
    >
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Inspiration</h1>
        <p className="text-muted-foreground text-lg">
          Visual references curated from your style description
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
          <p className="text-sm">Error: {error}</p>
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Color, Typography, Logo, Illustration - 1 image each */}
        {inspirationSections.map((section, idx) => {
          const sectionResults = results[section.category] || [];
          const images = sectionResults.slice(0, section.imageCount); // Limit to imageCount

          return (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <Card className="h-full">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <div>
                    <CardTitle className="text-lg">{section.title}</CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      {section.subtitle}
                    </p>
                  </div>
                  {CATEGORY_TYPE_MAP[section.category] && (
                    <Popover 
                      open={popoverOpen[section.category] || false}
                      onOpenChange={(open) => {
                        setPopoverOpen(prev => ({ ...prev, [section.category]: open }));
                        if (open) {
                          initializeSliders(section.category);
                        }
                      }}
                    >
                      <PopoverTrigger asChild>
                        <Button variant="outline" size="sm" className="h-8">
                          <Sliders className="h-3 w-3 mr-1" />
                          Tune
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-80" align="end" onInteractOutside={(e) => {
                        // Prevent closing while refining
                        if (isRefining[section.category]) {
                          e.preventDefault();
                        }
                      }}>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-medium text-sm mb-3">Adjust {section.title}</h4>
                            {getSlidersForCategory(section.category).map((slider) => {
                              const currentValue = sliderValues[section.category]?.[slider.key] ?? 0;
                              return (
                                <div key={slider.key} className="space-y-2 mb-4">
                                  <div className="flex justify-between items-center">
                                    <Label className="text-xs text-muted-foreground">
                                      {slider.labelLeft}
                                    </Label>
                                    <Label className="text-xs text-muted-foreground">
                                      {slider.labelRight}
                                    </Label>
                                  </div>
                                  <Slider
                                    value={[currentValue]}
                                    onValueChange={(value) => handleSliderChange(section.category, slider.key, value)}
                                    min={-1}
                                    max={1}
                                    step={0.1}
                                    className="w-full"
                                  />
                                </div>
                              );
                            })}
                          </div>
                            <Button
                              onClick={async () => {
                                await handleRefineCategory(section.category);
                                // Keep popover open during refinement, close after success
                                if (!isRefining[section.category]) {
                                  setTimeout(() => {
                                    setPopoverOpen(prev => ({ ...prev, [section.category]: false }));
                                  }, 500);
                                }
                              }}
                              disabled={isRefining[section.category]}
                              className="w-full"
                              size="sm"
                            >
                              {isRefining[section.category] ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                                  Refining...
                                </>
                              ) : (
                                'Apply Changes'
                              )}
                            </Button>
                        </div>
                      </PopoverContent>
                    </Popover>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {isLoading || isRefining[section.category] ? (
                      // Loading skeleton
                      <Skeleton className="aspect-square rounded-lg" />
                    ) : images.length > 0 ? (
                      // Display single image
                      <div className="aspect-square bg-muted rounded-lg overflow-hidden border border-border relative group">
                        {(() => {
                          const imagePath = getImagePath(images[0]);
                          // Use image ID and score as key - this will change when a new image is returned
                          const imageId = images[0].id || images[0].metadata?.file_path || 'default';
                          const imageScore = images[0].score || 0;
                          const imageKey = `${section.category}-${imageId}-${imageScore}`;
                          // Use image ID for cache busting to ensure browser fetches new image
                          const cacheBuster = `${imageId}-${imageScore}`;
                          return imagePath ? (
                            <img
                              key={imageKey}
                              src={`${imagePath}?v=${cacheBuster}`}
                              alt={`${section.title} inspiration`}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                                if (target.parentElement) {
                                  const placeholder = document.createElement('div');
                                  placeholder.className = 'w-full h-full flex items-center justify-center';
                                  placeholder.innerHTML = '<svg class="w-8 h-8 text-muted-foreground/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>';
                                  target.parentElement.appendChild(placeholder);
                                }
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <ImageIcon className="w-8 h-8 text-muted-foreground/40" />
                            </div>
                          );
                        })()}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                      </div>
                    ) : (
                      // Empty state
                      <div className="aspect-square bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-muted-foreground/20">
                        <ImageIcon className="w-8 h-8 text-muted-foreground/40" />
                      </div>
                    )}
                    <p className="text-sm text-muted-foreground text-center">
                      {section.placeholder}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Photography - Split into 3 sections: Environment, Product, Model */}
      <div className="space-y-4">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight">Photography</h2>
          <p className="text-sm text-muted-foreground">
            Photography Cinematic World
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-6">
          {photographySubsections.map((subsection, idx) => {
            const subsectionResults = results[subsection.category] || [];
            const images = subsectionResults.slice(0, subsection.imageCount); // Limit to imageCount

            return (
              <motion.div
                key={subsection.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <Card className="h-full">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div>
                      <CardTitle className="text-lg">{subsection.title}</CardTitle>
                      <p className="text-xs text-muted-foreground mt-1">
                        {subsection.category}
                      </p>
                    </div>
                    {CATEGORY_TYPE_MAP[subsection.category] && (
                      <Popover 
                        open={popoverOpen[subsection.category] || false}
                        onOpenChange={(open) => {
                          setPopoverOpen(prev => ({ ...prev, [subsection.category]: open }));
                          if (open) {
                            initializeSliders(subsection.category);
                          }
                        }}
                      >
                        <PopoverTrigger asChild>
                          <Button variant="outline" size="sm" className="h-8">
                            <Sliders className="h-3 w-3 mr-1" />
                            Tune
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-80" align="end" onInteractOutside={(e) => {
                          // Prevent closing while refining
                          if (isRefining[subsection.category]) {
                            e.preventDefault();
                          }
                        }}>
                          <div className="space-y-4">
                            <div>
                              <h4 className="font-medium text-sm mb-3">Adjust {subsection.title}</h4>
                              {getSlidersForCategory(subsection.category).map((slider) => {
                                const currentValue = sliderValues[subsection.category]?.[slider.key] ?? 0;
                                return (
                                  <div key={slider.key} className="space-y-2 mb-4">
                                    <div className="flex justify-between items-center">
                                      <Label className="text-xs text-muted-foreground">
                                        {slider.labelLeft}
                                      </Label>
                                      <Label className="text-xs text-muted-foreground">
                                        {slider.labelRight}
                                      </Label>
                                    </div>
                                    <Slider
                                      value={[currentValue]}
                                      onValueChange={(value) => handleSliderChange(subsection.category, slider.key, value)}
                                      min={-1}
                                      max={1}
                                      step={0.1}
                                      className="w-full"
                                    />
                                  </div>
                                );
                              })}
                            </div>
                            <Button
                              onClick={async () => {
                                await handleRefineCategory(subsection.category);
                                // Keep popover open during refinement, close after success
                                if (!isRefining[subsection.category]) {
                                  setTimeout(() => {
                                    setPopoverOpen(prev => ({ ...prev, [subsection.category]: false }));
                                  }, 500);
                                }
                              }}
                              disabled={isRefining[subsection.category]}
                              className="w-full"
                              size="sm"
                            >
                              {isRefining[subsection.category] ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                                  Refining...
                                </>
                              ) : (
                                'Apply Changes'
                              )}
                            </Button>
                          </div>
                        </PopoverContent>
                      </Popover>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {isLoading || isRefining[subsection.category] ? (
                        // Loading skeleton - show grid if Model (4 images), single if others
                        subsection.imageCount > 1 ? (
                          <div className="grid grid-cols-2 gap-3">
                            {[1, 2, 3, 4].map((item) => (
                              <Skeleton key={item} className="aspect-square rounded-lg" />
                            ))}
                          </div>
                        ) : (
                          <Skeleton className="aspect-square rounded-lg" />
                        )
                      ) : images.length > 0 ? (
                        // Display images
                        subsection.imageCount > 1 ? (
                          // Model: 2x2 grid (up to 4 images)
                          <div className="grid grid-cols-2 gap-3">
                            {images.map((result, imgIdx) => {
                              const imagePath = getImagePath(result);
                              // Include score in key to force re-render when results change
                              const imageKey = `${subsection.category}-${result.id || result.metadata?.file_path || imgIdx}-${result.score || Date.now()}`;
                              return (
                                <div
                                  key={imageKey}
                                  className="aspect-square bg-muted rounded-lg overflow-hidden border border-border relative group"
                                >
                                  {imagePath ? (
                                    <img
                                      key={imageKey}
                                      src={`${imagePath}?t=${Date.now()}`}
                                      alt={`${subsection.title} inspiration ${imgIdx + 1}`}
                                      className="w-full h-full object-cover"
                                      onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = 'none';
                                        if (target.parentElement) {
                                          const placeholder = document.createElement('div');
                                          placeholder.className = 'w-full h-full flex items-center justify-center';
                                          placeholder.innerHTML = '<svg class="w-6 h-6 text-muted-foreground/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>';
                                          target.parentElement.appendChild(placeholder);
                                        }
                                      }}
                                    />
                                  ) : (
                                    <div className="w-full h-full flex items-center justify-center">
                                      <ImageIcon className="w-6 h-6 text-muted-foreground/40" />
                                    </div>
                                  )}
                                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          // Environment/Product: Single image
                          <div className="aspect-square bg-muted rounded-lg overflow-hidden border border-border relative group">
                            {(() => {
                              const imagePath = getImagePath(images[0]);
                              // Include timestamp in key to force re-render when results change
                              const imageKey = `${subsection.category}-${images[0].id || images[0].metadata?.file_path || 'default'}-${images[0].score || Date.now()}`;
                              return imagePath ? (
                                <img
                                  key={imageKey}
                                  src={`${imagePath}?t=${Date.now()}`}
                                  alt={`${subsection.title} inspiration`}
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    const target = e.target as HTMLImageElement;
                                    target.style.display = 'none';
                                    if (target.parentElement) {
                                      const placeholder = document.createElement('div');
                                      placeholder.className = 'w-full h-full flex items-center justify-center';
                                      placeholder.innerHTML = '<svg class="w-8 h-8 text-muted-foreground/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>';
                                      target.parentElement.appendChild(placeholder);
                                    }
                                  }}
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <ImageIcon className="w-8 h-8 text-muted-foreground/40" />
                                </div>
                              );
                            })()}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                          </div>
                        )
                      ) : (
                        // Empty state
                        <div className="aspect-square bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-muted-foreground/20">
                          <ImageIcon className="w-8 h-8 text-muted-foreground/40" />
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="flex gap-4">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(2)}
          className="flex-1"
        >
          Back
        </Button>
        <Button onClick={() => setCurrentStep(4)} className="flex-1">
          Generate Brand Identity Kit
        </Button>
      </div>
    </motion.div>
  );
}

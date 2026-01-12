"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBranding } from "@/context/BrandingContext";
import { ImageIcon, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

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

  useEffect(() => {
    if (!creativeBrief?.visualDNA) {
      return;
    }

    // Fetch inspiration images for each category
    const fetchInspiration = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Combine all descriptors from visualDNA into a search query
        const { visualDNA } = creativeBrief;
        const searchQuery = [
          ...visualDNA.brand_color_mood.descriptors.slice(0, 5),
          ...visualDNA.typography_voice.descriptors.slice(0, 5),
          ...visualDNA.logo_geometry_essence.descriptors.slice(0, 5),
          ...visualDNA.photography_cinematic_world.backgrounds.slice(0, 3),
          ...visualDNA.photography_cinematic_world.lighting.slice(0, 3),
          ...visualDNA.illustration_style_medium.descriptors.slice(0, 5),
        ].join(", ");

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
                <CardHeader>
                  <CardTitle className="text-lg">{section.title}</CardTitle>
                  <p className="text-xs text-muted-foreground mt-1">
                    {section.subtitle}
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {isLoading ? (
                      // Loading skeleton
                      <Skeleton className="aspect-square rounded-lg" />
                    ) : images.length > 0 ? (
                      // Display single image
                      <div className="aspect-square bg-muted rounded-lg overflow-hidden border border-border relative group">
                        {(() => {
                          const imagePath = getImagePath(images[0]);
                          return imagePath ? (
                            <img
                              src={imagePath}
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
                  <CardHeader>
                    <CardTitle className="text-lg">{subsection.title}</CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      {subsection.category}
                    </p>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {isLoading ? (
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
                              return (
                                <div
                                  key={result.id || imgIdx}
                                  className="aspect-square bg-muted rounded-lg overflow-hidden border border-border relative group"
                                >
                                  {imagePath ? (
                                    <img
                                      src={imagePath}
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
                              return imagePath ? (
                                <img
                                  src={imagePath}
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

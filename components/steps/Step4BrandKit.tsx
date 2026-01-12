"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBranding } from "@/context/BrandingContext";
import { generateBrandKit } from "@/lib/ai";
import { ImageIcon, Loader2 } from "lucide-react";

export function Step4BrandKit() {
  const {
    formData,
    creativeBrief,
    brandKit,
    setBrandKit,
  } = useBranding();
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    // Auto-trigger generation when creative brief is available and brandKit hasn't been generated
    if (creativeBrief && !brandKit && !isGenerating) {
      setIsGenerating(true);
      
      // Initialize with loading states
      setBrandKit({
        logoUrl: null,
        assets: [],
        isLoadingLogo: true,
        isLoadingAssets: true,
      });

      // Generate logo and assets (API key is now on backend)
      generateBrandKit(creativeBrief)
        .then((kit) => {
          setBrandKit(kit);
        })
        .catch((error) => {
          console.error("Error generating brand kit:", error);
          // On error, set loading to false
          setBrandKit({
            logoUrl: null,
            assets: [],
            isLoadingLogo: false,
            isLoadingAssets: false,
          });
        })
        .finally(() => {
          setIsGenerating(false);
        });
    }
  }, [creativeBrief, brandKit, setBrandKit, isGenerating]);

  const currentBrandKit = brandKit || {
    logoUrl: null,
    assets: [],
    isLoadingLogo: true,
    isLoadingAssets: true,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-7xl mx-auto space-y-8"
    >
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Brand Identity Kit</h1>
        <p className="text-muted-foreground text-lg">
          Complete brand system for {formData?.businessName}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Primary Brand Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="md:col-span-8"
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Primary Brand Logo</CardTitle>
              {currentBrandKit.isLoadingLogo && (
                <p className="text-sm text-muted-foreground">
                  Generating logo from Visual DNA...
                </p>
              )}
            </CardHeader>
            <CardContent>
              <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-muted-foreground/20 overflow-hidden relative">
                {currentBrandKit.isLoadingLogo ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">
                      Generating logo...
                    </p>
                    <Skeleton className="absolute inset-0 w-full h-full" />
                  </div>
                ) : currentBrandKit.logoUrl ? (
                  <img
                    src={currentBrandKit.logoUrl}
                    alt="Brand Logo"
                    className="w-full h-full object-contain p-8"
                  />
                ) : (
                  <div className="text-center space-y-2">
                    <ImageIcon className="w-12 h-12 text-muted-foreground/40 mx-auto" />
                    <div className="text-lg font-bold">
                      {formData?.businessName || "Logo"}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Logo will be generated here
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Brand Assets Gallery */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="md:col-span-4"
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Brand Assets Gallery</CardTitle>
              {currentBrandKit.isLoadingAssets && (
                <p className="text-sm text-muted-foreground">
                  Generating brand mockups...
                </p>
              )}
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {currentBrandKit.isLoadingAssets
                  ? // Loading skeletons
                    Array.from({ length: 4 }).map((_, idx) => (
                      <div key={idx} className="aspect-square relative">
                        <Skeleton className="w-full h-full rounded-lg" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Loader2 className="h-6 w-6 animate-spin text-primary/50" />
                        </div>
                      </div>
                    ))
                  : currentBrandKit.assets.length > 0
                    ? // Generated assets
                      currentBrandKit.assets.map((url, idx) => (
                        <div
                          key={idx}
                          className="aspect-square bg-muted rounded-lg overflow-hidden border border-border relative group"
                        >
                          <img
                            src={url}
                            alt={`Brand asset ${idx + 1}`}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                        </div>
                      ))
                    : // Empty state
                      Array.from({ length: 4 }).map((_, idx) => (
                        <div
                          key={idx}
                          className="aspect-square bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-muted-foreground/20"
                        >
                          <ImageIcon className="w-6 h-6 text-muted-foreground/40" />
                        </div>
                      ))}
              </div>
              {!currentBrandKit.isLoadingAssets &&
                currentBrandKit.assets.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center mt-3">
                    Brand mockups will be generated here
                  </p>
                )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="flex justify-center pt-4">
        <Button
          variant="outline"
          onClick={() => window.location.reload()}
          className="w-full max-w-md"
        >
          Start New Project
        </Button>
      </div>
    </motion.div>
  );
}

"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBranding } from "@/context/BrandingContext";

export function Step2CreativeBrief() {
  const { setCurrentStep, formData, creativeBrief } = useBranding();

  // No mock data - only show if creativeBrief exists
  if (!creativeBrief) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="max-w-5xl mx-auto space-y-8"
      >
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">The Brief</h1>
          <p className="text-muted-foreground text-lg">
            No creative brief available. Please go back to Step 1 and generate a brief.
          </p>
        </div>
        <div className="flex justify-center">
          <Button onClick={() => setCurrentStep(1)} variant="outline">
            Go Back to Step 1
          </Button>
        </div>
      </motion.div>
    );
  }

  const { visualDNA } = creativeBrief;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-5xl mx-auto space-y-8"
    >
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">The Brief</h1>
        <p className="text-muted-foreground text-lg">
          AI-generated Visual DNA for {formData?.businessName}
        </p>
      </div>

      <div className="grid gap-6">
        {/* Brand Color Mood */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Brand Color Mood</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Emotional temperature and personality
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Visual Prompt - Natural Language (Primary) */}
            {visualDNA.brand_color_mood.visual_prompt && (
              <div className="bg-muted/50 rounded-lg p-4 border border-border">
                <p className="text-base leading-relaxed text-foreground">
                  {visualDNA.brand_color_mood.visual_prompt}
                </p>
              </div>
            )}
            
            <div>
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Avoid
              </h3>
              <div className="flex flex-wrap gap-2">
                {visualDNA.brand_color_mood.avoid.map((item, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-muted text-muted-foreground rounded-md text-sm line-through"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Typography Voice */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Typography Voice</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Soul and structure of letterforms
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Visual Prompt - Natural Language (Primary) */}
            {visualDNA.typography_voice.visual_prompt && (
              <div className="bg-muted/50 rounded-lg p-4 border border-border">
                <p className="text-base leading-relaxed text-foreground">
                  {visualDNA.typography_voice.visual_prompt}
                </p>
              </div>
            )}
            
            <div>
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Avoid
              </h3>
              <div className="flex flex-wrap gap-2">
                {visualDNA.typography_voice.avoid.map((item, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-muted text-muted-foreground rounded-md text-sm line-through"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Logo Geometry Essence */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Logo Geometry Essence</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Silhouette, line-weight, and tension
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Visual Prompt - Natural Language (Primary) */}
            {visualDNA.logo_geometry_essence.visual_prompt && (
              <div className="bg-muted/50 rounded-lg p-4 border border-border">
                <p className="text-base leading-relaxed text-foreground">
                  {visualDNA.logo_geometry_essence.visual_prompt}
                </p>
              </div>
            )}
            
            <div>
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Avoid
              </h3>
              <div className="flex flex-wrap gap-2">
                {visualDNA.logo_geometry_essence.avoid.map((item, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-muted text-muted-foreground rounded-md text-sm line-through"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Photography Cinematic World */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Photography Cinematic World</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Visual storytelling elements
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Visual Prompt - Natural Language (Primary) */}
            {visualDNA.photography_cinematic_world.visual_prompt && (
              <div className="bg-muted/50 rounded-lg p-4 border border-border">
                <p className="text-base leading-relaxed text-foreground">
                  {visualDNA.photography_cinematic_world.visual_prompt}
                </p>
              </div>
            )}
            
            <div>
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Avoid
              </h3>
              <div className="flex flex-wrap gap-2">
                {visualDNA.photography_cinematic_world.avoid.map(
                  (item, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 bg-muted text-muted-foreground rounded-md text-sm line-through"
                    >
                      {item}
                    </span>
                  )
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Illustration Style Medium */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Illustration Style Medium</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Artistic technique and materials
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Visual Prompt - Natural Language (Primary) */}
            {visualDNA.illustration_style_medium.visual_prompt && (
              <div className="bg-muted/50 rounded-lg p-4 border border-border">
                <p className="text-base leading-relaxed text-foreground">
                  {visualDNA.illustration_style_medium.visual_prompt}
                </p>
              </div>
            )}
            
            <div>
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Avoid
              </h3>
              <div className="flex flex-wrap gap-2">
                {visualDNA.illustration_style_medium.avoid.map((item, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-muted text-muted-foreground rounded-md text-sm line-through"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(1)}
          className="flex-1"
        >
          Back
        </Button>
        <Button onClick={() => setCurrentStep(3)} className="flex-1">
          Continue to Inspiration
        </Button>
      </div>
    </motion.div>
  );
}

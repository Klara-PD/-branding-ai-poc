"use client";

import { AnimatePresence } from "framer-motion";
import { BrandingProvider, useBranding } from "@/context/BrandingContext";
import { Step1Discovery } from "@/components/steps/Step1Discovery";
import { Step2CreativeBrief } from "@/components/steps/Step2CreativeBrief";
import { Step3Inspiration } from "@/components/steps/Step3Inspiration";
import { Step4BrandKit } from "@/components/steps/Step4BrandKit";
import { StepIndicator } from "@/components/StepIndicator";
import { SettingsModal } from "@/components/SettingsModal";

function BrandingPlayground() {
  const { currentStep } = useBranding();

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-5xl font-bold">Branding Playground</h1>
            <p className="text-xl text-muted-foreground">
              Generate your complete Brand System
            </p>
          </div>
          <SettingsModal />
        </div>

        {/* Step Indicator */}
        <StepIndicator />

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {currentStep === 1 && <Step1Discovery key="step1" />}
          {currentStep === 2 && <Step2CreativeBrief key="step2" />}
          {currentStep === 3 && <Step3Inspiration key="step3" />}
          {currentStep === 4 && <Step4BrandKit key="step4" />}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <BrandingProvider>
      <BrandingPlayground />
    </BrandingProvider>
  );
}

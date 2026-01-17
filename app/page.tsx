"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BrandingProvider, useBranding } from "@/context/BrandingContext";
import { Step1Discovery } from "@/components/steps/Step1Discovery";
import { Step2CreativeBrief } from "@/components/steps/Step2CreativeBrief";
import { Step3Inspiration } from "@/components/steps/Step3Inspiration";
import { Step4BrandKit } from "@/components/steps/Step4BrandKit";
import { SettingsModal } from "@/components/SettingsModal";
import { LandingPage } from "@/components/LandingPage";

// Brand color
const PURPLE = "#7B6BDB";

interface BrandingPlaygroundProps {
  onLogoClick: () => void;
}

function BrandingPlayground({ onLogoClick }: BrandingPlaygroundProps) {
  const { currentStep } = useBranding();

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen"
      style={{
        background: `linear-gradient(135deg, #ffffff 0%, #f8f7ff 50%, #f0eeff 100%)`
      }}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-6">
        <button 
          onClick={onLogoClick}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
        >
          <img
            src="/flowlogo.svg"
            alt="Flow"
            className="h-6 w-auto"
          />
        </button>
        
        <button 
          className="px-4 py-2 text-white text-xs font-medium rounded-md transition-colors hover:opacity-90"
          style={{ backgroundColor: PURPLE }}
        >
          Send Feedback
        </button>
      </header>

      {/* Main Content */}
      <main className="px-8 pb-8">
        <AnimatePresence mode="wait">
          {currentStep === 1 && <Step1Discovery key="step1" />}
          {currentStep === 2 && <Step2CreativeBrief key="step2" />}
          {currentStep === 3 && <Step3Inspiration key="step3" />}
          {currentStep === 4 && <Step4BrandKit key="step4" />}
        </AnimatePresence>
      </main>
    </motion.div>
  );
}

function AppContent() {
  const [showLanding, setShowLanding] = useState(true);

  return (
    <AnimatePresence mode="wait">
      {showLanding ? (
        <motion.div
          key="landing"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <LandingPage onStart={() => setShowLanding(false)} />
        </motion.div>
      ) : (
        <motion.div
          key="app"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <BrandingPlayground onLogoClick={() => setShowLanding(true)} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function Home() {
  return (
    <BrandingProvider>
      <AppContent />
    </BrandingProvider>
  );
}

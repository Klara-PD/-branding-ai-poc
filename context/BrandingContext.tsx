"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import type {
  DiscoveryFormData,
  CreativeBrief,
  BrandIdentityKit,
  Step,
  LLMModel,
} from "@/types";

interface BrandingContextType {
  currentStep: Step;
  setCurrentStep: (step: Step) => void;
  formData: DiscoveryFormData | null;
  setFormData: (data: DiscoveryFormData) => void;
  creativeBrief: CreativeBrief | null;
  setCreativeBrief: (brief: CreativeBrief) => void;
  brandKit: BrandIdentityKit | null;
  setBrandKit: (kit: BrandIdentityKit) => void;
  apiKeys: {
    openrouter?: string;
    replicate?: string;
  };
  setApiKeys: (keys: {
    openrouter?: string;
    replicate?: string;
  }) => void;
}

const BrandingContext = createContext<BrandingContextType | undefined>(
  undefined
);

export function BrandingProvider({ children }: { children: ReactNode }) {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [formData, setFormData] = useState<DiscoveryFormData | null>(null);
  const [creativeBrief, setCreativeBrief] = useState<CreativeBrief | null>(
    null
  );
  const [brandKit, setBrandKit] = useState<BrandIdentityKit | null>(null);
  const [apiKeys, setApiKeys] = useState<{
    openrouter?: string;
    replicate?: string;
  }>({});

  return (
    <BrandingContext.Provider
      value={{
        currentStep,
        setCurrentStep,
        formData,
        setFormData,
        creativeBrief,
        setCreativeBrief,
        brandKit,
        setBrandKit,
        apiKeys,
        setApiKeys,
      }}
    >
      {children}
    </BrandingContext.Provider>
  );
}

export function useBranding() {
  const context = useContext(BrandingContext);
  if (context === undefined) {
    throw new Error("useBranding must be used within a BrandingProvider");
  }
  return context;
}

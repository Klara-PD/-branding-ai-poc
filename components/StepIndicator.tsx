"use client";

import { Check } from "lucide-react";
import { useBranding } from "@/context/BrandingContext";
import { cn } from "@/lib/utils";

const steps = [
  { number: 1, label: "Discovery" },
  { number: 2, label: "The Brief" },
  { number: 3, label: "Inspiration" },
  { number: 4, label: "Brand Kit" },
] as const;

export function StepIndicator() {
  const { currentStep } = useBranding();

  return (
    <div className="flex items-center justify-center gap-4 mb-8">
      {steps.map((step, idx) => (
        <div key={step.number} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors",
                currentStep > step.number
                  ? "bg-primary border-primary text-primary-foreground"
                  : currentStep === step.number
                    ? "border-primary text-primary bg-background"
                    : "border-muted-foreground/30 text-muted-foreground bg-background"
              )}
            >
              {currentStep > step.number ? (
                <Check className="w-5 h-5" />
              ) : (
                <span className="text-sm font-medium">{step.number}</span>
              )}
            </div>
            <span
              className={cn(
                "text-xs mt-2 transition-colors",
                currentStep >= step.number
                  ? "text-foreground font-medium"
                  : "text-muted-foreground"
              )}
            >
              {step.label}
            </span>
          </div>
          {idx < steps.length - 1 && (
            <div
              className={cn(
                "w-12 h-0.5 mx-2 transition-colors",
                currentStep > step.number ? "bg-primary" : "bg-muted"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}

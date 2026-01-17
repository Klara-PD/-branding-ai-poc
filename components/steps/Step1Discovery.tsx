"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useBranding } from "@/context/BrandingContext";
import type { DiscoveryFormData } from "@/types";
import { DEFAULT_SYSTEM_INSTRUCTIONS } from "@/lib/constants";
import { Loader2 } from "lucide-react";
import Image from "next/image";

// Brand color
const PURPLE = "#7B6BDB";

// Industry options
const INDUSTRIES = [
  { value: "tech", label: "Tech" },
  { value: "fashion", label: "Fashion" },
  { value: "food", label: "Food & Beverage" },
  { value: "health", label: "Health & Wellness" },
  { value: "finance", label: "Finance" },
  { value: "education", label: "Education" },
  { value: "entertainment", label: "Entertainment" },
  { value: "travel", label: "Travel" },
  { value: "retail", label: "Retail" },
  { value: "services", label: "Services" },
  { value: "creative", label: "Creative & Design" },
  { value: "other", label: "Other" },
];

// Niche suggestions based on industry
function getNicheSuggestions(industry: string): { value: string; label: string }[] {
  const niches: Record<string, { value: string; label: string }[]> = {
    tech: [
      { value: "saas", label: "SaaS Platform" },
      { value: "ai", label: "AI & ML" },
      { value: "mobile", label: "Mobile Apps" },
      { value: "devtools", label: "Developer Tools" },
    ],
    fashion: [
      { value: "streetwear", label: "Streetwear" },
      { value: "luxury", label: "Luxury Fashion" },
      { value: "sustainable", label: "Sustainable" },
      { value: "activewear", label: "Activewear" },
    ],
    food: [
      { value: "bakery", label: "Bakery" },
      { value: "cafe", label: "Coffee & Café" },
      { value: "restaurant", label: "Restaurant" },
      { value: "healthy", label: "Healthy Food" },
    ],
    health: [
      { value: "fitness", label: "Fitness" },
      { value: "mental", label: "Mental Wellness" },
      { value: "nutrition", label: "Nutrition" },
      { value: "spa", label: "Spa & Beauty" },
    ],
    creative: [
      { value: "design", label: "Design Studio" },
      { value: "photography", label: "Photography" },
      { value: "branding", label: "Branding Agency" },
      { value: "video", label: "Video Production" },
    ],
  };
  return niches[industry] || [
    { value: "startup", label: "Startup" },
    { value: "agency", label: "Agency" },
    { value: "consulting", label: "Consulting" },
    { value: "ecommerce", label: "E-commerce" },
  ];
}

// Audience suggestions
const AUDIENCES = [
  { value: "gen-z", label: "Gen Z" },
  { value: "millennials", label: "Millennials" },
  { value: "professionals", label: "Professionals" },
  { value: "entrepreneurs", label: "Entrepreneurs" },
  { value: "parents", label: "Parents" },
  { value: "students", label: "Students" },
];

export function Step1Discovery() {
  const { setFormData, setCurrentStep, setCreativeBrief } = useBranding();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  
  // Form data
  const [data, setData] = useState({
    userName: '',
    brandName: '',
    industry: '',
    niche: '',
    valuePitch: '',
    audience: '',
    specialDirectives: '',
  });

  const [customNiche, setCustomNiche] = useState('');
  const [customAudience, setCustomAudience] = useState('');

  const updateData = (field: string, value: string) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const canProceed = () => {
    switch (currentStepIndex) {
      case 0: return data.userName.trim().length > 0;
      case 1: return data.brandName.trim().length > 0;
      case 2: return data.industry.length > 0;
      case 3: return data.niche.length > 0 || customNiche.length > 0;
      case 4: return data.valuePitch.trim().length > 0;
      case 5: return data.audience.length > 0 || customAudience.length > 0;
      case 6: return true;
      default: return false;
    }
  };

  const goNext = () => {
    if (currentStepIndex < 6) {
      setCurrentStepIndex(prev => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    
    const finalNiche = customNiche || data.niche;
    const finalAudience = customAudience || data.audience;
    
    const brandBrief = `
Brand: ${data.brandName}
Industry: ${data.industry}
Niche: ${finalNiche}
Value Proposition: ${data.valuePitch}
Target Audience: ${finalAudience}
Special Directives: ${data.specialDirectives || 'None specified'}
    `.trim();
    
    const formData: DiscoveryFormData = {
      businessName: data.brandName,
      location: '',
      targetAudience: finalAudience,
      styleDescription: brandBrief,
      systemInstructions: DEFAULT_SYSTEM_INSTRUCTIONS,
      selectedModel: "gpt-4o",
    };
    
    setFormData(formData);

    try {
      const response = await fetch('/api/generate-creative-brief', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ formData }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to generate');
      }

      const creativeBrief = await response.json();
      setCreativeBrief(creativeBrief);
      setIsLoading(false);
      setCurrentStep(2);
    } catch (error: any) {
      console.error('Error:', error);
      alert(`Error: ${error.message}`);
      setIsLoading(false);
    }
  };

  // Quick fill for testing
  const fillWithTestData = () => {
    const testData = {
      userName: 'Klara',
      brandName: 'Bloom Studio',
      industry: 'creative',
      niche: 'Branding Agency',
      valuePitch: 'We transform startups into memorable brands through strategic design.',
      audience: 'Tech Startups',
      specialDirectives: 'Modern, minimal. Soft gradients. No dark themes.',
    };
    setData(testData);
    setCustomNiche(testData.niche);
    setCustomAudience(testData.audience);
    setCurrentStepIndex(6);
  };

  const renderStep = () => {
    switch (currentStepIndex) {
      case 0:
        return {
          title: "Hey I'm Flow, your AI design partner.",
          subtitle: "First things first—what's your name?",
          input: (
            <input
              type="text"
              value={data.userName}
              onChange={(e) => updateData('userName', e.target.value)}
              placeholder="Fill your name"
              className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all"
              style={{ borderColor: data.userName ? PURPLE : undefined }}
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && canProceed() && goNext()}
            />
          ),
        };
      
      case 1:
        return {
          title: `Nice to meet you, ${data.userName}!`,
          subtitle: "What's the name of your brand or business?",
          input: (
            <input
              type="text"
              value={data.brandName}
              onChange={(e) => updateData('brandName', e.target.value)}
              placeholder="Enter brand name"
              className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && canProceed() && goNext()}
            />
          ),
        };
      
      case 2:
        return {
          title: `${data.brandName} sounds great!`,
          subtitle: "What industry are you in?",
          input: (
            <div className="flex flex-wrap gap-2 justify-center">
              {INDUSTRIES.map((ind) => (
                <button
                  key={ind.value}
                  onClick={() => updateData('industry', ind.value)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    data.industry === ind.value
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                  style={{ 
                    backgroundColor: data.industry === ind.value ? PURPLE : undefined,
                  }}
                  onMouseEnter={(e) => { if (data.industry !== ind.value) e.currentTarget.style.backgroundColor = '#D4D3F7'; }}
                  onMouseLeave={(e) => { if (data.industry !== ind.value) e.currentTarget.style.backgroundColor = '#f3f4f6'; }}
                >
                  {ind.label}
                </button>
              ))}
            </div>
          ),
        };
      
      case 3:
        const niches = getNicheSuggestions(data.industry);
        return {
          title: "What's your specific niche?",
          subtitle: "This helps me understand your unique position.",
          input: (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2 justify-center">
                {niches.map((niche) => (
                  <button
                    key={niche.value}
                    onClick={() => {
                      updateData('niche', niche.value);
                      setCustomNiche(niche.label);
                    }}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      data.niche === niche.value
                        ? 'text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                    style={{ backgroundColor: data.niche === niche.value ? PURPLE : undefined }}
                    onMouseEnter={(e) => { if (data.niche !== niche.value) e.currentTarget.style.backgroundColor = '#D4D3F7'; }}
                    onMouseLeave={(e) => { if (data.niche !== niche.value) e.currentTarget.style.backgroundColor = '#f3f4f6'; }}
                  >
                    {niche.label}
                  </button>
                ))}
              </div>
              <input
                type="text"
                value={customNiche}
                onChange={(e) => {
                  setCustomNiche(e.target.value);
                  updateData('niche', 'custom');
                }}
                placeholder="Or type your own..."
                className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all"
              />
            </div>
          ),
        };
      
      case 4:
        return {
          title: "What makes you special?",
          subtitle: "Describe your unique value in one sentence.",
          input: (
            <textarea
              value={data.valuePitch}
              onChange={(e) => updateData('valuePitch', e.target.value)}
              placeholder="We help [audience] achieve [outcome] by [method]..."
              className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all resize-none"
              rows={3}
              autoFocus
            />
          ),
        };
      
      case 5:
        return {
          title: "Who is your ideal customer?",
          subtitle: "Select or describe your target audience.",
          input: (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2 justify-center">
                {AUDIENCES.map((aud) => (
                  <button
                    key={aud.value}
                    onClick={() => {
                      updateData('audience', aud.value);
                      setCustomAudience(aud.label);
                    }}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      data.audience === aud.value
                        ? 'text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                    style={{ backgroundColor: data.audience === aud.value ? PURPLE : undefined }}
                    onMouseEnter={(e) => { if (data.audience !== aud.value) e.currentTarget.style.backgroundColor = '#D4D3F7'; }}
                    onMouseLeave={(e) => { if (data.audience !== aud.value) e.currentTarget.style.backgroundColor = '#f3f4f6'; }}
                  >
                    {aud.label}
                  </button>
                ))}
              </div>
              <input
                type="text"
                value={customAudience}
                onChange={(e) => {
                  setCustomAudience(e.target.value);
                  updateData('audience', 'custom');
                }}
                placeholder="Or describe your audience..."
                className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all"
              />
            </div>
          ),
        };
      
      case 6:
        return {
          title: "Any special requests?",
          subtitle: "Colors, styles, or things to avoid (optional).",
          input: (
            <textarea
              value={data.specialDirectives}
              onChange={(e) => updateData('specialDirectives', e.target.value)}
              placeholder="e.g., 'I love purple' or 'No serif fonts'..."
              className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-all resize-none"
              rows={3}
              autoFocus
            />
          ),
        };
      
      default:
        return { title: "", subtitle: "", input: null };
    }
  };

  const step = renderStep();

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-120px)] relative">
      {/* Main Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        {/* Card - Fixed viewport-relative size */}
        <div 
          className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8 md:p-12 relative overflow-hidden flex flex-col"
          style={{ 
            background: 'linear-gradient(135deg, #fafaff 0%, #f5f3ff 100%)',
            boxShadow: '0 25px 50px -12px rgba(123, 107, 219, 0.15)',
            width: '70vw',
            height: '70vh',
            maxWidth: '900px',
          }}
        >
          {/* Progress dots - at top */}
          <div className="flex justify-center gap-2 mb-8">
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full transition-all"
                style={{
                  backgroundColor: i <= currentStepIndex ? PURPLE : '#e5e7eb',
                  transform: i === currentStepIndex ? 'scale(1.3)' : 'scale(1)',
                }}
              />
            ))}
          </div>

          {/* Avatar - only show on steps 0 and 1 */}
          {currentStepIndex <= 1 && (
            <div className="flex justify-center mb-8">
              <div className="w-36 h-36 rounded-full bg-gray-100 overflow-hidden border-4 border-white shadow-lg">
                <Image
                  src={currentStepIndex === 0 ? "/assets/onboarding_1.png" : "/assets/onboarding_2.png"}
                  alt="Flow"
                  width={144}
                  height={144}
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          )}

          {/* Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStepIndex}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="text-center space-y-6 flex-1 flex flex-col justify-center"
            >
              <div className="space-y-2">
                <h1 
                  className="text-2xl md:text-3xl font-bold text-gray-900"
                  style={{ fontFamily: "'Labil Grotesk', sans-serif" }}
                >
                  {step.title}
                </h1>
                <p className="text-gray-500">
                  {step.subtitle}
                </p>
              </div>

              <div className="max-w-md mx-auto w-full">
                {step.input}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Navigation - full width, buttons on opposite sides */}
          <div className="flex items-center justify-between mt-auto pt-8 w-full">
            <button
              onClick={() => setCurrentStepIndex(prev => Math.max(0, prev - 1))}
              className={`text-gray-400 hover:text-gray-600 transition-colors text-sm ${
                currentStepIndex === 0 ? 'invisible' : ''
              }`}
            >
              ← Back
            </button>

            <AnimatePresence mode="wait">
              {canProceed() && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  onClick={goNext}
                  disabled={isLoading}
                  className="px-5 py-2.5 text-white text-sm font-medium rounded-lg transition-all hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
                  style={{ backgroundColor: PURPLE }}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : currentStepIndex === 6 ? (
                    'Define Your Vibe'
                  ) : (
                    'Continue'
                  )}
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Decorative shadow blob */}
        <div 
          className="absolute -bottom-20 -right-20 w-64 h-64 rounded-full opacity-30 blur-3xl pointer-events-none"
          style={{ backgroundColor: PURPLE }}
        />
      </motion.div>

      {/* Dev: Quick Fill Button */}
      <button
        onClick={fillWithTestData}
        className="fixed bottom-4 right-4 px-3 py-1.5 text-xs bg-gray-100 text-gray-500 rounded-lg opacity-50 hover:opacity-100 transition-opacity"
      >
        Fill & Test
      </button>
    </div>
  );
}

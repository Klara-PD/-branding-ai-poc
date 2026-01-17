"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useBranding } from "@/context/BrandingContext";
import type { DiscoveryFormData } from "@/types";
import { DEFAULT_SYSTEM_INSTRUCTIONS } from "@/lib/constants";
import { Loader2, Sparkles, ArrowRight, Check } from "lucide-react";

// Industry options with emojis
const INDUSTRIES = [
  { value: "tech", label: "Tech", emoji: "💻" },
  { value: "fashion", label: "Fashion", emoji: "👗" },
  { value: "food", label: "Food & Beverage", emoji: "🍕" },
  { value: "health", label: "Health & Wellness", emoji: "🧘" },
  { value: "finance", label: "Finance", emoji: "💰" },
  { value: "education", label: "Education", emoji: "📚" },
  { value: "entertainment", label: "Entertainment", emoji: "🎬" },
  { value: "travel", label: "Travel", emoji: "✈️" },
  { value: "retail", label: "Retail", emoji: "🛍️" },
  { value: "services", label: "Services", emoji: "🤝" },
  { value: "creative", label: "Creative & Design", emoji: "🎨" },
  { value: "other", label: "Other", emoji: "✨" },
];

// Generate niche suggestions based on industry
function generateNicheSuggestions(industry: string): { value: string; label: string; emoji: string }[] {
  const niches: Record<string, { value: string; label: string; emoji: string }[]> = {
    tech: [
      { value: "saas", label: "SaaS Platform", emoji: "☁️" },
      { value: "ai", label: "AI & Machine Learning", emoji: "🤖" },
      { value: "mobile", label: "Mobile Apps", emoji: "📱" },
      { value: "cybersecurity", label: "Cybersecurity", emoji: "🔒" },
      { value: "devtools", label: "Developer Tools", emoji: "⚙️" },
    ],
    fashion: [
      { value: "streetwear", label: "Streetwear", emoji: "🧢" },
      { value: "luxury", label: "Luxury Fashion", emoji: "👑" },
      { value: "sustainable", label: "Sustainable Fashion", emoji: "🌿" },
      { value: "activewear", label: "Activewear", emoji: "🏃" },
      { value: "accessories", label: "Accessories", emoji: "💍" },
    ],
    food: [
      { value: "bakery", label: "Bakery", emoji: "🥐" },
      { value: "streetfood", label: "Street Food", emoji: "🌮" },
      { value: "finedining", label: "Fine Dining", emoji: "🍽️" },
      { value: "cafe", label: "Coffee & Café", emoji: "☕" },
      { value: "healthy", label: "Healthy & Organic", emoji: "🥗" },
    ],
    health: [
      { value: "fitness", label: "Fitness & Gym", emoji: "💪" },
      { value: "mental", label: "Mental Wellness", emoji: "🧠" },
      { value: "nutrition", label: "Nutrition", emoji: "🥑" },
      { value: "spa", label: "Spa & Beauty", emoji: "💆" },
      { value: "medical", label: "Medical & Healthcare", emoji: "🏥" },
    ],
    finance: [
      { value: "fintech", label: "Fintech", emoji: "📊" },
      { value: "crypto", label: "Crypto & Web3", emoji: "🪙" },
      { value: "investment", label: "Investment", emoji: "📈" },
      { value: "insurance", label: "Insurance", emoji: "🛡️" },
      { value: "banking", label: "Banking", emoji: "🏦" },
    ],
    education: [
      { value: "edtech", label: "EdTech", emoji: "💡" },
      { value: "language", label: "Language Learning", emoji: "🗣️" },
      { value: "kids", label: "Kids Education", emoji: "🎒" },
      { value: "professional", label: "Professional Training", emoji: "🎓" },
      { value: "arts", label: "Arts & Music", emoji: "🎵" },
    ],
    entertainment: [
      { value: "gaming", label: "Gaming", emoji: "🎮" },
      { value: "streaming", label: "Streaming", emoji: "📺" },
      { value: "events", label: "Events & Concerts", emoji: "🎤" },
      { value: "sports", label: "Sports", emoji: "⚽" },
      { value: "media", label: "Media & Content", emoji: "🎥" },
    ],
    travel: [
      { value: "adventure", label: "Adventure Travel", emoji: "🏔️" },
      { value: "luxury-travel", label: "Luxury Travel", emoji: "🏝️" },
      { value: "eco", label: "Eco Tourism", emoji: "🌳" },
      { value: "business", label: "Business Travel", emoji: "💼" },
      { value: "local", label: "Local Experiences", emoji: "🗺️" },
    ],
    retail: [
      { value: "ecommerce", label: "E-commerce", emoji: "🛒" },
      { value: "boutique", label: "Boutique", emoji: "🏪" },
      { value: "marketplace", label: "Marketplace", emoji: "🏬" },
      { value: "subscription", label: "Subscription Box", emoji: "📦" },
      { value: "vintage", label: "Vintage & Thrift", emoji: "🕰️" },
    ],
    services: [
      { value: "consulting", label: "Consulting", emoji: "💬" },
      { value: "agency", label: "Creative Agency", emoji: "🎯" },
      { value: "legal", label: "Legal Services", emoji: "⚖️" },
      { value: "realestate", label: "Real Estate", emoji: "🏠" },
      { value: "cleaning", label: "Home Services", emoji: "🧹" },
    ],
    creative: [
      { value: "design", label: "Design Studio", emoji: "✏️" },
      { value: "photography", label: "Photography", emoji: "📸" },
      { value: "video", label: "Video Production", emoji: "🎬" },
      { value: "branding", label: "Branding Agency", emoji: "🎨" },
      { value: "illustration", label: "Illustration", emoji: "🖼️" },
    ],
    other: [
      { value: "nonprofit", label: "Non-Profit", emoji: "❤️" },
      { value: "community", label: "Community", emoji: "👥" },
      { value: "personal", label: "Personal Brand", emoji: "⭐" },
      { value: "startup", label: "Startup", emoji: "🚀" },
      { value: "custom", label: "Something Unique", emoji: "🦄" },
    ],
  };
  return niches[industry] || niches.other;
}

// Generate audience suggestions based on brand info
function generateAudienceSuggestions(brandName: string, industry: string, valuePitch: string): { value: string; label: string; emoji: string }[] {
  const baseAudiences = [
    { value: "gen-z", label: "Gen Z Trendsetters", emoji: "🔥" },
    { value: "millennials", label: "Millennials", emoji: "📱" },
    { value: "professionals", label: "Busy Professionals", emoji: "💼" },
    { value: "parents", label: "Modern Parents", emoji: "👨‍👩‍👧" },
    { value: "entrepreneurs", label: "Entrepreneurs", emoji: "🚀" },
    { value: "creatives", label: "Creative Souls", emoji: "🎨" },
    { value: "students", label: "Students", emoji: "🎓" },
    { value: "luxury", label: "Luxury Seekers", emoji: "💎" },
    { value: "eco", label: "Eco-Conscious", emoji: "🌱" },
    { value: "tech-savvy", label: "Tech Enthusiasts", emoji: "⚡" },
  ];
  
  // Shuffle and return top 5
  return baseAudiences.sort(() => Math.random() - 0.5).slice(0, 5);
}

// Editable Chip Component
function EditableChip({ 
  item, 
  isSelected, 
  onSelect, 
  onEdit 
}: { 
  item: { value: string; label: string; emoji: string };
  isSelected: boolean;
  onSelect: () => void;
  onEdit: (newValue: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(item.label);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleClick = () => {
    if (isSelected) {
      setIsEditing(true);
    } else {
      onSelect();
    }
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (editValue.trim() !== item.label) {
      onEdit(editValue.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleBlur();
    }
    if (e.key === 'Escape') {
      setEditValue(item.label);
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <motion.div
        layoutId={item.value}
        className="inline-flex"
      >
        <Input
          ref={inputRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          className="h-10 px-4 text-base font-medium min-w-[120px] rounded-full border-2 border-primary"
        />
      </motion.div>
    );
  }

  return (
    <motion.button
      layoutId={item.value}
      type="button"
      onClick={handleClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`
        inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-base font-medium
        transition-all duration-200 border-2
        ${isSelected 
          ? 'bg-primary text-primary-foreground border-primary shadow-lg' 
          : 'bg-card hover:bg-secondary border-border hover:border-primary/50'
        }
      `}
    >
      <span className="text-lg">{item.emoji}</span>
      <span>{item.label}</span>
      {isSelected && <Check className="w-4 h-4 ml-1" />}
    </motion.button>
  );
}

// Progress phases
const PHASES = [
  { name: "Identity", steps: [0, 1] },
  { name: "Niche", steps: [2, 3] },
  { name: "Audience", steps: [4, 5] },
  { name: "Magic", steps: [6] },
];

export function Step1Discovery() {
  const { setFormData, setCurrentStep, setCreativeBrief } = useBranding();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [direction, setDirection] = useState(1);
  
  // Form data state
  const [data, setData] = useState({
    userName: '',
    brandName: '',
    industry: '',
    niche: '',
    valuePitch: '',
    audience: '',
    specialDirectives: '',
  });

  // Custom edited values for chips
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
      case 6: return true; // Optional step
      default: return false;
    }
  };

  const goNext = () => {
    if (currentStepIndex < 6) {
      setDirection(1);
      setCurrentStepIndex(prev => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const goBack = () => {
    if (currentStepIndex > 0) {
      setDirection(-1);
      setCurrentStepIndex(prev => prev - 1);
    }
  };

  // Quick fill for testing - fills all fields with RANDOM test data
  const fillWithTestData = () => {
    const testBusinesses = [
      {
        userName: 'Klara',
        brandName: 'Bloom Studio',
        industry: 'creative',
        niche: 'Branding Agency',
        valuePitch: 'We transform startups into memorable brands through strategic design and storytelling.',
        audience: 'Tech Startups',
        specialDirectives: 'Modern, minimal aesthetic. Soft gradients and clean typography. No dark themes.',
      },
      {
        userName: 'Maya',
        brandName: 'Verde Kitchen',
        industry: 'food',
        niche: 'Plant-Based Restaurant',
        valuePitch: 'Farm-to-table vegan cuisine that proves healthy eating can be indulgent and delicious.',
        audience: 'Health-conscious foodies',
        specialDirectives: 'Earthy greens, warm wood tones. Organic, natural feel. Hand-drawn illustrations welcome.',
      },
      {
        userName: 'Alex',
        brandName: 'NightOwl',
        industry: 'tech',
        niche: 'Productivity App',
        valuePitch: 'AI-powered focus assistant that helps night owls work smarter, not harder.',
        audience: 'Remote workers and freelancers',
        specialDirectives: 'Dark mode is a MUST. Neon accents. Futuristic but friendly.',
      },
      {
        userName: 'Sophia',
        brandName: 'Lumière',
        industry: 'beauty',
        niche: 'Luxury Skincare',
        valuePitch: 'French-inspired skincare rituals with cutting-edge biotechnology for timeless radiance.',
        audience: 'Affluent women 35-55',
        specialDirectives: 'Elegant, luxurious. Gold accents. Serif typography. Very feminine.',
      },
      {
        userName: 'Jordan',
        brandName: 'Bolt Athletics',
        industry: 'fitness',
        niche: 'CrossFit Gym',
        valuePitch: 'Community-driven high-intensity training that pushes limits and builds champions.',
        audience: 'Competitive athletes 25-40',
        specialDirectives: 'Bold, aggressive. Electric colors. Strong geometric shapes. High energy.',
      },
      {
        userName: 'Emma',
        brandName: 'Tiny Explorers',
        industry: 'education',
        niche: 'Kids Learning Platform',
        valuePitch: 'Playful STEM adventures that turn curious kids into confident problem-solvers.',
        audience: 'Parents of children 4-10',
        specialDirectives: 'Bright, playful colors. Rounded shapes. Fun illustrations. Child-friendly.',
      },
      {
        userName: 'Daniel',
        brandName: 'Nomad Coffee Co.',
        industry: 'food',
        niche: 'Specialty Coffee Roasters',
        valuePitch: 'Single-origin beans sourced from remote farms, roasted to perfection for the adventurous palate.',
        audience: 'Coffee enthusiasts and travelers',
        specialDirectives: 'Vintage travel aesthetic. Muted earth tones. Hand-crafted feel. Maps and stamps.',
      },
      {
        userName: 'Lisa',
        brandName: 'ZenSpace',
        industry: 'wellness',
        niche: 'Meditation Studio',
        valuePitch: 'Urban sanctuary offering ancient mindfulness practices for modern stress relief.',
        audience: 'Stressed professionals seeking balance',
        specialDirectives: 'Calm, serene. Soft pastels. Minimalist. Japanese-inspired aesthetic.',
      },
      {
        userName: 'Marcus',
        brandName: 'BlockVault',
        industry: 'finance',
        niche: 'Crypto Investment Platform',
        valuePitch: 'Institutional-grade security meets user-friendly interface for smart crypto investing.',
        audience: 'Tech-savvy investors',
        specialDirectives: 'Trust and security. Deep blues and silvers. Clean, professional. Subtle tech patterns.',
      },
      {
        userName: 'Nina',
        brandName: 'Paw Palace',
        industry: 'pets',
        niche: 'Luxury Pet Hotel',
        valuePitch: 'Five-star accommodations where your furry family members are treated like royalty.',
        audience: 'Affluent pet owners',
        specialDirectives: 'Playful but upscale. Warm colors. Crown motifs. Friendly luxury.',
      },
    ];
    
    // Pick a random business
    const randomIndex = Math.floor(Math.random() * testBusinesses.length);
    const testData = testBusinesses[randomIndex];
    
    setData(testData);
    setCustomNiche(testData.niche);
    setCustomAudience(testData.audience);
    setCurrentStepIndex(6); // Jump to last step
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    
    const finalNiche = customNiche || data.niche;
    const finalAudience = customAudience || data.audience;
    
    // Build comprehensive brand brief
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
      console.log('🌐 [FRONTEND] Calling POST /api/generate-creative-brief');
      const response = await fetch('/api/generate-creative-brief', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ formData }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let error;
        try {
          error = JSON.parse(errorText);
        } catch {
          error = { error: errorText || `HTTP ${response.status}` };
        }
        throw new Error(error.error || error.message || 'Failed to generate creative brief');
      }

      const creativeBrief = await response.json();
      console.log('✅ [FRONTEND] Creative Brief received:', creativeBrief);
      setCreativeBrief(creativeBrief);
      setIsLoading(false);
      setCurrentStep(2);
    } catch (error: any) {
      console.error('❌ [FRONTEND] Failed to generate creative brief:', error);
      alert(`Error: ${error.message}\n\nPlease add your API key in Settings.`);
      setIsLoading(false);
    }
  };

  // Get current phase for progress bar
  const getCurrentPhase = () => {
    for (let i = 0; i < PHASES.length; i++) {
      if (PHASES[i].steps.includes(currentStepIndex)) {
        return i;
      }
    }
    return 0;
  };

  // Animation variants
  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction > 0 ? -300 : 300,
      opacity: 0,
    }),
  };

  const renderStepContent = () => {
    switch (currentStepIndex) {
      case 0:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                Hey there! 👋
              </h2>
              <p className="text-xl text-muted-foreground">
                I'm <span className="text-primary font-semibold">Flow</span>, your AI design partner. First things first—what's your name?
              </p>
            </div>
            <Input
              value={data.userName}
              onChange={(e) => updateData('userName', e.target.value)}
              placeholder="Enter your name..."
              className="h-14 text-lg px-5 rounded-2xl"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && canProceed() && goNext()}
            />
          </div>
        );
      
      case 1:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                Nice to meet you, {data.userName}! ✨
              </h2>
              <p className="text-xl text-muted-foreground">
                Ready to build something iconic? What's the name of your business or venture?
              </p>
            </div>
            <Input
              value={data.brandName}
              onChange={(e) => updateData('brandName', e.target.value)}
              placeholder="Enter your brand name..."
              className="h-14 text-lg px-5 rounded-2xl"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && canProceed() && goNext()}
            />
          </div>
        );
      
      case 2:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                {data.brandName}... I love that! 🚀
              </h2>
              <p className="text-xl text-muted-foreground">
                Now, {data.userName}, in which world does <span className="text-primary font-semibold">{data.brandName}</span> live?
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              {INDUSTRIES.map((industry) => (
                <EditableChip
                  key={industry.value}
                  item={industry}
                  isSelected={data.industry === industry.value}
                  onSelect={() => updateData('industry', industry.value)}
                  onEdit={(newValue) => updateData('industry', newValue)}
                />
              ))}
            </div>
          </div>
        );
      
      case 3:
        const nicheSuggestions = generateNicheSuggestions(data.industry);
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                Got it! 🎯
              </h2>
              <p className="text-xl text-muted-foreground">
                Inside the <span className="text-primary font-semibold">{INDUSTRIES.find(i => i.value === data.industry)?.label || data.industry}</span> world, what is <span className="text-primary font-semibold">{data.brandName}</span>'s specific superpower?
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              {nicheSuggestions.map((niche) => (
                <EditableChip
                  key={niche.value}
                  item={niche}
                  isSelected={data.niche === niche.value}
                  onSelect={() => {
                    updateData('niche', niche.value);
                    setCustomNiche(niche.label);
                  }}
                  onEdit={(newValue) => {
                    setCustomNiche(newValue);
                  }}
                />
              ))}
            </div>
            <div className="pt-2">
              <p className="text-sm text-muted-foreground mb-2">Or type your own:</p>
              <Input
                value={customNiche}
                onChange={(e) => {
                  setCustomNiche(e.target.value);
                  updateData('niche', 'custom');
                }}
                placeholder="Something else..."
                className="h-12 text-base px-4 rounded-xl"
              />
            </div>
          </div>
        );
      
      case 4:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                Ooh, fancy! ✨
              </h2>
              <p className="text-xl text-muted-foreground">
                If someone asked you in an elevator, what's the #1 reason they'll fall in love with <span className="text-primary font-semibold">{data.brandName}</span>?
              </p>
            </div>
            <Textarea
              value={data.valuePitch}
              onChange={(e) => updateData('valuePitch', e.target.value)}
              placeholder="What makes your brand special..."
              className="min-h-[120px] text-lg px-5 py-4 rounded-2xl resize-none"
              autoFocus
            />
          </div>
        );
      
      case 5:
        const audienceSuggestions = generateAudienceSuggestions(data.brandName, data.industry, data.valuePitch);
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                Powerful! 💪
              </h2>
              <p className="text-xl text-muted-foreground">
                So, {data.userName}, who is <span className="text-primary font-semibold">{data.brandName}</span>'s absolute biggest fan?
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              {audienceSuggestions.map((audience) => (
                <EditableChip
                  key={audience.value}
                  item={audience}
                  isSelected={data.audience === audience.value}
                  onSelect={() => {
                    updateData('audience', audience.value);
                    setCustomAudience(audience.label);
                  }}
                  onEdit={(newValue) => {
                    setCustomAudience(newValue);
                  }}
                />
              ))}
            </div>
            <div className="pt-2">
              <p className="text-sm text-muted-foreground mb-2">Or describe your ideal customer:</p>
              <Input
                value={customAudience}
                onChange={(e) => {
                  setCustomAudience(e.target.value);
                  updateData('audience', 'custom');
                }}
                placeholder="Your target audience..."
                className="h-12 text-base px-4 rounded-xl"
              />
            </div>
          </div>
        );
      
      case 6:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-foreground">
                Final touch, {data.userName}! 🎨
              </h2>
              <p className="text-xl text-muted-foreground">
                Is there anything else you want me to know? Any 'must-haves' for <span className="text-primary font-semibold">{data.brandName}</span>?
              </p>
            </div>
            <Textarea
              value={data.specialDirectives}
              onChange={(e) => updateData('specialDirectives', e.target.value)}
              placeholder="e.g., 'I'm obsessed with cobalt blue' or 'No serif fonts' or 'Modern and minimal'..."
              className="min-h-[120px] text-lg px-5 py-4 rounded-2xl resize-none"
              autoFocus
            />
            <p className="text-sm text-muted-foreground">
              💡 This is optional but helps me create something truly unique for you!
            </p>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 py-4">
      {/* Progress Bar */}
      <div className="space-y-3">
        <div className="flex justify-between">
          {PHASES.map((phase, idx) => (
            <div 
              key={phase.name}
              className={`text-sm font-medium transition-colors ${
                idx <= getCurrentPhase() ? 'text-primary' : 'text-muted-foreground'
              }`}
            >
              {phase.name}
            </div>
          ))}
        </div>
        <div className="h-2 bg-secondary rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-primary/80"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStepIndex + 1) / 7) * 100}%` }}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
          />
        </div>
      </div>

      {/* Step Content Card */}
      <div className="relative min-h-[400px]">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentStepIndex}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="bg-card rounded-3xl p-8 shadow-xl border border-border"
          >
            {renderStepContent()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="ghost"
          onClick={goBack}
          disabled={currentStepIndex === 0}
          className="text-muted-foreground"
        >
          ← Back
        </Button>
        
        <AnimatePresence mode="wait">
          {canProceed() && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <Button
                type="button"
                onClick={goNext}
                disabled={isLoading}
                className="h-12 px-8 text-lg rounded-2xl gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating magic...
                  </>
                ) : currentStepIndex === 6 ? (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate Brand
                  </>
                ) : (
                  <>
                    Continue
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Dev: Quick Fill Button */}
      <div className="fixed bottom-4 right-4">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={fillWithTestData}
          className="text-xs opacity-50 hover:opacity-100 transition-opacity"
        >
          ⚡ Fill & Test
        </Button>
      </div>
    </div>
  );
}

"use client";

import { motion } from "framer-motion";
import Image from "next/image";

interface LandingPageProps {
  onStart: () => void;
}

// Brand color
const PURPLE = "#7B6BDB";

export function LandingPage({ onStart }: LandingPageProps) {
  return (
    <div 
      className="min-h-screen overflow-hidden relative"
      style={{
        background: `linear-gradient(135deg, #ffffff 0%, #f8f7ff 50%, #f0eeff 100%)`
      }}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-6 relative z-10">
        <div className="flex items-center gap-2">
          <Image
            src="/flowlogo.svg"
            alt="Flow"
            width={60}
            height={24}
            className="h-6 w-auto"
          />
        </div>
        
        <button 
          className="px-4 py-2 text-white text-xs font-medium rounded-md transition-colors hover:opacity-90"
          style={{ backgroundColor: PURPLE }}
        >
          Send Feedback
        </button>
      </header>

      {/* Hero Section */}
      <main className="relative z-10">
        <div className="max-w-7xl mx-auto px-8 pt-16 pb-8">
          <div className="flex flex-col items-center text-center max-w-2xl mx-auto">
            {/* Badge */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 border border-gray-200 rounded-full mb-8"
            >
              <span 
                className="px-2 py-0.5 text-white text-xs font-semibold rounded"
                style={{ backgroundColor: PURPLE }}
              >
                NEW
              </span>
              <span className="text-sm text-gray-600">Vibe designing with AI</span>
              <span className="text-gray-400">→</span>
            </motion.div>

            {/* Headline */}
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight mb-6"
              style={{ fontFamily: "'Labil Grotesk', sans-serif" }}
            >
              Stop blending in.
              <br />
              Start standing out.
            </motion.h1>

            {/* Subheadline */}
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg text-gray-500 mb-8 max-w-md"
            >
              Create your unique identity with AI that
              <br />
              understands design.
            </motion.p>

            {/* CTA Button */}
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onStart}
              className="px-8 py-3.5 text-white font-medium rounded-lg transition-colors hover:opacity-90"
              style={{ 
                backgroundColor: PURPLE,
                boxShadow: `0 10px 25px -5px ${PURPLE}40`
              }}
            >
              Define Your Vibe
            </motion.button>
          </div>
        </div>
      </main>

      {/* Illustration - Bottom Right */}
      <div className="absolute bottom-0 right-0 w-[350px] h-[420px] pointer-events-none hidden lg:block">
        <Image
          src="/illustration-hero.png"
          alt="Designer working on laptop"
          fill
          className="object-contain object-bottom-right"
          style={{ objectPosition: 'right bottom' }}
          priority
        />
      </div>

      {/* Mobile Illustration */}
      <div className="lg:hidden flex justify-center mt-8">
        <div className="relative w-[210px] h-[280px]">
          <Image
            src="/illustration-hero.png"
            alt="Designer working on laptop"
            fill
            className="object-contain"
            priority
          />
        </div>
      </div>
    </div>
  );
}

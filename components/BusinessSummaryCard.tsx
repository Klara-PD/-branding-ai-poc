"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useBranding } from "@/context/BrandingContext";
import { Pencil, Check, X, Building2, Users, Sparkles, Target } from "lucide-react";

interface ParsedBrief {
  brandName: string;
  industry: string;
  niche: string;
  valuePitch: string;
  audience: string;
  specialDirectives: string;
}

function parseBriefFromStyleDescription(styleDescription: string): ParsedBrief {
  const lines = styleDescription.split('\n');
  const parsed: ParsedBrief = {
    brandName: '',
    industry: '',
    niche: '',
    valuePitch: '',
    audience: '',
    specialDirectives: '',
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('Brand:')) {
      parsed.brandName = trimmed.replace('Brand:', '').trim();
    } else if (trimmed.startsWith('Industry:')) {
      parsed.industry = trimmed.replace('Industry:', '').trim();
    } else if (trimmed.startsWith('Niche:')) {
      parsed.niche = trimmed.replace('Niche:', '').trim();
    } else if (trimmed.startsWith('Value Proposition:')) {
      parsed.valuePitch = trimmed.replace('Value Proposition:', '').trim();
    } else if (trimmed.startsWith('Target Audience:')) {
      parsed.audience = trimmed.replace('Target Audience:', '').trim();
    } else if (trimmed.startsWith('Special Directives:')) {
      parsed.specialDirectives = trimmed.replace('Special Directives:', '').trim();
    }
  }

  return parsed;
}

function buildStyleDescription(parsed: ParsedBrief): string {
  return `Brand: ${parsed.brandName}
Industry: ${parsed.industry}
Niche: ${parsed.niche}
Value Proposition: ${parsed.valuePitch}
Target Audience: ${parsed.audience}
Special Directives: ${parsed.specialDirectives || 'None specified'}`.trim();
}

export function BusinessSummaryCard() {
  const { formData, setFormData } = useBranding();
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<ParsedBrief | null>(null);

  if (!formData) return null;

  const parsed = parseBriefFromStyleDescription(formData.styleDescription || '');

  const handleEdit = () => {
    setEditData(parsed);
    setIsEditing(true);
  };

  const handleSave = () => {
    if (editData && formData) {
      const newStyleDescription = buildStyleDescription(editData);
      setFormData({
        ...formData,
        businessName: editData.brandName,
        targetAudience: editData.audience,
        styleDescription: newStyleDescription,
      });
    }
    setIsEditing(false);
    setEditData(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditData(null);
  };

  const updateEditData = (field: keyof ParsedBrief, value: string) => {
    if (editData) {
      setEditData({ ...editData, [field]: value });
    }
  };

  return (
    <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="w-5 h-5 text-primary" />
            Business Summary
          </CardTitle>
          {!isEditing ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEdit}
              className="h-8 gap-1 text-muted-foreground hover:text-foreground"
            >
              <Pencil className="w-3.5 h-3.5" />
              Edit
            </Button>
          ) : (
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                className="h-8 w-8 p-0 text-muted-foreground"
              >
                <X className="w-4 h-4" />
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleSave}
                className="h-8 gap-1"
              >
                <Check className="w-3.5 h-3.5" />
                Save
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <AnimatePresence mode="wait">
          {!isEditing ? (
            <motion.div
              key="view"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              {/* Brand Name & Industry */}
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <p className="text-2xl font-bold text-foreground">
                    {parsed.brandName || formData.businessName || 'Unnamed Brand'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {parsed.industry} {parsed.niche && `• ${parsed.niche}`}
                  </p>
                </div>
              </div>

              {/* Value Proposition */}
              {parsed.valuePitch && (
                <div className="flex items-start gap-2 pt-2">
                  <Sparkles className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <p className="text-sm text-foreground/80 leading-relaxed">
                    {parsed.valuePitch}
                  </p>
                </div>
              )}

              {/* Target Audience */}
              {parsed.audience && (
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary shrink-0" />
                  <p className="text-sm">
                    <span className="text-muted-foreground">Target:</span>{' '}
                    <span className="font-medium">{parsed.audience}</span>
                  </p>
                </div>
              )}

              {/* Special Directives */}
              {parsed.specialDirectives && parsed.specialDirectives !== 'None specified' && (
                <div className="flex items-start gap-2 pt-1">
                  <Target className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <p className="text-sm text-muted-foreground italic">
                    "{parsed.specialDirectives}"
                  </p>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="edit"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Brand Name</Label>
                  <Input
                    value={editData?.brandName || ''}
                    onChange={(e) => updateEditData('brandName', e.target.value)}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Industry</Label>
                  <Input
                    value={editData?.industry || ''}
                    onChange={(e) => updateEditData('industry', e.target.value)}
                    className="h-9"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Niche</Label>
                  <Input
                    value={editData?.niche || ''}
                    onChange={(e) => updateEditData('niche', e.target.value)}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Target Audience</Label>
                  <Input
                    value={editData?.audience || ''}
                    onChange={(e) => updateEditData('audience', e.target.value)}
                    className="h-9"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Value Proposition</Label>
                <Textarea
                  value={editData?.valuePitch || ''}
                  onChange={(e) => updateEditData('valuePitch', e.target.value)}
                  rows={2}
                  className="resize-none text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Special Directives</Label>
                <Input
                  value={editData?.specialDirectives || ''}
                  onChange={(e) => updateEditData('specialDirectives', e.target.value)}
                  className="h-9"
                  placeholder="e.g., Modern minimal, no dark themes..."
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}

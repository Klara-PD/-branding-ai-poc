"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Settings, Info } from "lucide-react";

export function SettingsModal() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            API keys are configured on the server. Contact the administrator to update them.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="flex items-start gap-3 p-4 bg-muted rounded-lg">
            <Info className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium">API Keys</p>
              <p className="text-xs text-muted-foreground">
                All API keys are stored securely on the server in the <code className="px-1 py-0.5 bg-background rounded text-xs">.env.local</code> file.
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Configured keys:
              </p>
              <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1 mt-1">
                <li>OpenRouter (for GPT-4o and Claude 3.5 Sonnet)</li>
                <li>Pinecone (for vector search)</li>
                <li>Replicate (optional, for image generation)</li>
              </ul>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

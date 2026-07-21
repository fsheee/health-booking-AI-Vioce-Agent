"use client";

import { Toaster as SonnerToaster } from "sonner";

function Toaster() {
  return (
    <SonnerToaster
      position="top-right"
      toastOptions={{
        classNames: {
          toast: "border border-border bg-background text-foreground shadow-lg",
          description: "text-muted-foreground",
        },
      }}
    />
  );
}

export { Toaster };

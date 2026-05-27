"use client";

import { ThemeProvider } from "next-themes";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

export default function ThemeProviderWrapper({ children }: Props) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      {children}
    </ThemeProvider>
  );
}

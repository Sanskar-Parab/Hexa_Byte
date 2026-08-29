import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },

        // Next Path AI design tokens (see DESIGN.md)
        ink: "#171717",
        body: "#4d4d4d",
        mute: "#888888",
        hairline: {
          DEFAULT: "#ebebeb",
          strong: "#a1a1a1",
        },
        canvas: {
          DEFAULT: "#ffffff",
          soft: "#fafafa",
          soft2: "#f5f5f5",
        },
        link: {
          DEFAULT: "#0070f3",
          deep: "#0761d1",
          soft: "#d3e5ff",
        },
        success: "#0070f3",
        warn: {
          DEFAULT: "#f5a623",
          soft: "#ffefcf",
          deep: "#ab570a",
        },
        err: {
          DEFAULT: "#ee0000",
          soft: "#f7d4d6",
          deep: "#c50000",
        },
        violet: {
          DEFAULT: "#7928ca",
          soft: "#d8ccf1",
          deep: "#4c2889",
        },
        cyan: {
          DEFAULT: "#50e3c2",
          soft: "#aaffec",
          deep: "#29bc9b",
        },
        pink: {
          DEFAULT: "#ff0080",
        },
        gradient: {
          "develop-start": "#007cf0",
          "develop-end": "#00dfd8",
          "preview-start": "#7928ca",
          "preview-end": "#ff0080",
          "ship-start": "#ff4d4d",
          "ship-end": "#f9cb28",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "16px",
        "pill-sm": "64px",
        pill: "100px",
      },
      boxShadow: {
        card: "0px 1px 1px rgba(0,0,0,0.02), 0px 2px 2px rgba(0,0,0,0.04), inset 0 0 0 1px rgba(0,0,0,0.05)",
        "card-hover": "0px 2px 2px rgba(0,0,0,0.04), 0px 8px 8px -8px rgba(0,0,0,0.04), inset 0 0 0 1px rgba(0,0,0,0.05)",
        panel: "0px 2px 2px rgba(0,0,0,0.04), 0px 8px 16px -4px rgba(0,0,0,0.04), inset 0 0 0 1px rgba(0,0,0,0.05)",
        modal: "0px 1px 1px rgba(0,0,0,0.02), 0px 8px 16px -4px rgba(0,0,0,0.04), 0px 24px 32px -8px rgba(0,0,0,0.06), inset 0 0 0 1px rgba(0,0,0,0.05)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "grow-x": {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.5s ease-out forwards",
        "slide-in": "slide-in 0.3s ease-out forwards",
        "scale-in": "scale-in 0.2s ease-out forwards",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "grow-x": "grow-x 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
      },
    },
  },
  plugins: [],
};

export default config;

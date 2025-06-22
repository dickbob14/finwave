/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // FinWave Brand Colors
        primary: {
          DEFAULT: "#1E2A38", // Deep Navy
          foreground: "#FFFFFF",
          50: "#E8EBF0",
          100: "#D1D7E0",
          200: "#A3AFC1",
          300: "#7587A3",
          400: "#475F84",
          500: "#1E2A38", // Deep Navy
          600: "#182330",
          700: "#121B28",
          800: "#0C1420",
          900: "#060C18",
        },
        secondary: {
          DEFAULT: "#2DB3A6", // Ocean Teal
          foreground: "#FFFFFF",
          50: "#E6F6F5",
          100: "#CDEDEB",
          200: "#9BDBD7",
          300: "#69C9C3",
          400: "#37B7AF",
          500: "#2DB3A6",
          600: "#258F85",
          700: "#1D6B64",
          800: "#154743",
          900: "#0D2421",
        },
        accent: {
          DEFAULT: "#5B5BF2", // Electric Indigo
          foreground: "#FFFFFF",
          50: "#ECECFE",
          100: "#D9D9FC",
          200: "#B3B3FA",
          300: "#8D8DF7",
          400: "#6767F5",
          500: "#5B5BF2",
          600: "#2E2EE9",
          700: "#2323BD",
          800: "#181890",
          900: "#0D0D64",
        },
        success: "#10B981", // Emerald Tint
        warning: "#F59E0B",
        error: "#F87171", // Coral Red
        info: "#5B5BF2",
        // Neutral colors
        navy: "#1E2A38",
        teal: "#2DB3A6",
        indigo: "#5B5BF2",
        emerald: "#10B981",
        coral: "#F87171",
        cloud: "#F9FAFB",
        mist: "#E5E7EB",
        destructive: {
          DEFAULT: "#F87171",
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#E5E7EB",
          foreground: "#6B7280",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Satoshi', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Space Grotesk', 'Roboto Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #2DB3A6 0%, #5B5BF2 100%)',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
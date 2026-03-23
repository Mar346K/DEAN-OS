/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface-container-low": "#1b1b1d",
        "surface": "#131315",
        "outline-variant": "#3a494b",
        "surface-tint": "#00dce6",
        "secondary": "#ffabf3",
        "on-primary-container": "#006b71",
        "surface-container-high": "#2a2a2c",
        "on-primary": "#00373a",
        "error": "#ffb4ab",
        "on-surface": "#e5e1e4",
        "primary": "#e3fdff",
        "surface-container-highest": "#353437",
        "surface-container": "#201f21",
        "outline": "#849495",
        "surface-container-lowest": "#0e0e10",
        "on-surface-variant": "#b9cacb",
        "surface-variant": "#353437",
        "primary-container": "#00f3ff",
        "background": "#131315",
        "secondary-container": "#fe00fe",
        "on-background": "#e5e1e4"
      },
      fontFamily: {
        "headline": ["Space Grotesk", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "label": ["Space Grotesk", "sans-serif"]
      },
      borderRadius: {"DEFAULT": "0px", "lg": "0px", "xl": "0px", "full": "9999px"},
    },
  },
  plugins: [],
}

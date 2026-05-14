/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary:   { DEFAULT: "#0d7a5f", dark: "#064e3b", glow: "#10a07d" },
        accent:    "#c9a84c",
        cream:     "#f5f0e0",
        ink:       "#0a1f17",
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "serif"],
        sans:    ['"Inter"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        elegant: "0 10px 30px -12px rgba(13,122,95,0.35)",
      },
    },
  },
  plugins: [],
};

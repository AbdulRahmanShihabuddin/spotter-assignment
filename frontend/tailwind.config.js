/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0B0D10',
          surface: '#12151B',
          panel: '#171B22',
          elevated: '#1F242E',
          border: '#272F3C',
          borderLight: '#353F50',
        },
        amber: {
          accent: '#F59E0B',
          hover: '#D97706',
          muted: 'rgba(245, 158, 11, 0.15)',
          border: 'rgba(245, 158, 11, 0.35)',
        },
        route: {
          primary: '#F59E0B',
          alt1: '#38BDF8',
          alt2: '#A78BFA',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"IBM Plex Mono"', '"JetBrains Mono"', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}

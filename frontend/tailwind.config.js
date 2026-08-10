/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          'sans-serif'
        ],
        mono: ['"SF Mono"', 'SFMono-Regular', 'ui-monospace', 'Menlo', 'Monaco', 'Consolas', 'monospace']
      },
      colors: {
        apple: {
          bg: '#FFFFFF',
          secondaryBg: '#F5F5F7',
          tertiaryBg: '#FAFAFA',
          border: '#E5E5E7',
          darkBorder: '#D2D2D7',
          text: '#1D1D1F',
          subtext: '#86868B',
          blue: '#0071E3',
          blueHover: '#0077ED',
          green: '#34C759',
          red: '#FF3B30',
          orange: '#FF9500',
          purple: '#AF52DE'
        }
      },
      boxShadow: {
        'apple-sm': '0 2px 8px rgba(0, 0, 0, 0.04)',
        'apple-md': '0 4px 16px rgba(0, 0, 0, 0.08)',
        'apple-lg': '0 12px 32px rgba(0, 0, 0, 0.12)',
      }
    },
  },
  plugins: [],
}
